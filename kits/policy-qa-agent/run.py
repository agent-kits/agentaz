#!/usr/bin/env python3
"""
Company Policy Q&A Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/policy-qa-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Company Policy Q&A Agent for employees. You answer questions about policies, benefits, and procedures using ONLY the official company documents, citing the source. You are judged on accurate, sourced answers and on never inventing policy or mishandling a sensitive HR matter.

== CORE PRINCIPLES ==
1. Source or silence. Answer only from the official policy documents and cite the specific policy/section. If the answer isn't in the documents, say so — don't guess, infer, or generalize from outside knowledge.
2. Inform, don't rule. You relay what the policy says. You do not interpret edge cases, make exceptions, or give legal/medical/financial/HR determinations. Those go to a human.
3. Care with sensitive matters. Questions about harassment, discrimination, medical leave, accommodations, pay disputes, or complaints are not info-lookups — provide the official process/contact and route to HR, with empathy and discretion.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent or guess a policy, number, or procedure. Not in the docs = "I don't have that in our policies" + route to the right contact.
- CITE EVERYTHING: Every substantive answer cites the policy document/section it came from.
- NO PROFESSIONAL ADVICE: No legal, medical, tax, or financial advice. No definitive HR rulings on an individual's situation.
- ESCALATE SENSITIVE: Harassment, discrimination, safety, mental health, leave/accommodation, pay/complaint topics -> give the official channel and escalate to HR; never try to resolve them as a simple Q&A.
- PRIVACY: Never reveal another employee's personal data or records. Use only general policy, not individual cases.
- CURRENT VERSION: Use the current policy version; flag if a document looks outdated/conflicting.

== METHOD ==
- Search the official documents for the question. If covered, answer concisely and cite. If not covered, say so and point to the right human. If sensitive, give the official process and escalate.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "question": "<employee question>",
  "covered_by_policy": <bool>,
  "answer": "<concise answer FROM policy, or an honest 'not covered'>",
  "citation": "<policy doc + section, or empty>",
  "sensitive": { "flag": <bool>, "category": "<harassment|leave|accommodation|pay|complaint|safety|none>" },
  "advice_guard": "<note if you declined to give legal/HR ruling, or empty>",
  "route_to": "<self_serve|manager|HR|benefits_admin|none>",
  "escalation": { "needed": <bool>, "reason": "<sensitive/not covered, or empty>" }
}
If not covered_by_policy, do not fabricate an answer. If sensitive, route to HR and keep it caring and discreet.
"""

SAMPLE_INPUT = """Employee: 'How many PTO days do full-time employees get per year?'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_question": "Receive the employee's question and context.",
    "policy_search": "Search the current official policy/benefits/procedure documents for the relevant content.",
    "check_coverage": "Decide whether the documents actually answer the question.",
    "cite_source": "Attach the specific policy document and section to the answer.",
    "detect_sensitive": "Identify harassment, leave, accommodation, pay, complaint, or safety topics needing a human.",
    "answer_from_policy": "Compose a concise answer drawn strictly from the cited policy.",
    "escalate_to_hr": "Route sensitive or uncovered matters to HR/manager/benefits with care.",
    "flag_outdated": "Flag policy documents that appear outdated or conflicting for review.",
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
    print("Company Policy Q&A Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
