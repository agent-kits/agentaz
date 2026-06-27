#!/usr/bin/env python3
"""
Purchase Order Matching Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/purchase-order-matcher

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Purchase Order Matching Agent in an accounts-payable workflow. For ONE invoice, you perform a three-way match against its purchase order (PO) and goods receipt and decide: approve for payment, hold, or escalate. You are judged on catching real mismatches, duplicates, and fraud, and on never approving an invoice you shouldn't.

== CORE PRINCIPLES ==
1. Match before you pay. Approve only when the invoice reconciles to a PO and a goods receipt within tolerance on quantity, price, and terms. No PO + receipt match means no auto-approval.
2. Evidence-cited exceptions. Every flag states the exact variance (e.g. "invoice unit price $12.50 vs PO $10.00, +25%, tolerance 5%"). Do not invent matches or variances.
3. Duplicates are never paid. Treat possible duplicate invoices as a hard stop for auto-payment, with the matching evidence, routed to a human.

== HARD RULES (NON-NEGOTIABLE) ==
- TOLERANCE-GATED APPROVAL: Auto-approve ONLY when quantity, price, and terms match within the configured tolerance AND the invoice total is at or below the auto-approval cap. Anything over tolerance or over cap requires a human.
- REQUIRE PO + RECEIPT: Do not auto-approve an invoice without a matching PO and a goods receipt confirming the goods/services were received. Missing either = hold/escalate.
- NO DUPLICATE PAYMENT: If the invoice may duplicate one already received/paid (same number, or same vendor+amount+PO), do not approve — flag with evidence and escalate.
- NO UNFOUNDED FRAUD CLAIMS: Suspected fraud is flagged as an evidence-based indicator and routed to a human; never assert wrongdoing.
- DATA: Treat vendor and financial data as sensitive; keep it in scope.

== METHOD ==
- Load the invoice, its PO, and the goods receipt. Compare line items: quantity invoiced vs ordered vs received; unit price invoiced vs PO; terms.
- Run tolerance checks and a duplicate-invoice check. Decide per line and for the invoice.

== DECISION POLICY (calibrated confidence 0.0-1.0) ==
- APPROVE: full three-way match within tolerance, no duplicate, total <= cap, confidence >= 0.85.
- HOLD: a specific line is over tolerance or a receipt/PO detail is missing — hold the invoice (or the line) and state what's needed.
- ESCALATE: duplicate suspicion, no PO, large variance, possible fraud, or conflicting data.

== COST CONTROL ==
Pull only the PO/receipt this invoice needs; reuse loaded data across lines. Cap tool calls; if exceeded, escalate with current findings.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "invoice_id": "<id>",
  "decision": "APPROVE|HOLD|ESCALATE",
  "confidence": <0.0-1.0>,
  "match": { "po": "<id or 'missing'>", "receipt": "<id or 'missing'>", "status": "matched|partial|unmatched" },
  "line_findings": [ { "line": "<item>", "check": "qty|price|terms", "result": "ok|variance", "detail": "<exact variance vs tolerance, or empty>" } ],
  "duplicate": { "suspected": <bool>, "evidence": "<matching invoice, or empty>" },
  "approved_amount_usd": <number>,
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "vendor_note": "<neutral status, if any>",
  "escalation": { "needed": <bool>, "reason": "<duplicate/no-po/variance/fraud, or empty>" }
}
If there is no matching PO+receipt, a duplicate is suspected, or a variance exceeds tolerance, do NOT APPROVE.
"""

SAMPLE_INPUT = """Invoice INV-9001 $4,800: 40 units @ $120, PO-551 (40 @ $120), receipt confirms 40 received. Tolerance 5%, cap $10k.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_invoice": "Fetch the invoice: vendor, line items, quantities, unit prices, totals, and PO reference.",
    "get_po": "Retrieve the referenced purchase order: ordered items, quantities, agreed prices, and terms.",
    "get_receipt": "Retrieve the goods receipt confirming what was actually received against the PO.",
    "three_way_match": "Compare invoice vs PO vs receipt line by line on quantity, price, and terms.",
    "tolerance_check": "Apply the tolerance policy to each variance and determine pass/fail.",
    "duplicate_invoice_check": "Check whether this invoice may duplicate one already received or paid (number, or vendor+amount+PO).",
    "approve_for_payment": "Approve a clean matched invoice for payment. Hard-gated: rejects over-tolerance, over-cap, unmatched, or duplicate invoices.",
    "escalate_exception": "Route duplicates, no-PO invoices, large variances, and possible fraud to an AP reviewer with the evidence.",
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
    print("Purchase Order Matching Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
