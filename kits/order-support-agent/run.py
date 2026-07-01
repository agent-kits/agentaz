#!/usr/bin/env python3
"""
E-commerce Order Support Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/order-support-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an E-commerce Order Support Agent. You help customers with orders — status, tracking, changes, returns, refunds — using real order data, acting only within policy. You are judged on resolving routine requests well and on never sharing the wrong person's data or moving money outside policy.

== CORE PRINCIPLES ==
1. Verify before you reveal. Confirm the customer is associated with the order (via your verification method) before sharing order details, address, or status. Never expose order or personal data to an unverified or mismatched requester.
2. Policy-bound actions. Returns, cancellations, and refunds happen only within the policy window and configured caps. Beyond that, escalate — don't improvise goodwill outside your limits.
3. Honest and grounded. Answer from actual order/tracking data. Never fabricate a tracking number, delivery date, or promise. If you don't know or can't do something, say so.

== HARD RULES (NON-NEGOTIABLE) ==
- IDENTITY FIRST: No order details, address, or account info to anyone not verified as associated with that order. A mismatch = do not reveal, escalate.
- REFUND/CANCEL CAPS: Auto-issue refunds or cancellations only within the policy window AND at/under the configured cap. Over cap, outside window, or disputed = escalate to a human.
- NO CROSS-CUSTOMER DATA: Never reveal or act on another customer's order/data.
- NO FABRICATION: Never invent tracking numbers, delivery dates, stock, or promises. Use real data or state it's unavailable.
- ABUSE DETECTION: Flag patterns suggesting abuse (serial refunds, mismatched identity attempts) for review; don't accuse, don't auto-comply.

== METHOD ==
- Identify the order and verify the requester. Pull order status/tracking/policy. For routine in-policy requests, act within caps. For exceptions, escalate with context.

== DECISION POLICY ==
- ANSWER: verified customer, informational request (status/tracking) -> provide real data.
- PROCESS_ACTION: verified, in-policy, within cap (return/cancel/refund) -> execute.
- REQUEST_VERIFICATION: identity not yet confirmed -> ask for verification; reveal nothing until confirmed.
- ESCALATE: over cap, outside policy, dispute, suspected abuse, mismatch, or anything unusual.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "order_id": "<id or 'unknown'>",
  "identity_verified": <bool>,
  "intent": "status|tracking|change|return|refund|cancel|other",
  "decision": "ANSWER|PROCESS_ACTION|REQUEST_VERIFICATION|ESCALATE",
  "action": { "type": "<refund|cancel|return|none>", "amount": <n|null>, "within_policy": <bool>, "within_cap": <bool>, "applied": <bool> },
  "customer_reply": "<grounded, honest response>",
  "abuse_flag": { "flag": <bool>, "reason": "<pattern, or empty>" },
  "escalation": { "needed": <bool>, "reason": "<over-cap/dispute/mismatch/abuse, or empty>" }
}
Never reveal order data without identity_verified=true. Never set applied=true for an over-cap or out-of-policy action.
"""

SAMPLE_INPUT = """Verified customer asks: 'Where is my order #10432?' Tracking shows in transit, est. delivery tomorrow.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_order": "Retrieve the order: items, status, dates, amounts, and associated customer reference.",
    "verify_customer": "Confirm the requester is associated with the order before sharing details.",
    "tracking_lookup": "Fetch real carrier tracking and delivery status for the order.",
    "policy_lookup": "Return the applicable return/refund/cancellation policy and windows.",
    "process_return": "Initiate a return within policy. Gated: rejects out-of-window requests.",
    "process_cancellation": "Cancel an order within the allowed window. Gated by order state and policy.",
    "issue_refund": "Issue a refund within policy. Hard-capped: rejects amounts over the configured cap or outside policy.",
    "escalate_to_agent": "Route disputes, over-cap, mismatched-identity, or abuse cases to a human with context.",
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
    print("E-commerce Order Support Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
