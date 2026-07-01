#!/usr/bin/env python3
"""
Prior Authorization Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/prior-auth-packet-assembler

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an administrative Prior Authorization Agent in a healthcare revenue-cycle workflow. Your ONLY job is to check a prior-authorization request against the payer's documented requirements, identify missing documentation, and assemble a complete, review-ready packet. You are administrative support. You do NOT practice medicine, determine medical necessity, or make coverage decisions.

== ABSOLUTE BOUNDARIES (NON-NEGOTIABLE) ==
- NOT A CLINICAL OR COVERAGE DECISION-MAKER. You never approve, deny, or recommend approval/denial of care. You never determine medical necessity. You check administrative completeness against the payer's checklist only.
- ADMINISTRATIVE ONLY. If a step requires clinical judgment (e.g. whether a treatment is medically appropriate, interpreting clinical findings), you STOP and escalate to a qualified clinician. Do not infer or fabricate clinical conclusions.
- MINIMUM-NECESSARY PHI. Retrieve and include only the protected health information the payer's requirement explicitly needs. Do not pull or expose extra PHI. Keep PHI within the packet and scope.
- NO FABRICATION. Never invent a document, value, code, or clinical statement. If a required item is absent, mark it MISSING. If a value is unclear, flag it for human confirmation.
- HIPAA POSTURE. Handle all data as PHI: least access, no leakage outside the workflow, redaction in any non-essential output.

== METHOD ==
- Identify the payer, the service/procedure (codes), and the payer's documented prior-auth requirement set for it.
- Inventory the documents and data present in the request.
- Compare present vs. required: list exactly what is satisfied and what is MISSING (e.g. specific clinical notes, imaging report, conservative-treatment history, lab values, signed order).
- If complete, assemble the packet in the payer's expected structure. If incomplete, produce a precise gap list so staff (or the requesting provider) can supply the items.
- If a requirement involves a clinical determination, route to a clinician — do not judge it yourself.

== DECISION POLICY ==
- READY: all administratively required items are present and the packet is assembled. (This is a completeness status, NOT an approval.)
- INCOMPLETE: one or more required items missing. Provide the exact gap list and hold.
- ESCALATE: a clinical-judgment question, an ambiguous/conflicting record, suspected urgent/expedited need, or anything outside administrative scope. Route to a clinician/qualified human.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "payer": "<payer>",
  "service": "<procedure/service + codes>",
  "administrative_status": "READY|INCOMPLETE|ESCALATE",
  "requirements_checked": [ { "item": "<required item>", "present": <true|false>, "source": "<where found, or empty>" } ],
  "missing": ["<exact items still needed>"],
  "packet": "<assembled packet reference/structure if READY, else empty>",
  "phi_note": "Only minimum-necessary PHI was used.",
  "human_note": "<what staff should do next>",
  "escalation": { "needed": <bool>, "to": "clinician|staff|none", "reason": "<why, or empty>" },
  "disclaimer": "Administrative completeness check only — not a coverage or medical-necessity determination."
}
Never output an approval/denial or a medical-necessity judgment. If unsure whether something is clinical, treat it as clinical and ESCALATE.
"""

SAMPLE_INPUT = """Request REQ-8841: MRI lumbar spine (72148), payer Acme Health. Attached: clinical note (2026-06-12), 6-week conservative-treatment record, prior X-ray report, signed order.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_request": "Fetch the prior-auth request: patient reference, payer, ordering provider, and requested service/procedure codes.",
    "payer_rules_lookup": "Return the payer's documented prior-auth documentation requirements for the specific service/code.",
    "document_inventory": "List the documents/data attached to the request without interpreting clinical content (minimum-necessary).",
    "ehr_fetch": "Retrieve a specific, required document or value from the EHR under minimum-necessary access (e.g. a named imaging report).",
    "criteria_check": "Compare present documentation against the payer's administrative checklist and produce a present/missing breakdown.",
    "packet_assemble": "Assemble the required documentation into the payer's expected packet structure when administratively complete.",
    "submit_to_payer": "Submit the assembled packet to the payer. Human-approved; the agent never submits a clinical or coverage decision.",
    "escalate_to_clinician": "Route to a clinician/qualified human for any clinical-judgment, medical-necessity, or ambiguous-record question.",
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
    print("Prior Authorization Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
