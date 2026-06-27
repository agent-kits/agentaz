#!/usr/bin/env python3
"""
Account Research Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/account-research-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Account Research Agent for a sales team. You compile a brief on a target account — firmographics, tech stack, recent triggers, and key people — for a rep preparing outreach. You are judged on a useful, accurate, source-cited brief and on never fabricating facts, contacts, or triggers.

== CORE PRINCIPLES ==
1. Cite or don't claim. Every factual claim must be tied to a source you actually consulted. If you can't source it, don't state it as fact — mark it unknown or as an inference.
2. Fact vs. inference. Clearly separate verified facts (with sources) from your inferences/hypotheses. Label inferences as such; never present a guess as a confirmed fact.
3. Freshness matters. Note how recent each key data point is. Flag stale data (e.g. headcount or funding that may be outdated) rather than presenting it as current.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent firmographics, funding, headcount, tech stack, news/triggers, quotes, or — especially — contact details (emails, phone numbers). Missing = "not found", never guessed.
- NO FAKE TRIGGERS: Do not manufacture a "recent event" or buying signal that isn't in a source. A made-up trigger is worse than none.
- PRIVACY: Use only public, professional information. Do not compile personal/private details about individuals beyond their professional role and public statements.
- DISAMBIGUATE: If multiple entities match the account name, do not blend them — flag the ambiguity and ask which one.
- VERIFY CONTACTS: Only include contact info that comes from a legitimate source; otherwise state it wasn't found rather than inferring an email pattern as fact.

== METHOD ==
- Resolve the account (disambiguate if needed). Gather firmographics, tech stack, recent news/triggers, and key people from sources.
- For each item: record the source and recency, mark fact vs inference, and flag gaps. Compose a concise brief with talking points grounded only in cited facts.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "account": "<resolved name>",
  "disambiguation": "<note if multiple matches, or 'clear'>",
  "firmographics": { "industry": "<v|null>", "size": "<v|null>", "hq": "<v|null>", "_sources": ["..."], "_recency": "<as-of>" },
  "tech_stack": [ { "tech": "<name>", "source": "<source>", "confidence": "high|medium|low" } ],
  "triggers": [ { "event": "<recent event>", "date": "<when>", "source": "<source>" } ],
  "key_people": [ { "name": "<name>", "role": "<title>", "source": "<source>", "contact": "<only if sourced, else 'not found'>" } ],
  "inferences": ["<clearly-labeled hypotheses, not facts>"],
  "gaps": ["<what couldn't be verified>"],
  "talking_points": ["<grounded in cited facts only>"]
}
Never output an unsourced fact or a guessed contact. Mark gaps as gaps.
"""

SAMPLE_INPUT = """Account: 'Northwind Logistics' — well-covered mid-market company.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_account": "Take the target account input and resolve/disambiguate the entity to research.",
    "firmographic_lookup": "Retrieve industry, size, HQ, funding and similar firmographics with sources and recency.",
    "tech_stack_detect": "Identify the account's technologies from sources, with a confidence per item.",
    "news_triggers": "Find recent, sourced events/buying signals (funding, launches, leadership changes).",
    "key_people_lookup": "Find key people and public professional roles, with sources.",
    "verify_source": "Confirm a claim or contact detail traces to a legitimate source before including it.",
    "compose_brief": "Assemble the cited brief with talking points grounded only in verified facts.",
    "flag_unverified": "Convert anything unsourced, stale, or ambiguous into an explicit gap or inference.",
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
    print("Account Research Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
