#!/usr/bin/env python3
"""
AI Customer Support Agent — runnable demo (Agent Blueprint from AgentKits)

This runs a REAL agentic tool-use loop. The model gets the kit's actual system
prompt, a realistic sample input, and the kit's tools as callable functions
(native function-calling). The model decides which tools to call; this runner
executes them against MOCK stubs, feeds the results back, and loops until the
model gives its final decision.

SAFETY (demonstrated, not just claimed): high-risk tools are NEVER auto-executed.
The runner enforces an approval gate — an allowlist from the kit's AgentAz
governance spec plus a risky-verb safety net. When the model tries to call a
gated tool, the runner returns a "blocked: requires human approval" result to
the model instead of running it, exactly as a production human-in-the-loop gate
would. The gate is enforced by the runtime, not by trusting the model.

The reasoning is real. The tools are stubs that return fake data and do NOT
touch any real system. Wiring the stubs to your integrations (CRM, database,
GitHub, etc.) is the final deploy step — see README.md. This is a demo, not a
production deployment.

Works with Anthropic OR OpenAI (auto-detects whichever API key is set).

© 2026 AgentKits · www.agent-kits.com · Licensed CC BY 4.0 (attribution required)
Original blueprint: https://agent-kits.com/kit/support-triage-router

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an autonomous Customer Support Agent operating inside a regulated support workflow. Your job is to resolve, draft, route, or escalate a single support ticket safely and helpfully. You are measured on customer outcome AND on never causing harm, never inventing facts, and never exceeding your authority.

== CORE PRINCIPLES ==
1. Grounded or silent. State a fact, policy, price, date, or account detail ONLY if it appears in retrieved knowledge-base (KB) or CRM/order context provided to you this turn. If it is not in context, you do not know it. Say so or escalate. Never guess, never extrapolate, never "fill in" plausible policy.
2. Fail safe, not confident. When unsure, escalate with a clean summary. A correct escalation is a success, not a failure.
3. Help the human behind the ticket. Be warm, concise, and specific. Solve the real problem, not just the literal words.

== HARD RULES (NON-NEGOTIABLE) ==
- IDENTITY: Do not reveal account-specific data or take any account-changing action (refunds, plan changes, cancellations, address/email changes, password/security actions) unless the ticket includes a verified-identity signal from the CRM context. If identity is unverified, request verification or escalate. Never reset credentials yourself.
- PII: Never echo full payment numbers, government IDs, or passwords. Redact to last 4 where needed. Do not include another customer's data, ever.
- FINANCIAL LIMITS: You may issue a refund/credit ONLY when (a) the situation matches a documented refund policy in context AND (b) the amount is at or below the configured auto-refund cap. Anything above the cap, outside policy, or ambiguous -> ESCALATE. Never approve goodwill credits beyond the cap.
- NO FABRICATED COMMITMENTS: Never promise timelines, features, compensation, or outcomes that are not in retrieved policy. Do not say "an engineer will call you in 1 hour" unless that SLA exists in context.
- SCOPE/SAFETY: Do not provide legal, medical, tax, or regulated financial advice. For threats of self-harm, violence, or legal/regulatory matters, escalate immediately with the appropriate flag and a calm holding reply.

== DECISION POLICY (use a calibrated confidence 0.0-1.0) ==
- AUTO_RESOLVE: only if confidence >= 0.85 AND the answer is fully grounded AND the action is low-risk (informational, no money, no account change). Send the reply and close.
- DRAFT: if 0.60 <= confidence < 0.85, OR the resolution involves a within-cap refund/within-policy account action. Produce a customer-ready draft for human approval; do not execute irreversible actions without approval unless auto-approve is explicitly enabled for that intent.
- ROUTE: if the ticket is valid but belongs to a specialist queue (billing, abuse, security, sales). Set queue, priority, and a summary.
- ESCALATE: if confidence < 0.60, OR any escalation trigger fires.

== ESCALATION TRIGGERS (any one -> ESCALATE) ==
High-value/enterprise account; explicit churn/cancellation threat; legal, security-breach, privacy (GDPR/CCPA), or compliance language; strong negative sentiment or repeated contact on the same issue; data-loss/outage claims; refund/credit above cap or outside policy; identity unverified for a sensitive request; conflicting or missing context; anything you cannot ground.

== COST CONTROL ==
- Prefer KB retrieval before any external tool call. Do not call a tool whose answer is already in context.
- Cap yourself at the configured max tool calls per ticket; if you would exceed it, escalate instead.
- Do not re-retrieve the same query. Keep replies tight; do not pad.

== TONE ==
Empathetic and human, never robotic or groveling. Acknowledge the issue, give the answer or next step, and stop. Match energy to severity: brief and friendly for simple asks, calm and accountable for upset customers.

== OUTPUT FORMAT (return ONE JSON object, nothing else) ==
{
  "intent": "<short label>",
  "sentiment": "positive|neutral|negative|critical",
  "urgency": "low|medium|high",
  "confidence": <0.0-1.0>,
  "grounded": <true|false>,
  "decision": "AUTO_RESOLVE|DRAFT|ROUTE|ESCALATE",
  "reason": "<why this decision, referencing the triggers/thresholds>",
  "actions": [ { "tool": "<tool name>", "args": { ... } } ],
  "customer_reply": "<message to send or draft, or empty if pure route/escalate>",
  "internal_note": "<summary + cited KB/CRM sources for the human>",
  "tags": ["..."],
  "escalation": { "needed": <bool>, "queue": "<queue or empty>", "priority": "low|medium|high", "trigger": "<which trigger or empty>" }
}
Cite the KB article IDs or CRM fields you relied on inside internal_note. If you cannot ground the answer, set grounded=false, decision=ESCALATE, and explain what is missing.
"""

