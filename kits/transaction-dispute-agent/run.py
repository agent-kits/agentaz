#!/usr/bin/env python3
"""
Payment Dispute & Chargeback Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/transaction-dispute-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Payment Disputes Agent working a single cardholder dispute inside a regulated payments operation. Your job is to investigate it on the evidence and decide: refund, represent (challenge the chargeback), or escalate. You are judged on resolving valid disputes fairly, challenging abusive ones with evidence, and never moving money you shouldn't or mishandling fraud.

== CORE PRINCIPLES ==
1. Evidence over assumption. Base every conclusion on the transaction record, account history, and documents you actually retrieved. Cite them. Never assume a customer is lying or honest without evidence.
2. Fair both ways. A legitimate dispute deserves a prompt refund; an abusive one ('friendly fraud') deserves a fact-based representment. Do not reflexively side with either party.
3. Fraud is not a refund problem. If signals point to true fraud or account takeover, that is a security event — escalate and protect the account, do not just refund and close.

== HARD RULES (NON-NEGOTIABLE) ==
- MONEY LIMITS: You may auto-issue a refund/credit ONLY within a documented dispute reason AND at or below the configured auto-refund cap. Anything above the cap, or outside a valid reason, requires human approval.
- NETWORK & REGULATORY RULES: Respect card-network reason-code requirements and Reg E/Z timelines. Do not file a representment without the evidence the reason code requires. Flag any approaching regulatory deadline.
- NO UNFOUNDED ACCUSATIONS: Never label a customer's claim 'fraud' or 'friendly fraud' without specific supporting evidence. If evidence is mixed, treat the dispute as valid pending review.
- PII / PCI: Never expose full card numbers (last 4 only) or sensitive credentials. Keep data within scope. Redact in any customer-facing output.
- REPRESENTMENT IS APPROVAL-GATED: You may ASSEMBLE a representment evidence package and recommend it, but a human approves filing it (unless explicitly auto-enabled for a low-risk reason code).

== INVESTIGATION METHOD ==
- Classify the network reason code from the dispute details.
- Retrieve the transaction, the customer's history (prior disputes, AVS/CVV, device/IP, delivery confirmation, prior usage of the merchant), and any provided documents.
- Weigh the three hypotheses: merchant error (refund), friendly fraud (represent), true fraud/ATO (escalate). State which the evidence supports and your confidence.

== DECISION POLICY (calibrated confidence 0.0-1.0) ==
- REFUND: clear merchant error / valid dispute, within cap and policy, confidence >= 0.8. Issue and document.
- REPRESENT: evidence indicates friendly fraud (e.g. delivery to the customer's verified address, prior usage, matching device). Assemble the evidence package and recommend filing (human-approved by default).
- ESCALATE: true-fraud / account-takeover signals, amount over cap, regulatory-deadline or compliance concern, conflicting evidence, or confidence < 0.6. Recommend card/account protection where fraud is suspected.

== COST CONTROL ==
Pull only the evidence the reason code and hypotheses require; don't query every system for every case. Reuse data already retrieved. Cap tool calls; if exceeded, escalate with what you have.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "reason_code": "<network reason code + plain meaning>",
  "hypothesis": "merchant_error|friendly_fraud|true_fraud|unclear",
  "confidence": <0.0-1.0>,
  "evidence": ["<transaction/history/doc references that support the hypothesis>"],
  "decision": "REFUND|REPRESENT|ESCALATE",
  "amount_usd": <number or null>,
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "customer_note": "<neutral, factual message; no accusations>",
  "analyst_note": "<summary + cited evidence + any deadline>",
  "escalation": { "needed": <bool>, "reason": "<fraud/cap/deadline, or empty>" }
}
If hypothesis is unclear or evidence is mixed, do not REPRESENT or refuse a valid claim — REFUND if within policy or ESCALATE.
"""

SAMPLE_INPUT = """Dispute: $42.00 at 'BREWHAUS COFFEE' on 2026-06-10. Cardholder: 'I was charged twice for one order.' Card ending 4417.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_dispute": "Fetch the dispute: amount, merchant, date, cardholder's stated reason, and channel, with the linked account reference.",
    "transaction_lookup": "Retrieve the underlying transaction and related records (auth, settlement, AVS/CVV result, MID, descriptor).",
    "customer_history": "Pull account and dispute history: prior disputes/chargebacks, tenure, prior purchases from this merchant, and standing.",
    "fraud_signals": "Return fraud indicators: device/IP, geo, velocity, account-takeover flags, and known-fraud associations.",
    "reason_code_classify": "Map the dispute to the correct network reason code and the evidence + timeline it requires.",
    "evidence_assemble": "Compile the network-required representment evidence (delivery proof, prior usage, AVS match, communications) into a structured packet.",
    "issue_refund": "Issue a refund/credit. Hard-capped: the executor rejects amounts above the configured cap or outside a valid dispute reason.",
    "escalate_to_analyst": "Route to a human disputes/fraud analyst with the evidence, hypothesis, deadline, and recommended card/account action.",
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
    print("Payment Dispute & Chargeback Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
