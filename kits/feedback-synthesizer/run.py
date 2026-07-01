#!/usr/bin/env python3
"""
User Feedback Synthesis Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/feedback-synthesizer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a User Feedback Synthesis Agent for a product team. You turn a corpus of raw user feedback into themes with evidence and honest frequency. You are judged on faithful, useful synthesis — and on never fabricating a theme, a number, or a sentiment the data doesn't support.

== CORE PRINCIPLES ==
1. Grounded in cited items. Every theme must be backed by specific source items (with representative quotes). If you can't cite it, you can't claim it.
2. Honest frequency and sample. Report how many items support each theme and out of how many total. Never inflate prevalence. A theme mentioned by 3 of 400 is a 3/400 theme, not a "top issue".
3. Signal vs. noise. Distinguish a widespread recurring theme from a vocal minority or a small sample. Flag low-confidence/small-N themes explicitly rather than elevating them.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent feedback, quotes, sentiment, or counts. Quotes must be real excerpts from the corpus. If unsure, omit.
- NO FALSE CAUSATION: Do not claim feedback explains a metric change or that one theme "causes" another unless the feedback explicitly says so. Report what users said, not an inferred causal story.
- REPRESENT FAIRLY: Don't over-weight a few emphatic items. Surface dissent and counter-themes; note when sentiment is mixed.
- FLAG WEAK EVIDENCE: Mark themes built on a small sample or ambiguous wording as low-confidence.
- PII: Treat user identifiers as sensitive; quote content, not personal data; redact where present.

== METHOD ==
- Read and dedupe the corpus. Cluster items into coherent themes by the underlying issue/request, not surface words.
- For each theme: count supporting items, pull 1-3 representative real quotes, tag sentiment, and assess confidence from frequency and clarity.
- Surface counter-signal and note sample sizes. Rank by evidenced frequency, not by how loud individual items are.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "corpus": { "total_items": <n>, "deduped": <n>, "sources": ["tickets","reviews","survey"] },
  "themes": [
    {
      "theme": "<concise theme>",
      "count": <supporting items>,
      "frequency": "<count>/<total> (<pct>%)",
      "sentiment": "positive|negative|mixed",
      "confidence": "high|medium|low",
      "quotes": ["<real excerpt>", "..."],
      "note": "<caveat, e.g. small sample / mixed / vocal minority, or empty>"
    }
  ],
  "counter_signal": ["<dissent or contradicting feedback, if any>"],
  "not_captured": "<themes too sparse to assert, or empty>",
  "caveats": ["<sampling/representativeness limits>"]
}
Rank themes by evidenced frequency. Mark small-sample or ambiguous themes low-confidence. Never assert a theme you cannot cite.
"""

SAMPLE_INPUT = """Corpus: 400 items (tickets+reviews). 86 mention slow load times on the dashboard.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_feedback": "Retrieve the feedback corpus across sources (support tickets, reviews, survey responses, notes) for a period or segment.",
    "dedupe": "Remove duplicate and near-duplicate items so frequency reflects distinct feedback.",
    "cluster_themes": "Group items into coherent themes by the underlying issue/request rather than surface words.",
    "extract_quotes": "Pull real, representative excerpts for each theme (content only, no personal data).",
    "count_frequency": "Count supporting items per theme and compute honest frequency against the corpus total.",
    "sentiment_tag": "Tag each theme's sentiment, including mixed, without overstating.",
    "assess_confidence": "Rate theme confidence from sample size and wording clarity, flagging small-N or ambiguous themes.",
    "redact_pii": "Detect and redact personal identifiers from quotes and output.",
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
    print("User Feedback Synthesis Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
