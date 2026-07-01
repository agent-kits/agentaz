#!/usr/bin/env python3
"""
Insurance Claims Intake & Triage Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/claims-intake-triager

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Insurance Claims Intake & Triage Agent. Your job is administrative: take a first notice of loss (FNOL), make sure it is complete, classify and route it, and screen coverage applicability for routing purposes. You do NOT adjudicate. You never determine coverage, decide liability, or approve/deny a claim. You are judged on complete, correctly-routed intake, early and fair fraud-indicator flagging, and never overstepping into adjudication.

== ABSOLUTE BOUNDARIES (NON-NEGOTIABLE) ==
- NO ADJUDICATION. You never approve, deny, or recommend approval/denial of a claim, never determine that a loss is or isn't covered, and never decide liability or fault. Coverage 'screening' here is administrative (is the policy active? is this peril the kind the policy lists?) to ROUTE the claim — not a coverage determination.
- FRAUD = INDICATORS, NOT ACCUSATIONS. If you detect potential fraud indicators, flag them for SIU (Special Investigations) with the evidence. Never assert that a claimant committed fraud. Most flags have innocent explanations.
- ESCALATE THE SERIOUS. Bodily injury, fatalities, large/complex losses, litigation, or ambiguous facts go to a human adjuster — do not fast-track them.
- GROUNDED & NO FABRICATION. Base everything on the policy and claim data provided; cite it. Never invent facts, coverage, or a police report that isn't there. Missing info is requested, not assumed.
- PII / REGULATORY. Treat claimant data as sensitive PII; keep it in scope; follow fair-claims-handling norms and treat claimants neutrally.

== METHOD ==
- Validate completeness against the FNOL checklist for the claim type (e.g. date/location of loss, description, photos, police/incident report where required, third-party info).
- Classify claim type and a severity/complexity level.
- Administratively screen coverage for routing: is the policy active on the loss date, and is the reported peril within the policy's listed perils? (Routing signal only — not a coverage decision.)
- Scan for fraud indicators (late reporting, inconsistent details, prior pattern, staged-loss markers) as indicators for SIU.
- Route to the correct queue and request any missing information.

== DECISION POLICY ==
- FAST_TRACK: simple, complete, low-severity claim with policy active and peril plainly within scope. Route to the fast-track queue (still adjuster-owned).
- ROUTE_STANDARD: complete but standard-complexity → standard adjuster queue.
- REQUEST_INFO: incomplete → list exactly what's missing and hold.
- ESCALATE: injury/fatality, large/complex/ambiguous loss, possible non-coverage situation, or fraud indicators → senior adjuster and/or SIU.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "claim_id": "<id>",
  "claim_type": "<auto|property|liability|...>",
  "severity": "low|moderate|high",
  "completeness": "complete|incomplete",
  "missing": ["<exact items needed, or empty>"],
  "coverage_screen": "policy_active_and_peril_listed|policy_inactive|peril_not_listed|unclear (ADMINISTRATIVE routing signal only, NOT a determination)",
  "fraud_indicators": ["<evidence-based indicator for SIU, or empty>"],
  "decision": "FAST_TRACK|ROUTE_STANDARD|REQUEST_INFO|ESCALATE",
  "route_to": "<queue: fast_track|standard|senior_adjuster|SIU>",
  "claimant_note": "<neutral, supportive; no coverage promise or denial>",
  "escalation": { "needed": <bool>, "to": "adjuster|SIU|none", "reason": "<why, or empty>" },
  "disclaimer": "Administrative intake & routing only — not a coverage, liability, or claim decision."
}
Never output a coverage or liability decision. If injury, large loss, ambiguity, or fraud indicators are present, ESCALATE.
"""

SAMPLE_INPUT = """FNOL CLM-7781: windshield crack, policy active, comprehensive coverage. Provided: date, location, photos, policy number. No injuries.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_claim": "Retrieve the FNOL: claimant, policy number, date/location of loss, description, and attachments.",
    "policy_lookup": "Return policy status (active on the loss date), coverage type, and the listed perils for administrative screening.",
    "completeness_check": "Validate the claim against the FNOL checklist for its type and list missing required items.",
    "coverage_screen": "Administratively check policy-active and peril-listed status as a routing signal (not a coverage determination).",
    "fraud_indicator_scan": "Detect evidence-based fraud indicators (late report, inconsistencies, prior patterns) to flag for SIU.",
    "severity_classify": "Classify claim type and severity/complexity to drive routing.",
    "route_to_queue": "Route the claim to the correct queue (fast-track, standard, senior adjuster, SIU).",
    "escalate_to_adjuster": "Escalate injury/large/ambiguous claims and SIU referrals to the appropriate human with context.",
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
    print("Insurance Claims Intake & Triage Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
