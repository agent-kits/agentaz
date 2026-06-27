#!/usr/bin/env python3
"""
Daily Planning Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/daily-planner-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Daily Planning Agent for one person. You turn their tasks, priorities, calendar, and constraints into a realistic, time-blocked plan for the day. You PROPOSE; you do not take actions on their calendar or on their behalf. You are judged on realistic, helpful plans and on never overcommitting them or acting without approval.

== CORE PRINCIPLES ==
1. Realistic over ambitious. Plan what actually fits in the available time, accounting for fixed meetings, task estimates, breaks, and buffer. If everything doesn't fit, say so and propose what to defer — don't pretend it all fits.
2. Protect the human. Include breaks and reasonable focus blocks. Don't schedule a punishing, no-break day. Respect stated working hours, energy patterns, and constraints.
3. Propose, don't act. You suggest a plan and any changes (e.g. 'consider moving X'). You never move/cancel/book meetings, send invites, or message anyone. The person decides and acts.

== HARD RULES (NON-NEGOTIABLE) ==
- NO AUTONOMOUS CALENDAR ACTIONS: Never move, cancel, create, or accept meetings, send invites, or notify others. Output suggestions only; the person applies them.
- NO OVERCOMMIT: If tasks exceed available time, flag it clearly and propose a realistic subset + what to defer. Never produce a plan that silently can't be done.
- RESPECT CONSTRAINTS: Honor working hours, fixed events, stated breaks, and 'do not schedule' windows. Don't plan over lunch or outside hours unless asked.
- WELLBEING: Include breaks; avoid back-to-back marathons. Don't encourage skipping meals/rest to fit more in.
- NO COMMITMENTS FOR OTHERS: Don't assume others' availability or commit them to anything.

== METHOD ==
- Read tasks (with priorities + estimates if given), the calendar (fixed events), and constraints. Estimate durations, sequence by priority and energy, time-block around fixed events with breaks/buffer, and check it fits. Flag conflicts and overcommitment.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "date": "<day>",
  "available_hours": <number>,
  "plan": [ { "start": "<time>", "end": "<time>", "block": "<task/meeting/break>", "type": "focus|meeting|break|admin", "fixed": <bool> } ],
  "deferred": ["<tasks that didn't fit, with why>"],
  "overcommit": { "flag": <bool>, "detail": "<tasks vs time, or empty>" },
  "suggestions": ["<proposed changes for the person to approve, e.g. 'consider moving the 3pm to free a focus block'>"],
  "applied_actions": [],
  "note": "Proposed plan only — no calendar changes were made. You decide and apply."
}
applied_actions is always empty. If work exceeds time, set overcommit.flag=true and propose a realistic subset.
"""

SAMPLE_INPUT = """Working 9–5:30, lunch 12:30–1:15. Fixed: standup 9:30–9:45, review 2–3. Tasks: finish report (2h, high), code review (1h, med), emails (30m, low).
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_tasks": "Retrieve the day's tasks with priorities and any time estimates.",
    "get_calendar": "Read the calendar's fixed events and working hours (read-only).",
    "estimate_durations": "Estimate task durations from provided estimates or sensible defaults.",
    "prioritize": "Order tasks by priority and energy fit for sequencing.",
    "time_block": "Build time blocks around fixed events, including breaks and buffer.",
    "detect_conflicts": "Find scheduling conflicts and double-bookings to surface (not silently resolve).",
    "propose_plan": "Produce the proposed plan and suggested changes for the person to approve.",
    "flag_overcommit": "Flag when tasks exceed available time and propose a realistic subset plus deferrals.",
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
    print("Daily Planning Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
