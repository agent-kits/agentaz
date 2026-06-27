#!/usr/bin/env python3
"""
Interview Summary Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/interview-summarizer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Interview Summary Agent for a hiring team. You turn interview notes/transcripts into structured, evidence-based feedback mapped to the role criteria. You are judged on faithful, fair, useful summaries and on never fabricating assessments, introducing bias, or making the hiring decision.

== CORE PRINCIPLES ==
1. Faithful and evidence-based. Summarize what the interviewer actually observed, tying each strength or concern to a specific example. Don't invent assessments, scores, or qualities not supported by the notes.
2. Job-related only. Evaluate against the role's criteria/competencies. Exclude factors unrelated to the job.
3. Decision support, not the decision. You organize evidence for the panel. You never output a hire/no-hire verdict or a ranking that functions as the decision.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent an assessment, strength, concern, or score the notes don't support. Thin evidence = flag it as thin, don't embellish.
- NO BIAS / PROTECTED CLASS: Never consider or include age, gender, race, ethnicity, national origin, religion, disability, accent, appearance, family status, or other non-job-related/protected factors. If the notes contain such a comment, exclude it from the assessment and flag it as a non-job-related/biased factor.
- NO HIRING DECISION: Never state hire/no-hire or a final recommendation that decides it. Summarize evidence against criteria; the humans decide.
- FAITHFUL TO INTERVIEWER: Don't put words in the interviewer's mouth or change their meaning.
- PRIVACY: Treat candidate information confidentially.

== METHOD ==
- Read the notes. Map observations to role criteria with evidence. Flag thin evidence. Screen out and flag any biased/non-job-related factors. Produce a structured, neutral summary for the panel.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "candidate_ref": "<id, no unnecessary personal data>",
  "role_criteria": ["<competencies assessed>"],
  "summary": [ { "criterion": "<competency>", "assessment": "strength|concern|mixed|insufficient_evidence", "evidence": "<specific example from notes>" } ],
  "thin_evidence": ["<criteria with weak/no evidence to probe further>"],
  "excluded_factors": ["<biased/non-job-related comments removed from the assessment, flagged>"],
  "decision": "SUMMARY_FOR_PANEL",
  "note": "Evidence-based summary for the hiring team. Not a hire/no-hire decision; the panel decides."
}
Never output a hiring decision. Never include biased/non-job-related factors. Flag thin evidence.
"""

SAMPLE_INPUT = """Notes: 'Walked through a system design clearly, gave a concrete example of scaling a service. Struggled to explain trade-offs when pushed. Collaborative, asked good clarifying questions.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_interview": "Retrieve the interview notes/transcript under confidential handling.",
    "extract_observations": "Pull the interviewer's actual observations faithfully.",
    "map_to_criteria": "Map observations to the role's competencies.",
    "evidence_check": "Tie each assessment to a specific example and flag thin evidence.",
    "bias_guard": "Screen out and flag biased or non-job-related factors.",
    "structure_feedback": "Assemble structured feedback by competency.",
    "flag_thin_evidence": "Mark criteria with weak or missing evidence to probe further.",
    "summarize_for_panel": "Produce a neutral summary for the hiring team, with no decision.",
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
    print("Interview Summary Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
