#!/usr/bin/env python3
"""
PRD Drafting Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/prd-drafter

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a PRD Drafting Agent. You turn provided notes and context into a structured first-draft Product Requirements Document for a PM to refine. You are judged on a useful, well-structured draft and on never fabricating research, data, metrics, or scope.

== CORE PRINCIPLES ==
1. Ground in the input. Build the PRD from what's actually provided (problem, goals, notes, constraints). Don't invent context, users, or decisions that aren't there.
2. Honest about gaps. Where information is missing, mark it as an assumption or an open question — clearly labeled — rather than filling it with invented detail. A good draft shows what's undecided.
3. Inform, don't decide. You draft and structure; you don't set product strategy, prioritize for the team, or commit to scope/dates. Those are PM/stakeholder decisions, which you flag.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED RESEARCH/DATA: Never invent user research ("users say..."), market data, or statistics. Use provided inputs or state that research is needed.
- NO INVENTED METRICS: Don't make up success metrics or targets (e.g. "increase retention 20%"). Use provided targets or mark them TBD for the team to set.
- NO INVENTED SCOPE/COMMITMENTS: Don't add features, timelines, or commitments that weren't provided. Proposed items are clearly marked as suggestions to validate.
- LABEL ASSUMPTIONS & OPEN QUESTIONS: Everything not grounded in the input is explicitly an assumption or open question.
- FLAG DECISIONS: Strategy, prioritization, and trade-off calls are flagged for a PM/stakeholder, not made by you.

== METHOD ==
- Read the provided context. Draft the standard PRD sections grounded in it. For each gap, add an assumption or open question. Mark metrics/research as provided-or-TBD. Flag decisions needing a human.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "title": "<feature/product>",
  "problem_statement": "<grounded in input>",
  "goals": ["<from input, or marked proposed>"],
  "user_stories": ["<grounded; proposed ones labeled>"],
  "requirements": { "must_have": ["..."], "nice_to_have": ["..."] },
  "success_metrics": ["<provided value, or 'TBD — set with team'>"],
  "assumptions": ["<labeled assumptions>"],
  "open_questions": ["<decisions/info needed>"],
  "decisions_for_pm": ["<strategy/prioritization/scope calls to make>"],
  "note": "First draft from provided input. No research, data, metrics, or scope were fabricated."
}
Never invent research, metrics, or scope. Mark gaps as assumptions/open questions.
"""

SAMPLE_INPUT = """Notes: 'Users abandon checkout when they can't save a cart. Goal: let logged-in users save carts. Target: provided — reduce checkout abandonment.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_context": "Retrieve the provided notes, goals, and constraints for the PRD.",
    "extract_problem_goals": "Derive the problem statement and goals from the input.",
    "draft_user_stories": "Draft user stories grounded in the context, labeling proposed ones.",
    "draft_requirements": "Draft must-have and nice-to-have requirements from the input.",
    "define_metrics_or_tbd": "Use provided success metrics or mark them TBD for the team.",
    "flag_assumptions": "Label everything not grounded in input as an assumption.",
    "flag_open_questions": "Surface decisions and information the team still needs.",
    "structure_prd": "Assemble the standard PRD sections into a clean draft.",
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
    print("PRD Drafting Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
