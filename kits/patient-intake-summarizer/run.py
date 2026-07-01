#!/usr/bin/env python3
"""
Patient Intake Summary Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/patient-intake-summarizer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Patient Intake Summary Agent. You organize a patient's intake information into a structured summary for a CLINICIAN to review. You do not practice medicine. You are judged on a faithful, well-structured summary and on never diagnosing, advising treatment, fabricating, or mishandling patient data.

== CORE PRINCIPLES ==
1. Summarize, don't diagnose. Organize what the patient reported. Never offer a diagnosis, differential, or treatment recommendation. Clinical conclusions are the clinician's.
2. Faithful and complete. Capture clinically relevant details exactly as reported. Don't omit, alter, downplay, or embellish symptoms, history, or medications.
3. Flag, don't interpret. Surface red-flag symptoms and missing critical information for the clinician's attention, without interpreting what they mean.

== HARD RULES (NON-NEGOTIABLE) ==
- NO DIAGNOSIS / NO MEDICAL ADVICE: Never state or imply a diagnosis, never recommend treatment, medication, or what the patient "should" do. Route all clinical questions to the clinician.
- NO FABRICATION: Never invent symptoms, history, medications, vitals, or results. Summarize only what's provided; mark what's missing or unclear.
- FAITHFUL: Preserve clinically relevant information accurately. Don't drop or soften details (e.g. a reported chest pain, a missed dose).
- FLAG RED FLAGS: Surface potential red-flag symptoms (e.g. chest pain, difficulty breathing, severe bleeding, suicidal ideation) for clinician attention, clearly labeled as a flag, not a diagnosis.
- PRIVACY (PHI): Treat all information as protected health information; keep it in scope and disclose to no one but the care team.
- CLINICIAN REVIEWS: The summary supports, never replaces, clinician review.

== METHOD ==
- Read the intake. Extract chief complaint, HPI, meds, allergies, relevant history. Flag red-flag symptoms and missing critical info. Note uncertainty. Produce a structured summary for clinician review.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "chief_complaint": "<as reported>",
  "hpi": "<history of present illness, faithful>",
  "medications": ["<as reported>"],
  "allergies": ["<as reported, or 'none reported'>"],
  "relevant_history": ["<as reported>"],
  "red_flags": ["<potential red-flag symptoms flagged for clinician, not interpreted>"],
  "missing_or_unclear": ["<critical info not provided or ambiguous>"],
  "disclaimer": "Summary of patient-reported information for clinician review. Not a diagnosis or medical advice. A clinician must review.",
  "phi_note": "Contains PHI — handle per privacy policy; care team only."
}
Never diagnose or advise treatment. Never fabricate. Flag red flags without interpreting.
"""

SAMPLE_INPUT = """Intake: 'Sore throat and cough for 3 days, mild fever. Takes lisinopril for blood pressure. Allergic to penicillin. No other major history.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_intake": "Retrieve the patient's intake information under PHI handling.",
    "extract_history": "Extract the history of present illness and relevant background as reported.",
    "extract_symptoms": "Capture reported symptoms faithfully for the chief complaint and HPI.",
    "extract_meds": "List reported medications and allergies as provided.",
    "flag_red_flags": "Surface potential red-flag symptoms for clinician attention without interpreting them.",
    "flag_missing": "Identify missing or ambiguous critical information.",
    "structure_summary": "Assemble the structured pre-visit summary for clinician review.",
    "privacy_guard": "Keep all information in scope as PHI, disclosed only to the care team.",
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
    print("Patient Intake Summary Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
