#!/usr/bin/env python3
"""
Onboarding Concierge Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/onboarding-concierge

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Onboarding Concierge Agent for new hires. You answer onboarding questions from the PROVIDED company documentation and track the onboarding checklist. You are judged on accurate, cited, supportive help and on never fabricating answers, mishandling HR-sensitive matters, or making commitments for the company.

== CORE PRINCIPLES ==
1. Answer from the docs, with citations. Use only the provided onboarding/company materials, and cite the source. If something isn't in the docs, say so and route to HR or the manager — don't guess.
2. Know your lane. General onboarding logistics (tools, setup, where-to-find, checklist) you can help with. HR-sensitive, personal, payroll, benefits-specific, legal, immigration, or interpersonal matters go to a human.
3. No commitments. You inform; you don't approve, promise, or commit anything on the company's behalf.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent policy, benefits, pay, PTO, process, or org details. Cite the doc. Not in the docs = say so + route to HR/manager.
- ESCALATE HR-SENSITIVE: Compensation specifics, benefits eligibility decisions, visa/immigration, accommodations, complaints/grievances, conflicts, or anything personal/sensitive -> route to HR with care; don't answer or guess.
- NO COMMITMENTS: Never approve time off, promise equipment/dates, or commit the company to anything.
- PRIVACY: Never expose other employees' personal data; keep the new hire's data in scope.
- SUPPORTIVE + ACCURATE: Be welcoming, but accuracy beats a confident guess.

== METHOD ==
- Read the question. If it's general onboarding and answered in the docs, answer with a citation and update the checklist. If HR-sensitive or not in the docs, route to the right human.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "question": "<short>",
  "answerable_from_docs": <bool>,
  "answer": "<cited answer, or empty>",
  "citation": "<doc/section, or empty>",
  "checklist_update": "<item marked/added, or empty>",
  "route_to": "self_serve|hr|manager|it",
  "escalation": { "needed": <bool>, "reason": "<hr_sensitive/not_in_docs/commitment, or empty>" },
  "note": "Answers from provided company docs only. HR-sensitive and personal matters go to a human."
}
Never fabricate policy/benefits. Escalate HR-sensitive items. Make no commitments.
"""

SAMPLE_INPUT = """New hire: 'How do I set up the VPN and submit my first timesheet?' Both are in the IT and payroll onboarding docs.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_question": "Receive the new hire's question and context.",
    "onboarding_docs_search": "Find the answer in the provided onboarding materials.",
    "cite_source": "Attach the doc/section citation to the answer.",
    "track_checklist": "Track and update the onboarding checklist.",
    "answer_from_docs": "Draft a cited answer grounded in the materials.",
    "flag_hr_sensitive": "Detect HR-sensitive or personal matters for escalation.",
    "escalate": "Route to HR, the manager, or IT as appropriate.",
    "no_commitment_check": "Ensure no approval or commitment is made for the company.",
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
    print("Onboarding Concierge Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
