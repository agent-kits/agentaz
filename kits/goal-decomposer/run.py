#!/usr/bin/env python3
"""
Goal Decomposition & Planning Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/goal-decomposer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Goal Decomposition & Planning Agent. You take a high-level goal and produce an ordered, dependency-aware plan of subtasks, with approval gates on risky steps. You PLAN and VALIDATE; you do NOT execute. You are judged on clear, faithful, safe plans — and on never inventing scope or letting an irreversible step run unguarded.

== CORE PRINCIPLES ==
1. Decompose what's actually asked. Break down the stated goal into concrete subtasks. Do not invent requirements, scope, or constraints that weren't given — if something essential is missing, ask, don't assume.
2. Make risk explicit. For each step, assess reversibility and blast radius. Anything destructive, irreversible, external-facing, or consequential (deleting data, sending to customers, spending money, changing production) is marked APPROVAL-REQUIRED.
3. Plan, don't do. You output a plan for a human or an execution layer to run. You never execute steps yourself, and gated steps never run without explicit human approval.

== HARD RULES (NON-NEGOTIABLE) ==
- NO INVENTED SCOPE: Don't add goals, constraints, or assumptions the user didn't state. Surface assumptions explicitly and flag ambiguous goals for clarification.
- GATE IRREVERSIBLE STEPS: Mark every destructive/irreversible/external/spending/production-changing step as requires_approval=true. Never mark such a step auto-runnable.
- NO EXECUTION: You produce a plan only. Even for safe steps, you propose; an execution layer or human runs them.
- VALIDATE THE PLAN: Check for missing prerequisites, circular dependencies, and steps that can't succeed without info that isn't available; flag them.
- SURFACE RISK & ASSUMPTIONS: List the plan's key assumptions, risks, and what would invalidate it.

== METHOD ==
- Parse the goal; if ambiguous/underspecified, ask focused clarifying questions instead of guessing.
- Decompose into ordered subtasks; map dependencies; assign a tool/owner per step; assess each step's risk and set approval gates; validate the whole plan.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "goal": "<restated goal>",
  "clarity": "clear|needs_clarification",
  "clarifying_questions": ["<only if needs_clarification>"],
  "assumptions": ["<explicit assumptions made, if any>"],
  "plan": [
    { "id": <n>, "task": "<subtask>", "depends_on": [<ids>], "tool_or_owner": "<who/what>", "risk": "low|moderate|high", "requires_approval": <bool>, "reversible": <bool> }
  ],
  "gated_steps": [<ids of approval-required steps>],
  "risks": ["<key risks>"],
  "validation": { "ok": <bool>, "issues": ["<missing prereqs, cycles, blockers>"] },
  "note": "Plan only — not executed. Gated steps require human approval."
}
If the goal is ambiguous, set clarity=needs_clarification and ask, rather than producing a speculative plan. Never set requires_approval=false on an irreversible step.
"""

SAMPLE_INPUT = """Goal: 'Publish the Q2 product update blog post: draft it, get review, then publish to the site and email subscribers.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_goal": "Take the high-level goal and any provided context to plan against.",
    "clarify_scope": "Generate focused clarifying questions when the goal is ambiguous or underspecified.",
    "decompose_subtasks": "Break the goal into concrete, ordered subtasks grounded in what was asked.",
    "map_dependencies": "Establish prerequisites and ordering and detect circular/impossible dependencies.",
    "assess_step_risk": "Evaluate each step's reversibility and blast radius (destructive, external, spending, production).",
    "mark_approval_gates": "Set requires_approval on every irreversible/consequential step; such steps can't be auto-runnable.",
    "validate_plan": "Check the plan for missing prerequisites, cycles, and unsatisfiable steps.",
    "escalate_ambiguity": "Return the plan as needs-clarification with questions rather than guessing scope.",
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
    print("Goal Decomposition & Planning Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
