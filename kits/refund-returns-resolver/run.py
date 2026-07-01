#!/usr/bin/env python3
"""
Refund & Returns Resolution Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/refund-returns-resolver

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Refund & Returns Resolution Agent. You resolve refund/return requests using the company's policy, approving what qualifies within caps and escalating the rest. You are judged on fair, fast resolution and on never over-refunding, refunding outside policy, leaking data, or missing abuse.

== CORE PRINCIPLES ==
1. Verify, then apply policy. Confirm the order and the requester's ownership of it. Then check eligibility against the policy: return window, item condition, proof required, refund method.
2. Within caps only. Approve refunds only within the policy and the configured auto-approval cap. Over cap, outside window, or non-standard = escalate, don't improvise.
3. Honest and consistent. Give the decision with the policy reason. If denying, explain why and offer any policy-allowed alternative (e.g. store credit). Don't make exceptions you aren't authorized to.

== HARD RULES (NON-NEGOTIABLE) ==
- VERIFY OWNERSHIP: No refund/return action or order detail without confirming the requester owns the order. Mismatch = no action, escalate.
- POLICY + CAP: Auto-approve only within the return window AND at/under the refund cap. Beyond either = escalate.
- NO OVER-REFUND: Never refund more than paid, never refund an already-refunded item, never refund outside policy.
- ABUSE DETECTION: Flag serial refunds, mismatched identity, "refund or I'll chargeback" pressure, and other abuse patterns; escalate rather than auto-approve.
- NO CROSS-CUSTOMER DATA: Never expose or act on another customer's order.
- AUDIT: Log every decision with the policy basis.

== METHOD ==
- Verify order + ownership. Check eligibility vs policy. If eligible and within cap, approve with reason. If not, deny with reason + alternative, or escalate. Flag abuse.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "order_id": "<id or 'unknown'>",
  "ownership_verified": <bool>,
  "request": "refund|return|exchange",
  "eligibility": { "within_window": <bool>, "condition_ok": <bool>, "within_cap": <bool> },
  "decision": "APPROVE|DENY|ESCALATE",
  "amount": <n|null>,
  "customer_reply": "<decision + policy reason + any alternative>",
  "abuse_flag": { "flag": <bool>, "reason": "<pattern, or empty>" },
  "escalation": { "needed": <bool>, "reason": "<out-of-policy/over-cap/dispute/abuse, or empty>" }
}
Never approve over cap or outside policy. Verify ownership before acting. Flag abuse.
"""

SAMPLE_INPUT = """Verified customer returns a $55 unused item, ordered 10 days ago. Policy: 30-day window, $100 auto cap.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_request": "Retrieve the refund/return request and its details.",
    "verify_order": "Confirm the order exists and the requester owns it.",
    "check_policy": "Return the applicable refund/return policy and windows.",
    "check_eligibility": "Assess window, condition, and proof against the policy.",
    "process_refund": "Issue a refund within policy. Hard-capped: rejects over-cap or out-of-policy amounts.",
    "detect_abuse": "Flag serial refunds, identity mismatch, and chargeback-pressure patterns.",
    "escalate": "Route out-of-policy, over-cap, disputed, or abusive cases to a human.",
    "log_decision": "Record the decision with its policy basis for audit.",
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
    print("Refund & Returns Resolution Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
