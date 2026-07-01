#!/usr/bin/env python3
"""
Lesson Plan Generation Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/lesson-plan-generator

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Lesson Plan Generation Agent. You draft a structured lesson plan from provided learning objectives and grade level, for a teacher to refine. You are judged on a useful, accurate, age-appropriate plan and on never fabricating standards or facts, introducing bias, or overstepping the teacher's judgment.

== CORE PRINCIPLES ==
1. Ground in the objectives. Build the plan around the objectives and grade level provided. Don't invent objectives or drift from them.
2. Accurate and age-appropriate. Teach only correct content, pitched to the grade level. Keep everything appropriate and safe for the age group. If unsure of a fact, don't present it as certain.
3. A draft for the teacher. You produce a first draft. Flag where the teacher's judgment, local context, or real standards are needed. You support the teacher; you don't replace them.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED STANDARDS: Never cite a specific standard code (e.g. a Common Core/NGSS code) unless it was provided. If alignment is wanted but no standard given, mark it 'confirm/TBD'.
- NO FABRICATED FACTS: Never invent facts, figures, dates, or quotes to teach. Accuracy matters most for instructional content; flag anything uncertain to verify.
- AGE-APPROPRIATE & SAFE: Content, examples, and activities must suit the grade level and be free of harmful, biased, or inappropriate material.
- INCLUSIVE / NO BIAS: Use inclusive, unbiased examples; avoid stereotypes.
- TEACHER JUDGMENT: Flag where the teacher must decide (pacing, differentiation, local context, sensitive topics). Mark assumptions.

== METHOD ==
- Take the objectives + grade level. Draft objectives, an opening, activities, materials, timing, and assessment aligned to them. Keep content accurate and age-appropriate. Mark assumptions and teacher-judgment points.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "topic": "<lesson topic>",
  "grade_level": "<as provided>",
  "objectives": ["<from provided objectives>"],
  "standards_alignment": ["<provided standard, or 'confirm with your standards — not fabricated'>"],
  "lesson_flow": [ { "segment": "<opening|activity|practice|assessment|close>", "time": "<min>", "detail": "<what happens>" } ],
  "materials": ["<needed materials>"],
  "assessment": "<how learning is checked, aligned to objectives>",
  "assumptions": ["<assumptions made>"],
  "teacher_judgment": ["<decisions/areas for the teacher>"],
  "note": "First-draft lesson plan to adapt. No standards or facts were fabricated; a teacher should review."
}
Never fabricate a standard code or a fact. Keep it age-appropriate. Flag teacher-judgment points.
"""

SAMPLE_INPUT = """Objectives: 'Students can identify the parts of a plant and explain photosynthesis at a basic level.' Grade 5, 45 minutes.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_objectives": "Take the learning objectives and grade level for the lesson.",
    "align_standards_or_tbd": "Align to provided standards or mark alignment to confirm, never fabricating codes.",
    "structure_lesson": "Build the lesson flow around the objectives and grade level.",
    "generate_activities": "Create age-appropriate activities aligned to the objectives.",
    "generate_assessment": "Design an assessment that checks the stated objectives.",
    "age_appropriate_check": "Ensure content and activities suit the grade and are safe and inclusive.",
    "flag_teacher_input": "Mark assumptions and decisions needing the teacher's judgment.",
    "accuracy_check": "Keep instructional content accurate and flag uncertain facts to verify.",
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
    print("Lesson Plan Generation Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
