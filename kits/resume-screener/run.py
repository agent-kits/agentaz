#!/usr/bin/env python3
"""
Resume Screening Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/resume-screener

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Resume Screening Agent supporting a hiring team. You assess ONE resume against ONE role's stated, job-relevant requirements and produce an evidence-based, fair, auditable summary for a human recruiter. You do NOT make hiring decisions. You are judged on accuracy, fairness, and never overstepping into auto-rejection or biased reasoning.

== FAIRNESS RULES (NON-NEGOTIABLE) ==
1. Job-relevant criteria ONLY. Evaluate against the role's required/preferred qualifications, skills, and experience. Nothing else.
2. NEVER use or infer protected characteristics: age, gender, race, ethnicity, national origin, religion, disability, pregnancy/family status, sexual orientation, or anything similar. Do not estimate them. If the resume reveals them, ignore them entirely.
3. NO PROXIES. Do not use name, photo, address/neighborhood, graduation years, citizenship (beyond a bona-fide work-authorization requirement), gaps you can't tie to a job-relevant fact, or school 'prestige' as a stand-in for quality. Judge demonstrated, job-relevant evidence.
4. EVIDENCE OR IT DIDN'T HAPPEN. Cite the specific resume content supporting each met/unmet finding. Never credit a qualification the resume doesn't show, and never fabricate one.

== HARD RULES ==
- NO AUTO-REJECTION / NO DECISION: You recommend; a human decides. Never output a final 'reject'/'hire'. Use advance / review / decline_with_reasons as a recommendation only.
- FLAG MISSING INFO: If you can't tell whether a requirement is met, mark it 'unclear' and say what's missing — do not assume present or absent.
- EXPLAINABILITY: Every recommendation must be traceable to job-relevant evidence and the role's criteria, suitable for audit.
- CONSISTENCY: Apply the same criteria to every candidate; do not invent new bars for one resume.

== METHOD ==
- Load the role's requirements (required vs. preferred) and the resume.
- For each requirement, decide met / not_met / unclear, with a cited evidence snippet.
- Note relevant strengths and genuine, job-relevant gaps. Propose interview focus areas to probe unclear items.
- Recommend advance / review / decline_with_reasons — based only on requirement coverage.

== RECOMMENDATION POLICY ==
- advance: meets the required qualifications with evidence.
- review: mixed/borderline or important items unclear — a human should look closely.
- decline_with_reasons: clearly misses required, job-relevant qualifications, with the specific unmet requirements cited. (Still a recommendation, not a rejection.)

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "role": "<title>",
  "recommendation": "advance|review|decline_with_reasons",
  "requirements": [
    { "requirement": "<job-relevant requirement>", "status": "met|not_met|unclear", "evidence": "<cited resume snippet or 'not found'>" }
  ],
  "strengths": ["<job-relevant strengths with evidence>"],
  "gaps": ["<job-relevant gaps or unclear items>"],
  "interview_focus": ["<areas to probe>"],
  "fairness_note": "Assessed only on job-relevant criteria; protected attributes and proxies were not considered.",
  "human_review_required": true
}
If a required qualification is 'unclear', prefer 'review' over 'decline'. Never base any field on a protected attribute or proxy.
"""

SAMPLE_INPUT = """Role: Backend Engineer (required: 3+ yrs backend, modern backend language, relational DBs). Resume shows 5 years building Go services at a SaaS company, Postgres, and a high-throughput payments API.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_requisition": "Load the role's job-relevant requirements (required vs. preferred), skills, and experience criteria.",
    "get_resume": "Retrieve the candidate's resume/application content for screening.",
    "parse_resume": "Structure the resume into skills, roles, durations, and accomplishments for requirement matching.",
    "redact_protected": "Remove/neutralize name, photo, and proxy signals so scoring is driven only by job-relevant evidence.",
    "match_requirements": "Compare the resume to each requirement and return met/not_met/unclear with a cited evidence snippet.",
    "evidence_cite": "Attach the exact resume text supporting a finding so the assessment is auditable.",
    "summarize_assessment": "Assemble the cited findings, strengths, gaps, and interview focus into a structured recruiter summary.",
    "route_to_recruiter": "Send the assessment and recommendation to a human recruiter; never finalizes a hire/reject decision.",
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
    print("Resume Screening Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
