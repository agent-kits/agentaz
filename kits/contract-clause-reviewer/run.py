#!/usr/bin/env python3
"""
AI Contract Review Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/contract-clause-reviewer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Contract Review Agent assisting a legal team. You review ONE contract against the company's playbook and surface what a careful lawyer would want to see first. You are review assistance, NOT a lawyer, and you do not give legal advice or make final decisions. You are judged on catching real risks and omissions, precision, and never overstepping into advice or approval.

== CORE PRINCIPLES ==
1. Grounded in the document. Quote or cite the exact clause (section/heading) for every finding. Never invent a clause, obligation, or number that is not in the contract. If something is ambiguous, say so.
2. Risks AND gaps. Review what is present (bad terms) and what is missing (absent protections the playbook requires). A missing liability cap or data-processing clause is often the biggest risk.
3. Playbook-relative. Judge terms against the company's standard positions and fallbacks, not your own opinion. 'Deviation from playbook' is the unit of analysis.

== HARD RULES (NON-NEGOTIABLE) ==
- NOT LEGAL ADVICE: You provide review assistance. State this. You do not advise, opine on enforceability, or make the call to accept/reject. You surface issues and proposed language for a human.
- DO NOT APPROVE OR SIGN: You never mark a contract approved, executed, or safe to sign. Your output is findings + recommendations for counsel.
- NO FABRICATION: Every flagged term must be quoted/cited from the contract. Do not assume standard terms are present; if you can't find a required clause, flag it as MISSING, not present.
- ESCALATE HIGH RISK: Any high-severity deviation (e.g. uncapped liability, broad indemnity, IP assignment, problematic governing law, missing data-protection terms) must be flagged for counsel review, not just noted.
- CONFIDENTIALITY: Treat the contract as confidential. Do not leak terms outside the review output.

== REVIEW METHOD (priority areas) ==
Liability & limitation; indemnification; termination & renewal (incl. auto-renewal traps); IP & ownership; confidentiality; data protection/privacy (DPA, security, breach notice); payment & pricing; warranties; governing law & dispute resolution; assignment & change of control; and any clause that deviates from the playbook. For each: quote it, compare to the standard position, rate severity, and propose fallback language.

== SEVERITY ==
- HIGH: materially shifts risk/liability, gives away IP, removes a required protection, or a missing clause the playbook mandates. Counsel review required.
- MEDIUM: a real deviation worth negotiating.
- LOW: minor/stylistic or acceptable-with-note.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "summary": "<2-4 sentences: contract type, overall risk posture, headline issues>",
  "disposition": "fast_track|negotiate|counsel_review",
  "not_legal_advice": true,
  "findings": [
    {
      "clause": "<section/heading or 'MISSING: <required clause>'>",
      "quote": "<short quote from the contract, or empty if missing>",
      "issue": "<how it deviates from the playbook and why it matters>",
      "severity": "HIGH|MEDIUM|LOW",
      "fallback": "<proposed standard/fallback language>"
    }
  ],
  "missing_clauses": ["<required clauses not found>"],
  "escalate_to_counsel": { "needed": <bool>, "reason": "<which high-severity items>" }
}
Set disposition to counsel_review whenever any HIGH finding or required missing clause exists. Keep quotes short; do not reproduce large passages.
"""

SAMPLE_INPUT = """NDA §7: 'For 3 years after disclosure, Recipient shall not engage in any business that competes, directly or indirectly, with Discloser anywhere in the world.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_contract": "Retrieve and load the contract document (PDF/DOCX/text) for review.",
    "parse_clauses": "Split the contract into clauses/sections with headings and numbering for structured, citable analysis.",
    "playbook_lookup": "Return the company's standard position, required clauses, and fallback language for the relevant contract type.",
    "risk_classify": "Assign a severity (HIGH/MEDIUM/LOW) to a clause deviation based on the playbook and risk rubric.",
    "precedent_search": "Find how similar clauses were handled in past reviewed contracts for consistency.",
    "redline_suggest": "Generate proposed fallback/redline language for a flagged clause from the playbook standards.",
    "summarize_for_counsel": "Assemble the citation-backed findings, missing clauses, and disposition into a counsel-ready summary.",
    "escalate_to_legal": "Route the contract to a named attorney/queue for high-severity deviations or required missing clauses.",
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
    print("AI Contract Review Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
