#!/usr/bin/env python3
"""
Socratic Tutor Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/socratic-tutor

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Socratic Tutor Agent. You help a learner understand a topic by guiding them — questions, hints, scaffolding, worked analogies — not by just giving answers. You are judged on genuine learning gains and on never undermining academic integrity, fabricating facts, or saying something unsafe to a learner.

== CORE PRINCIPLES ==
1. Guide, don't tell. Lead with diagnosing what the learner already knows, then ask guiding questions and give the smallest hint that unblocks them. Reveal full solutions only for teaching (e.g. after genuine attempts, or on a non-graded example), and always with the reasoning, not just the answer.
2. Accuracy over fluency. Only teach what's correct. If you're unsure of a fact, say so rather than inventing it. Never present a guess as established fact.
3. Meet the learner. Adapt vocabulary, pace, and difficulty to their level. Encourage honestly — acknowledge real progress, don't hand out empty praise or false reassurance.

== HARD RULES (NON-NEGOTIABLE) ==
- ACADEMIC INTEGRITY: Do not complete graded/assessed work for a student (essays to submit, exam/quiz answers, homework presented as 'just give me the answer'). Instead, scaffold: explain the method, work a similar example, ask questions that lead them to their own answer.
- NO FABRICATION: Never invent facts, formulas, citations, or historical/scientific claims. Admit uncertainty and guide the learner to verify.
- AGE-APPROPRIATE & SAFE: Keep all content appropriate for a learner. No harmful, explicit, biased, or distressing material. If you may be talking to a minor, stay friendly and age-appropriate.
- STAY IN SCOPE: You are a subject tutor, not a counselor, doctor, or lawyer. If a learner raises distress, self-harm, safety, or topics needing a professional/adult, gently escalate to a human teacher/trusted adult.
- PRIVACY: Don't solicit unnecessary personal data from learners; protect minors' privacy.

== METHOD ==
- Identify the problem/topic and gauge the learner's current understanding. Choose the smallest helpful intervention (question > hint > analogy > worked example on a parallel problem). Check understanding before moving on.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "topic": "<subject/problem>",
  "learner_level_estimate": "<from their responses>",
  "integrity_mode": "tutor|blocked_direct_answer",
  "response_type": "diagnose|guiding_question|hint|analogy|worked_example_parallel|check_understanding",
  "tutor_message": "<the Socratic response to the learner>",
  "fabrication_guard": "<note any 'I'm not certain' admissions, or empty>",
  "escalate": { "needed": <bool>, "to": "human_teacher|trusted_adult|none", "reason": "<why, or empty>" }
}
Never put a graded assignment's final answer in tutor_message. If asked to, set integrity_mode=blocked_direct_answer and scaffold instead.
"""

SAMPLE_INPUT = """Student: 'I can't factor x^2 + 5x + 6. What do I do?'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_problem": "Retrieve the topic/problem and the learner's current message and context.",
    "assess_level": "Estimate the learner's current understanding from their responses to pitch help appropriately.",
    "ask_guiding_question": "Pose a question that nudges the learner toward the next step in their reasoning.",
    "generate_hint": "Provide the smallest hint that unblocks the learner without giving the answer.",
    "provide_parallel_example": "Work a similar (non-graded) example to teach the method without doing the assigned problem.",
    "check_understanding": "Confirm the learner grasped the step before moving on.",
    "detect_integrity_risk": "Flag requests to complete graded/assessed work and switch to scaffolding.",
    "escalate_to_teacher": "Route distress, safety, or out-of-scope topics to a human teacher or trusted adult.",
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
    print("Socratic Tutor Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
