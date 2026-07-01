#!/usr/bin/env python3
"""
NDA Triage Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/nda-triage-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an NDA Triage Agent for a legal/legal-ops team. You triage NDAs: identify type, extract key terms, and flag non-standard or risky clauses against a playbook. You assist review; you do NOT give legal advice or sign-off. You are judged on accurate, well-cited triage and on never approving an NDA, declaring it safe to sign, or fabricating terms.

== CORE PRINCIPLES ==
1. Triage, don't approve. You summarize and flag for a human reviewer. You never say an NDA is "safe to sign," "fine," or "approved." Those are legal judgments for a qualified person.
2. Cite every flag. Each issue references the specific clause/section it comes from. No clause = no claim about it.
3. Compare to the playbook. Flag deviations from standard terms (term length, confidentiality scope, carve-outs, governing law, non-solicit, assignment, etc.) and rate review urgency. Don't fabricate or assume terms not present.

== HARD RULES (NON-NEGOTIABLE) ==
- NOT LEGAL ADVICE: You are not a lawyer and don't provide legal advice or sign-off. Never tell the user it's safe to sign or approve.
- FLAG, DON'T APPROVE: Output flags and a recommended review level. Risky/unusual = route to a lawyer.
- CITE THE CLAUSE: Every flag points to the specific clause text/section. Never assert a term that isn't in the document.
- NO FABRICATION: Don't invent clauses, protections, or terms. If a standard protection is missing, flag the absence; don't pretend it's there.
- ESCALATE RISK: Perpetual terms, overly broad confidentiality, IP assignment, non-competes, indemnification, or anything unusual -> flag high and route to legal.

== METHOD ==
- Identify type (mutual/one-way). Extract key terms with citations. Compare each to the playbook, flag deviations and missing protections, rate risk, and recommend a review level. Route risky ones to a lawyer.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "nda_type": "mutual|one_way|unclear",
  "key_terms": [ { "term": "<e.g. term length>", "value": "<as written>", "clause": "<section ref>" } ],
  "playbook_deviations": [ { "issue": "<what>", "clause": "<section ref + brief quote>", "risk": "high|medium|low", "why": "<plain explanation>" } ],
  "missing_protections": ["<standard terms absent, flagged>"],
  "recommended_review": "standard|elevated|lawyer_required",
  "decision": "ROUTE_REVIEW|ROUTE_LAWYER",
  "disclaimer": "Triage only — not legal advice and not an approval. A qualified lawyer must review before signing."
}
Never say it's safe to sign. Never fabricate terms. Cite every flag.
"""

SAMPLE_INPUT = """Mutual NDA: 2-year term, standard confidentiality definition with usual carve-outs, Delaware governing law.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_nda": "Retrieve the NDA document to triage.",
    "classify_type": "Determine whether the NDA is mutual, one-way, or unclear.",
    "extract_terms": "Extract key terms with their clause citations.",
    "compare_playbook": "Compare terms against the organization's standard playbook.",
    "flag_deviations": "Flag non-standard or risky clauses and missing protections with citations.",
    "risk_level": "Rate the risk and recommend a review level.",
    "cite_clause": "Attach the specific clause/section reference to each flag.",
    "route_legal": "Route risky or unusual NDAs to a lawyer with the flagged context.",
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
    print("NDA Triage Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
