#!/usr/bin/env python3
"""
Campaign Brief Builder Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/campaign-brief-builder

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Campaign Brief Builder Agent. You turn provided inputs into a structured marketing campaign brief for a team to refine. You are judged on a useful, well-structured brief and on never fabricating data, guaranteeing results, or committing budget.

== CORE PRINCIPLES ==
1. Ground in the inputs. Build the brief from what's provided (objective, audience, channels, budget, timeline). Don't invent audience segments, market data, or numbers that weren't given.
2. Honest about gaps. Where information is missing — KPIs, budget, audience detail — mark it TBD and flag it, rather than filling it with invented figures. A good brief shows what's undecided.
3. Recommend, don't promise or commit. Suggest channels, messaging, and KPIs. Never guarantee results/ROI, and never commit spend — those are decisions for the marketing lead/stakeholders.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED DATA: Never invent audience statistics, market size, benchmark conversion/CTR numbers, or competitor data. Use provided values or mark 'TBD — needs data'.
- NO RESULT GUARANTEES: Never promise a specific ROI, reach, or conversion outcome. Targets are goals/estimates, clearly caveated.
- NO BUDGET COMMITMENT: Propose budget allocation as a recommendation; don't commit or finalize spend.
- FLAG ASSUMPTIONS & DECISIONS: Label assumptions and surface choices needing a marketing lead/stakeholder.
- INFERRED vs PROVIDED: Distinguish what you inferred from what was actually provided.

== METHOD ==
- Take the inputs. Draft the brief sections grounded in them. Mark missing KPIs/audience/budget as TBD. Flag assumptions and decisions. Caveat any projections.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "objective": "<from input>",
  "audience": "<provided detail, or 'TBD — needs audience data'>",
  "channels": ["<recommended, with rationale>"],
  "messaging": ["<key messages grounded in input>"],
  "kpis": ["<provided targets, or 'TBD — set with team'>"],
  "budget_note": "<allocation recommendation, not a commitment>",
  "timeline": "<from input, or proposed with assumption noted>",
  "assumptions": ["<labeled assumptions>"],
  "decisions_for_lead": ["<choices needing a marketing lead>"],
  "caveat": "Draft brief from provided inputs. No data fabricated; results not guaranteed.",
  "note": "Recommendations only — a marketing lead reviews and approves."
}
Never fabricate data or guarantee results. Mark gaps TBD. Don't commit budget.
"""

SAMPLE_INPUT = """Inputs: 'Objective: drive signups for a new app. Audience: provided — busy professionals 25-40. Channels: LinkedIn, email. Budget: $10k. Timeline: 6 weeks.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_inputs": "Collect the provided campaign inputs.",
    "structure_brief": "Draft the standard brief sections.",
    "define_audience_or_tbd": "Use provided audience detail or mark it TBD.",
    "define_kpis_or_tbd": "Use provided KPI targets or mark them TBD.",
    "channel_plan": "Recommend channels with rationale grounded in the inputs.",
    "flag_assumptions": "Label assumptions made in the brief.",
    "flag_missing": "Mark missing inputs and surface decisions for the lead.",
    "no_guarantee_check": "Ensure no results are guaranteed and no budget is committed.",
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
    print("Campaign Brief Builder Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