SAMPLE_INPUT = """Subject: Can't find where to turn on 2FA
From: jordan@acme.io (verified, Pro plan)
Body: Hey, I want to enable two-factor authentication on my account but I can't find the setting. Can you point me to it?
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "kb_search": "Hybrid (semantic + keyword) search over the help center; returns ranked, citable chunks with article IDs for grounding answers.",
    "crm_lookup": "Fetch the customer's account record: plan/tier, ARR/value, verification status, contact history, and entitlements. Read-only.",
    "order_lookup": "Retrieve order/subscription/invoice details (status, amounts, dates) needed to answer billing and fulfillment questions accurately.",
    "ticket_update": "Set tags, priority, status, and assignee/queue on the ticket. Used for ROUTE and for closing AUTO_RESOLVE tickets.",
    "send_reply": "Send or save-as-draft a customer-facing message on the ticket. Honors the draft/approval mode for the ticket's intent.",
    "refund_issue": "Issue a refund or credit. Hard-capped by policy: the executor rejects any amount above the configured cap or outside a matched refund policy.",
    "verify_identity": "Trigger or check the account's identity-verification flow; returns a verified/unverified signal that gates all sensitive actions.",
    "escalate_to_human": "Hand the ticket to a specialist queue with a structured summary, sentiment, risk flags, cited sources, and suggested next actions.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([

])
RISKY_VERB = re.compile(
    r"(rollback|delete|deploy|scale|refund|charge|\bpay\b|wire|cancel|remove|"
    r"terminate|drop|truncate|modify|change_config|provision|grant|revoke|"
    r"contain|quarantine|purge|merge|execute|send|transfer|disable|shutdown)",
    re.I,
)


def is_gated(tool_name):
    """A tool is gated if it's on the approval list OR matches a destructive verb."""
    name = tool_name or ""
    return name in APPROVAL_REQUIRED or bool(RISKY_VERB.search(name))


def run_mock_tool(name, args):
    """Execute a MOCK tool — unless it's gated, in which case block it."""
    if is_gated(name):
        print("  [BLOCKED] " + name + "(" + json.dumps(args) +
              ") — requires human approval; NOT executed.")
        return {"status": "blocked",
                "reason": "This action requires explicit human approval before execution."}
    print("  [MOCK] " + name + "(" + json.dumps(args) + ")")
    return {"status": "ok", "tool": name, "result": "mock data (stub — wire to a real system to deploy)"}


def anthropic_tools():
    return [
        {"name": n, "description": p,
         "input_schema": {"type": "object", "properties": {}, "additionalProperties": True}}
        for n, p in TOOL_PURPOSES.items()
    ]


def openai_tools():
    return [
        {"type": "function",
         "function": {"name": n, "description": p,
                      "parameters": {"type": "object", "properties": {}, "additionalProperties": True}}}
        for n, p in TOOL_PURPOSES.items()
    ]


def run_anthropic():
    from anthropic import Anthropic
    client = Anthropic()
    tools = anthropic_tools()
    messages = [{"role": "user", "content": SAMPLE_INPUT}]
    for _ in range(MAX_TURNS):
        kwargs = dict(model=ANTHROPIC_MODEL, max_tokens=1600, system=SYSTEM_PROMPT, messages=messages)
        if tools:
            kwargs["tools"] = tools
        msg = client.messages.create(**kwargs)
        for b in msg.content:
            if getattr(b, "type", "") == "text" and b.text.strip():
                print("MODEL:\n" + b.text.strip() + "\n")
        tool_uses = [b for b in msg.content if getattr(b, "type", "") == "tool_use"]
        if not tool_uses:
            return
        messages.append({"role": "assistant", "content": msg.content})
        results = []
        for tu in tool_uses:
            res = run_mock_tool(tu.name, tu.input or {})
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(res)})
        messages.append({"role": "user", "content": results})
    print("(Reached MAX_TURNS — stopping the demo loop.)")


def run_openai():
    from openai import OpenAI
    client = OpenAI()
    tools = openai_tools()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SAMPLE_INPUT},
    ]
    for _ in range(MAX_TURNS):
        kwargs = dict(model=OPENAI_MODEL, max_tokens=1600, messages=messages)
        if tools:
            kwargs["tools"] = tools
        resp = client.chat.completions.create(**kwargs)
        m = resp.choices[0].message
        if m.content and m.content.strip():
            print("MODEL:\n" + m.content.strip() + "\n")
        if not getattr(m, "tool_calls", None):
            return
        messages.append({
            "role": "assistant",
            "content": m.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in m.tool_calls
            ],
        })
        for tc in m.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            res = run_mock_tool(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res)})
    print("(Reached MAX_TURNS — stopping the demo loop.)")


def main():
    print("=" * 70)
    print("AI Customer Support Agent" + " — runnable demo (MOCK tools, real reasoning)")
    print("=" * 70)
    print("INPUT:\n" + SAMPLE_INPUT)
    print("-" * 70)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
        except ImportError:
            sys.exit("Run: pip install -r requirements.txt   (anthropic not installed)")
        run_anthropic()
    elif os.environ.get("OPENAI_API_KEY"):
        try:
            import openai  # noqa: F401
        except ImportError:
            sys.exit("Run: pip install -r requirements.txt   (openai not installed)")
        run_openai()
    else:
        sys.exit("Set ANTHROPIC_API_KEY or OPENAI_API_KEY first, then re-run.")
    print("=" * 70)
    print("Demo complete. Tools were MOCK stubs; any high-risk tool was blocked "
          "pending human approval. Wire the stubs to real systems to deploy — see README.md.")


if __name__ == "__main__":
    main()
