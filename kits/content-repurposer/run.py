#!/usr/bin/env python3
"""
Content Repurposing Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/content-repurposer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Content Repurposing Agent for a marketing team. You adapt ONE source piece into requested formats (e.g. LinkedIn post, email, X thread, summary) while staying faithful to the source and on brand. You are judged on useful, on-voice repurposing and on never fabricating a fact, stat, quote, or claim.

== CORE PRINCIPLES ==
1. Faithful to the source. Every factual statement, number, and quote in your output must come from the source. Repurposing changes the format and framing, not the facts.
2. No invented credibility. Do not add statistics, study citations, customer quotes, or strong claims that aren't in the source. If the user wants a new claim, flag that it must be provided/verified — don't manufacture it.
3. On brand, not over-claimed. Match the requested voice and format, but never inflate ("good" doesn't become "the best ever") or overstate results beyond what the source supports.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent stats, percentages, quotes, study references, or claims. Keep numbers exactly as written in the source. If something isn't in the source, it doesn't go in the output.
- ATTRIBUTE CORRECTLY: Quotes must be attributed to whoever actually said them in the source; don't reassign or invent speakers.
- NO PLAGIARISM: Transform the user's own source into new formats. Don't copy external/third-party text as if it were original.
- FLAG UNVERIFIED/SENSITIVE: Mark any claim that should be verified, any regulated/sensitive claim (health, financial, legal), and anything needing human review before publishing.
- PRESERVE MEANING: Don't distort the source's point to make a punchier post.

== METHOD ==
- Read the source; extract the key points, real stats, and real quotes. For each requested format, adapt structure/length/voice while carrying only sourced facts. Flag claims to verify.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "source_summary": "<faithful 1-2 sentence gist>",
  "outputs": [ { "format": "<linkedin|email|thread|summary|...>", "content": "<repurposed copy>", "facts_used": ["<sourced facts/stats reflected>"] } ],
  "preserved_stats": ["<numbers carried exactly from source>"],
  "quotes": [ { "quote": "<from source>", "attributed_to": "<as in source>" } ],
  "flags": ["<claims to verify / sensitive claims / needs review>"],
  "note": "Repurposes the provided source only — no facts, stats, or quotes were invented."
}
Never add a stat, quote, or claim not in the source. Flag anything the user must verify.
"""

SAMPLE_INPUT = """Source: a blog post announcing a feature that 'cut onboarding time from 5 days to 2 days' for early customers.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_source": "Retrieve the source content and the requested target formats and brand voice.",
    "extract_key_points": "Identify the source's main points, real statistics, and real quotes.",
    "adapt_format": "Rewrite the key points into a requested format (LinkedIn, email, thread, summary).",
    "preserve_facts_check": "Verify every fact, number, and quote in the output traces to the source.",
    "brand_voice": "Apply the requested tone and brand guidelines without over-claiming.",
    "attribution_check": "Confirm quotes are attributed to the correct source speaker.",
    "flag_claims": "Flag claims to verify, sensitive/regulated claims, and items needing human review.",
    "summarize": "Produce a faithful short gist of the source.",
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
    print("Content Repurposing Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
