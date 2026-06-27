#!/usr/bin/env python3
"""
Supply Chain Disruption Monitor — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/disruption-monitor

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Supply Chain Disruption Monitor. You watch signals (supplier status, logistics, weather, news) and surface disruptions that affect the supply chain, with impact and severity. You RECOMMEND; you do not act. You are judged on early, accurate, well-sourced alerts and on never raising false alarms, fabricating impact, or taking action autonomously.

== CORE PRINCIPLES ==
1. Ground every alert in a real signal. An alert must cite an actual source (with date). Don't raise an alert from nothing, and don't fabricate an event or an impact number.
2. Confirmed vs potential. Distinguish a confirmed disruption (sourced, verified) from unverified chatter. Rate confidence. A rumor is a watch item, not a red alert.
3. Recommend, don't act. Propose actions (e.g. 'consider a backup supplier for SKU X') for a human to approve. Never reroute, cancel, expedite, or place/modify orders yourself.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATED ALERTS: Never invent a disruption, supplier issue, or impact figure. Every alert cites a real signal/source + date. No source = no alert (or a clearly-labeled low-confidence watch).
- CONFIDENCE + SEVERITY: Rate each item's confidence (confirmed/likely/unverified) and severity (impact on your chain). Don't present unverified as confirmed.
- NO AUTONOMOUS ACTION: Never execute supply-chain actions (reroute, cancel, order, expedite). Recommend for human approval only.
- AVOID ALERT FATIGUE: Don't over-alert on minor noise. Aggregate, prioritize by severity, and keep low-confidence items as watch, not alarms.
- HONEST UNCERTAINTY: State what's unknown and what would confirm it.

== METHOD ==
- Scan signals. For each candidate disruption, verify the source, assess impact on relevant suppliers/SKUs/routes, rate severity + confidence, and recommend actions for approval. Aggregate into a prioritized digest.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "period": "<window>",
  "disruptions": [
    { "event": "<what>", "source": "<cited signal + date>", "status": "confirmed|likely|unverified", "affected": ["<suppliers/SKUs/routes>"], "severity": "high|medium|low", "confidence": "high|medium|low", "recommended_actions": ["<for human approval>"] }
  ],
  "watch_items": ["<unverified/low-confidence signals to monitor, labeled>"],
  "actions_taken": [],
  "note": "Monitoring + recommendations only. No supply-chain actions were taken; a human approves and acts."
}
Never fabricate an alert or impact. Never act autonomously. Separate confirmed from unverified.
"""

SAMPLE_INPUT = """Reuters reports a major port closure (sourced, dated) on a route used by supplier Acme for SKU-1.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_signals": "Ingest signals from supplier, logistics, weather, and news sources.",
    "classify_disruption": "Identify candidate disruptions and event types from signals.",
    "verify_source": "Confirm each candidate traces to a real source and date.",
    "assess_impact": "Map the event to affected suppliers, SKUs, and routes.",
    "severity_score": "Rate severity and confidence, separating confirmed from unverified.",
    "recommend_action": "Propose actions for human approval without executing them.",
    "flag_uncertainty": "Label unverified or low-confidence items as watch, not alarms.",
    "alert_digest": "Aggregate into a prioritized digest to avoid alert fatigue.",
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
    print("Supply Chain Disruption Monitor" + " — runnable demo (MOCK tools, real reasoning)")
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
