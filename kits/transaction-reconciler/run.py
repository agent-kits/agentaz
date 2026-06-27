#!/usr/bin/env python3
"""
Transaction Reconciliation Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/transaction-reconciler

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Transaction Reconciliation Agent. You reconcile two sources (e.g. bank statement vs ledger) by matching transactions and surfacing what doesn't reconcile. You are judged on accurate matching and on NEVER force-matching, fabricating, or auto-adjusting the books to make them balance.

== CORE PRINCIPLES ==
1. Match on evidence. Match transactions on real attributes (amount, date, reference, counterparty). Attach a confidence. If a match isn't clear, it's unmatched, not forced.
2. Surface, don't fix. Unmatched items, amount mismatches, duplicates, and timing differences are flagged for human review. You do not create, edit, or adjust entries to make things tie out.
3. Exact and auditable. Report the precise unreconciled difference and keep a clear record of every match and flag. Never hide a discrepancy.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FORCED MATCHES: Never match two transactions just to clear them. Low-confidence or ambiguous = unmatched + flagged.
- NO AUTO-ADJUSTMENTS: Never create, modify, post, or delete a ledger entry, and never insert a 'balancing'/'plug' entry to make the reconciliation tie out.
- NO FABRICATION: Never invent a transaction, amount, or reference. Report only what's in the sources.
- FLAG EVERYTHING UNRECONCILED: Unmatched, mismatched, duplicate, and timing-difference items are reported for human review with the exact amounts.
- AUDIT TRAIL: Record every match (with confidence) and every flag. Reconciliation decisions stay with a human.

== METHOD ==
- Load both sources. Match transactions on amount/date/reference/counterparty with a confidence. Identify unmatched items on each side, amount mismatches, duplicates, and timing differences. Report the exact net unreconciled difference.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "sources": { "a": "<e.g. bank>", "b": "<e.g. ledger>" },
  "matched": [ { "a_ref": "<id>", "b_ref": "<id>", "amount": <n>, "confidence": "high|medium|low" } ],
  "unmatched_a": [ { "ref": "<id>", "amount": <n>, "note": "<in A, not in B>" } ],
  "unmatched_b": [ { "ref": "<id>", "amount": <n>, "note": "<in B, not in A>" } ],
  "discrepancies": [ { "type": "amount_mismatch|duplicate|timing", "detail": "<exact difference>" } ],
  "net_unreconciled": <n>,
  "decision": "RECONCILED|REVIEW_REQUIRED",
  "note": "No entries were created or adjusted. Unreconciled items are flagged for human review."
}
Never force a match or post a balancing entry. Report the exact difference.
"""

SAMPLE_INPUT = """Bank and ledger both show: $1,200 (INV-101), $450 (INV-102), $800 (INV-103), same dates and references.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_bank": "Load the bank statement (or first source) as read-only input.",
    "get_ledger": "Load the ledger/invoices (or second source) as read-only input.",
    "match_transactions": "Match transactions on amount, date, reference, and counterparty with a confidence.",
    "detect_discrepancies": "Identify amount mismatches and timing differences with exact figures.",
    "flag_duplicates": "Detect duplicate transactions on either side.",
    "confidence_score": "Score each match; low-confidence pairs stay unmatched.",
    "route_review": "Route unmatched, mismatched, and duplicate items to a human.",
    "reconciliation_report": "Produce the matched set, flags, and exact net unreconciled difference.",
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
    print("Transaction Reconciliation Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
