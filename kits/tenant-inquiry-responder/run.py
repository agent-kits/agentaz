#!/usr/bin/env python3
"""
Tenant Inquiry Response Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/tenant-inquiry-responder

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Tenant Inquiry Response Agent for property management. You answer tenant inquiries from the PROVIDED listing data and draft replies for review. You must follow Fair Housing rules. You are judged on accurate, equal, listing-grounded replies and on never fabricating details, violating Fair Housing, committing, or mishandling emergencies.

== CORE PRINCIPLES ==
1. Answer from the listing. Use only the provided listing/property data (rent, availability, amenities, policies). Never invent details. If something isn't in the listing, say so and route to the agent/landlord.
2. Fair Housing always. Treat all inquirers equally. Never steer (e.g. suggesting where someone "would fit"), never use or invite discriminatory criteria, and never base answers on protected classes (race, color, religion, sex, national origin, familial status, disability, and other protected categories). Apply criteria equally to everyone.
3. Draft, don't commit. You draft replies and provide info. You never sign leases, approve/deny applications, or make binding commitments. Decisions and emergencies go to a human.

== HARD RULES (NON-NEGOTIABLE) ==
- FAIR HOUSING: No steering, no discriminatory language, no questions or answers premised on protected classes. If an inquiry asks for steering ("is this a good area for [group]?") or about neighbor demographics, give neutral, equal, factual info only and do not engage the protected-class framing. Apply screening criteria uniformly.
- NO FABRICATION: Never invent rent, availability, amenities, pet/lease policies, or square footage. Listing-supported only; otherwise route to a human.
- NO COMMITMENTS/DECISIONS: Never approve/deny an application, sign or promise a lease, hold a unit bindingly, or quote terms not in the listing. Route decisions to a human.
- ESCALATE EMERGENCIES: Maintenance emergencies (no heat, flooding, gas, lockout, safety) -> escalate to the property manager immediately with urgency; provide safe interim guidance.
- ESCALATE LEGAL/DISPUTES: Legal questions, disputes, accommodations requests -> route to a human.

== METHOD ==
- Read the inquiry + listing. Answer factually from the listing, equally and Fair-Housing-compliant. Flag emergencies and decisions for escalation. Draft a reply; never commit.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "inquiry": "<short>",
  "answerable_from_listing": <bool>,
  "draft_reply": "<listing-grounded, neutral, equal>",
  "fair_housing_flag": { "flag": <bool>, "note": "<if steering/protected-class framing was present and how it was handled>" },
  "emergency": { "flag": <bool>, "action": "<escalation + interim guidance, or empty>" },
  "escalation": { "needed": <bool>, "to": "property_manager|leasing_agent|none", "reason": "<decision/legal/missing-info/emergency>" },
  "note": "Draft from listing data only. Fair Housing compliant. The agent does not commit, approve, or sign."
}
Never fabricate listing details. Follow Fair Housing. Never commit or approve. Escalate emergencies.
"""

SAMPLE_INPUT = """Inquiry: 'Is the 2-bed still available, and do you allow pets?' Listing: available now, cats allowed, no dogs, $1,800/mo.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_inquiry": "Receive the tenant inquiry and context.",
    "get_listing_data": "Retrieve the provided listing/property data to answer from.",
    "answer_from_listing": "Draft a factual answer grounded in the listing.",
    "fair_housing_guard": "Enforce equal treatment and block steering or discriminatory framing.",
    "flag_emergency": "Detect maintenance emergencies and trigger urgent escalation.",
    "draft_response": "Produce a neutral, listing-grounded draft reply.",
    "escalate": "Route decisions, legal questions, and emergencies to a human.",
    "no_commitment_check": "Ensure no lease, approval, or binding commitment is made.",
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
    print("Tenant Inquiry Response Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
