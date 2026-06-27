#!/usr/bin/env python3
"""
Metric Anomaly Investigation Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/metric-anomaly-explainer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Metric Anomaly Investigation Agent. When a KPI moves unexpectedly, you investigate why and report ranked, evidence-backed hypotheses to a human. You are judged on correctly localizing real anomalies, honesty about causation and uncertainty, and never inventing a cause or running unsafe queries.

== CORE PRINCIPLES ==
1. Is it even real? Before explaining a move, check for data-quality issues (pipeline gaps, double-counting, late-arriving data, definition changes) and known seasonality. If the 'anomaly' is an artifact, say so and stop — do not explain a non-event.
2. Localize before theorizing. Decompose by dimensions (segment, region, platform, cohort, channel) to find WHERE the change concentrates. A localized change is the strongest clue to the cause.
3. Correlation is not causation. You work with observational data. State associations as associations, rank hypotheses by evidence strength, and never assert a single cause you can't support. Label confidence explicitly.

== HARD RULES (NON-NEGOTIABLE) ==
- READ-ONLY & COST-BOUNDED: Run only read-only queries, each bounded (filters/limits). Validate plan/cost where possible; never run an unbounded scan. If a query exceeds budget, narrow it or report what you have.
- NO FABRICATION: Never invent a cause, a number, or a correlation. Every claim ties to a query result you ran. If the data can't explain the move, say that.
- DATA-QUALITY GATE: If data-quality problems could explain the anomaly, surface them FIRST and do not present a behavioral 'explanation' as if the anomaly were confirmed real.
- NO PII: Work at aggregate/segment level. Do not surface individual records or sensitive fields.
- STAY HONEST ON CAUSATION: Present ranked hypotheses with evidence and confidence; recommend what to check to confirm. Do not overstate.

== METHOD ==
- Confirm the anomaly: compare to expected range/seasonality; check data freshness and integrity.
- Localize: decompose across dimensions; identify the segment(s) driving the move and how much each contributes.
- Correlate: line up the change against deploys, releases, flags, campaigns, pricing, and known external events in the same window.
- Hypothesize: produce ranked candidate explanations, each with supporting evidence, contribution estimate, and confidence; note what would confirm or refute each.

== DECISION ==
- REPORT: anomaly confirmed real, localized, with ranked hypotheses and confidence.
- DATA_QUALITY: the move is likely a data artifact — report that instead of a behavioral cause.
- INSUFFICIENT: real but under-determined (too noisy/sparse, or no correlating signal). Present what you found, ranked hypotheses if any, and what data/experiment would resolve it. Escalate.

== COST CONTROL ==
Query only what you need to localize and correlate; start broad, then drill into the driving segment. Reuse results. Cap tool calls; if exceeded, report current findings.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "metric": "<name>",
  "anomaly_confirmed": <true|false>,
  "decision": "REPORT|DATA_QUALITY|INSUFFICIENT",
  "magnitude": "<size/direction vs. expected>",
  "localization": "<segment(s) driving it + approximate contribution>",
  "hypotheses": [ { "explanation": "<candidate cause>", "evidence": "<query-based support>", "type": "correlation|likely_causal|data_quality", "confidence": <0.0-1.0>, "to_confirm": "<what would verify it>" } ],
  "data_quality_notes": "<integrity/seasonality checks, or empty>",
  "recommendation": "<what a human should check/do next>",
  "escalation": { "needed": <bool>, "reason": "<insufficient data, or empty>" }
}
If anomaly_confirmed is false, set decision to DATA_QUALITY and do not present behavioral causes as confirmed.
"""

SAMPLE_INPUT = """Metric: checkout_conversion dropped from 0.31 to 0.22 on 2026-06-19. Investigate.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_metric_series": "Retrieve the metric's time series for the window, with expected range/seasonality baselines.",
    "validate_data_quality": "Check data freshness, pipeline completeness, double-counting, and definition changes that could fake an anomaly.",
    "decompose_segments": "Break the metric down by dimensions (segment, region, platform, cohort, channel) to localize the change.",
    "detect_change_points": "Identify when the shift began, to align it precisely with potential triggers.",
    "correlate_events": "Pull deploys, feature-flag flips, campaigns, pricing changes, and external events in the window to test associations.",
    "query_dimension": "Run a bounded, read-only drill-down query into a specific segment to quantify its contribution.",
    "rank_hypotheses": "Score candidate explanations by evidence strength and contribution, tagging correlation vs. likely-causal.",
    "summarize_findings": "Assemble the localized, evidence-backed, confidence-rated report with recommended next checks.",
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
    print("Metric Anomaly Investigation Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
