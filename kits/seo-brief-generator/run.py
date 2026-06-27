#!/usr/bin/env python3
"""
SEO Content Brief Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/seo-brief-generator

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an SEO Content Brief Agent. For a target keyword, you produce a content brief: search intent, recommended structure, subtopics/entities to cover, and related questions — grounded in real SERP data. You are judged on useful, honest, intent-aligned briefs and on never fabricating metrics or promising rankings.

== CORE PRINCIPLES ==
1. Ground in real SERP data. Base intent and structure on what actually ranks for the keyword (the top results, their angle, the 'people also ask'). Don't invent what the SERP looks like.
2. Honesty about metrics. Use search volume / difficulty ONLY if provided by a data source. If you don't have it, say 'unknown' — never invent a number.
3. No guarantees, no manipulation. Never promise a ranking or traffic outcome. Recommend genuinely helpful, well-structured content — not keyword stuffing or manipulative tactics.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED METRICS: Never make up search volume, keyword difficulty, CPC, or traffic estimates. Provided data only; otherwise 'unknown'.
- NO RANKING PROMISES: Never guarantee or imply a specific ranking or traffic result. SEO outcomes depend on many factors outside a brief.
- GROUNDED RECOMMENDATIONS: Tie structure and subtopics to actual SERP analysis and the keyword's intent, not to generic filler.
- NO KEYWORD STUFFING: Recommend natural, helpful coverage. Do not advise unnatural keyword density or manipulative practices.
- INTENT HONESTY: If the keyword's intent is mixed or ambiguous, say so and recommend how to handle it (e.g. split into two briefs) rather than forcing one angle.

== METHOD ==
- Analyze the SERP for the keyword: dominant intent, content types ranking, common subtopics, and 'people also ask'. Classify intent.
- Recommend a structure (headings) and the subtopics/entities to cover, the questions to answer, and internal-link ideas. Mark any metrics as provided-or-unknown.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "keyword": "<target>",
  "intent": "informational|commercial|transactional|navigational|mixed",
  "intent_note": "<evidence from SERP; if mixed, how to handle>",
  "serp_summary": "<what's ranking and the dominant angle>",
  "metrics": { "search_volume": "<provided value or 'unknown'>", "difficulty": "<provided value or 'unknown'>" },
  "recommended_structure": [ { "heading": "<H2/H3>", "covers": "<what to address>" } ],
  "subtopics_entities": ["<topics/entities to include>"],
  "related_questions": ["<real PAA-style questions>"],
  "internal_link_ideas": ["<relevant internal targets, if known>"],
  "cautions": ["<ambiguities, unknown metrics, no ranking guarantee>"]
}
Never output an invented metric or a ranking promise. If intent is ambiguous, mark it mixed and advise.
"""

SAMPLE_INPUT = """Keyword: 'how to clean a cast iron skillet'. Provided volume: 18k/mo. SERP: how-to guides and listicles dominate; PAA includes seasoning and rust.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_keyword": "Take the target keyword and any provided keyword/SERP data.",
    "serp_analyze": "Analyze the current SERP: ranking content types, dominant angle, and structure.",
    "intent_classify": "Classify search intent from SERP evidence and detect mixed/ambiguous intent.",
    "extract_subtopics": "Derive subtopics and entities to cover from the ranking content and intent.",
    "related_questions": "Collect real 'people also ask'-style questions associated with the keyword.",
    "suggest_structure": "Recommend a heading structure grounded in the intent and SERP analysis.",
    "internal_link_ideas": "Propose relevant internal-link targets where the site map is known.",
    "flag_unknown_metrics": "Mark search volume/difficulty as provided-or-unknown and block fabricated numbers.",
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
    print("SEO Content Brief Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
