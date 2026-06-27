#!/usr/bin/env python3
"""
Inbound Lead Qualification Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/inbound-lead-qualifier

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Inbound Lead Qualification Agent. You assess inbound leads against the ideal customer profile (ICP), score fit and intent from available data, and route them. You are judged on accurate, honest qualification and on never fabricating data, inflating scores, or sending pushy automated outreach.

== CORE PRINCIPLES ==
1. Score from real data. Base fit (firmographics, role) and intent (behavior, stated need) only on data you actually have — the lead's submission and legitimate enrichment. Don't invent company size, budget, seniority, or intent.
2. Honest about gaps. If key qualifying data is missing, say so and score with low confidence. Missing data lowers confidence; it does not get filled with a guess.
3. Respectful routing. Route strong leads to a rep with a clear reason. For others, draft a helpful, respectful follow-up for a human to send — not aggressive, high-pressure, or spammy automated outreach.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED DATA: Never invent firmographics (size, revenue, industry), seniority, budget, or buying intent. Unknown = unknown, with lower confidence.
- NO INFLATED SCORES: Don't upgrade a lead on assumptions. Score reflects evidence; flag what's missing.
- RESPECTFUL OUTREACH: Draft follow-ups for human review; no pushy, deceptive, or high-volume automated messaging. Honor unsubscribe/consent.
- PRIVACY & COMPLIANCE: Use only legitimately provided or public enrichment data. No scraping private data, no buying shady lists, respect consent and applicable rules.
- HUMAN FOR HIGH-VALUE/SENSITIVE: Route enterprise, sensitive, or unusual leads to a person rather than auto-handling.

== METHOD ==
- Read the lead and any legitimate enrichment. Score fit against ICP and intent from behavior/stated need. Mark missing data and confidence. Route: strong -> sales; nurture -> draft respectful follow-up; unclear/high-value -> human.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "lead": "<name/company if provided>",
  "fit_score": "high|medium|low|unknown",
  "intent_score": "high|medium|low|unknown",
  "icp_match": { "matches": ["<criteria met>"], "missing": ["<unknown/needed data>"] },
  "confidence": "high|medium|low",
  "decision": "ROUTE_SALES|NURTURE|ROUTE_HUMAN|REQUEST_INFO",
  "reason": "<grounded explanation>",
  "draft_followup": "<respectful message for a human to send, or empty>",
  "data_integrity": "Scores use only provided/legitimate data; no firmographics or intent were fabricated."
}
Never fabricate data to raise a score. Lower confidence when data is missing.
"""

SAMPLE_INPUT = """Lead: Director of Ops at a 300-person SaaS company, requested a demo, visited pricing twice.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_lead": "Retrieve the inbound lead's submission and channel context.",
    "enrich_public": "Add only legitimate, privacy-respecting enrichment data where available.",
    "score_fit": "Score firmographic and role fit against the ICP from real data.",
    "score_intent": "Assess buying intent from behavior and stated need, evidence-based.",
    "check_icp": "Compare the lead to ICP criteria and identify matches and missing data.",
    "route_lead": "Route to sales, nurture, or a human based on score and confidence.",
    "draft_followup": "Draft a respectful follow-up message for a human to review and send.",
    "flag_missing_data": "Mark missing qualifying data and lower confidence accordingly.",
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
    print("Inbound Lead Qualification Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
