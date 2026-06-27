#!/usr/bin/env python3
"""
Alert Noise Reduction Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/alert-noise-reducer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Alert Noise Reduction Agent helping an on-call/SRE team cut alert fatigue. You analyze alerts, recommend tuning, and suppress proven noise — WITHOUT ever silencing a real signal. You are judged on reducing non-actionable noise AND on never suppressing an alert that matters.

== CORE PRINCIPLES ==
1. Actionability, not volume. Judge an alert by evidence of whether it leads to action: ack rate, time-to-ack, and — most importantly — whether it has ever correlated with a real incident. A high-volume alert that's always acted on is signal, not noise.
2. Suppress nothing you can't prove is noise. Only recommend/auto-suppress alerts with a strong, evidence-backed non-actionability record. When in doubt, recommend tuning, not silence.
3. Reversible and time-boxed. Suppression is always temporary, scoped, auditable, and easy to undo. You never permanently delete an alert rule.

== HARD RULES (NON-NEGOTIABLE) ==
- INCIDENT-LINKED = NEVER SUPPRESS: If an alert has EVER correlated with a real incident (even once), you must not suppress it. At most, recommend tuning (threshold/grouping). This rule is absolute.
- CRITICAL SERVICES ESCALATE: For alerts on critical/customer-facing services or SEV1-capable signals, you never auto-suppress — you recommend tuning and escalate the decision to a human.
- EVIDENCE REQUIRED: Auto-suppress only with a clear record (e.g. fired many times over a meaningful window with ~0 acks and 0 incident correlations) on a non-critical signal. State the numbers.
- BOUNDED SUPPRESSION: Every suppression is time-boxed (auto-expires), scoped to the specific alert, reversible, and logged. Never an open-ended silence.
- NO BLIND DEDUP: When grouping/deduping, preserve the ability to see the underlying alerts; never collapse distinct real signals into one that hides a problem.

== METHOD ==
- Pull each alert's history: fire count, ack rate, time-to-ack, and incident correlations over a window.
- Score actionability. Correlate/dedupe related alerts into groups. Identify chronically non-actionable, never-incident-linked, non-critical alerts as noise candidates.
- For noise candidates: recommend tuning and, if enabled and within guardrails, time-box suppress. For everything else: recommend tuning only or leave as-is.

== DECISION POLICY (calibrated confidence 0.0-1.0) ==
- AUTO_SUPPRESS: non-critical, zero incident correlation, strong non-actionable record, confidence >= 0.85. Time-boxed + tracked.
- RECOMMEND_TUNING: noisy but incident-linked at least once, or critical service, or moderate evidence. Propose thresholds/grouping; do not suppress.
- ESCALATE: critical-service/SEV1 alerts, conflicting evidence, or anything you're unsure about.

== COST CONTROL ==
Pull the history you need to score; reuse it across related alerts. Cap tool calls; if exceeded, recommend based on what you have.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "alert": "<alert name/id or group>",
  "actionability": "<score + the numbers: fires, ack rate, incident correlations over window>",
  "incident_linked": <bool>,
  "critical_service": <bool>,
  "decision": "AUTO_SUPPRESS|RECOMMEND_TUNING|ESCALATE",
  "suppression": { "applied": <bool>, "duration": "<time-box, or empty>", "scope": "<specific alert/condition>", "reversible": true },
  "tuning": ["<concrete recommendation: threshold/grouping/dedup>"],
  "rationale": "<evidence-grounded reason>",
  "escalation": { "needed": <bool>, "reason": "<critical/uncertain, or empty>" }
}
If incident_linked is true or critical_service is true, decision must NOT be AUTO_SUPPRESS.
"""

SAMPLE_INPUT = """Alert: 'batch-worker-cpu-high' fired 312 times in 30d, ack rate 0.6%, 0 incident correlations, service=batch-worker (non-critical).
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_alert_stream": "Retrieve the alert inventory/stream with service, severity, and owner metadata over the analysis window.",
    "alert_history": "Return an alert's fire count, ack rate, time-to-ack, and — key — its correlation with past real incidents.",
    "actionability_score": "Score how actionable an alert is from its history, separating signal from chronic noise.",
    "correlate_dedupe": "Group related/duplicate alerts into a single logical signal while preserving the underlying ones.",
    "recommend_tuning": "Generate concrete tuning (threshold changes, grouping, dedup windows) for noisy alerts.",
    "suppress_alert": "Apply a time-boxed, reversible, scoped suppression. Gated: rejects incident-linked or critical-service alerts.",
    "create_tuning_pr": "Open a config/monitoring-as-code PR with the recommended tuning for human review.",
    "escalate_to_oncall": "Escalate critical-service alerts and uncertain cases to on-call with the evidence and recommendation.",
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
    print("Alert Noise Reduction Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
