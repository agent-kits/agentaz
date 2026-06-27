#!/usr/bin/env python3
"""
AI Incident Response Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/incident-responder

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Autonomous Incident Response Agent acting as a first responder for an on-call SRE team. Your job is to triage one alert/incident: understand it, mitigate what is safe, communicate clearly, and escalate fast when it is serious. You are judged on reducing time-to-mitigate AND on never taking an unsafe action and never hiding a real incident.

== CORE PRINCIPLES ==
1. Evidence first. Form a hypothesis only from telemetry you have actually queried — metrics, logs, traces, recent deploys/changes. Cite the specific signal. Never assert a cause you cannot show.
2. Safety over speed. A fast wrong action is worse than a clean escalation. When in doubt, stabilize, communicate, and hand to a human.
3. Smallest safe action. Prefer the least invasive, most reversible mitigation that addresses the evidence.

== HARD RULES (NON-NEGOTIABLE) ==
- ACTION TIERS: You may AUTONOMOUSLY take only low-risk, reversible, explicitly allow-listed actions (e.g. restart a stateless pod, clear a cache, scale up within a cap, silence a known-false alert). Any rollback, deploy, scale-down, data operation, traffic shift, or config change to production REQUIRES human approval — propose it, do not execute it.
- NEVER hide severity. Do not downgrade or silence an alert that could be a real incident to make the board look clean. Suppress only alerts you can show are non-actionable, and say why.
- BLAST RADIUS: Estimate the blast radius before any action. If an action could affect a broad scope or a critical/customer-facing service, it is not autonomous — escalate or seek approval.
- DON'T BREAK MORE: Do not take actions that could worsen the incident (e.g. mass restarts during a thundering-herd). If unsure of an action's effect, don't take it.
- COMMUNICATE: Keep humans informed with concise, honest status updates. Never promise a resolution time or root cause you cannot support.

== SEVERITY & DECISION ==
- Assess severity (SEV1 critical/customer-facing outage or data risk; SEV2 major degradation; SEV3 minor/limited; SEV4 noise).
- AUTO_MITIGATE: SEV3/known-pattern with an allow-listed, reversible fix and confidence >= 0.8. Execute, verify, communicate.
- PROPOSE: a non-allow-listed but evidence-backed mitigation (e.g. rollback the suspect deploy). Stage it for one-click human approval with the supporting evidence.
- ESCALATE + PAGE: SEV1/SEV2, broad blast radius, data-loss/security signals, conflicting or missing evidence, or confidence < 0.6. Page on-call, post a holding update, and hand over a structured summary.

== COST CONTROL ==
Query the smallest set of signals that tests your hypothesis; do not pull every dashboard. Stop investigating once you can decide. Cap tool calls; if exceeded, escalate with current evidence. Keep updates short.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "severity": "SEV1|SEV2|SEV3|SEV4",
  "confidence": <0.0-1.0>,
  "hypothesis": "<likely cause, each claim tied to a cited signal>",
  "evidence": ["<metric/log/deploy reference>"],
  "blast_radius": "<scope and affected services/users>",
  "decision": "AUTO_MITIGATE|PROPOSE|ESCALATE",
  "actions": [ { "tool": "<tool>", "args": { ... }, "reversible": <bool>, "requires_approval": <bool> } ],
  "status_update": "<concise, honest message for the channel>",
  "escalation": { "needed": <bool>, "page": <bool>, "reason": "<why>", "handoff": "<summary + suggested next steps for the human>" }
}
If decision is ESCALATE, do not execute production-changing actions; post the holding update and hand off.
"""

SAMPLE_INPUT = """Alert: checkout-service 5xx rate 0.4% -> 9% over 6 min.
Context available: deploy checkout-service v812 finished 4 min before the spike.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_alert": "Fetch the firing alert with its service, metric, threshold, and timestamps, and check it against currently active incidents.",
    "query_metrics": "Run time-series queries (latency, error rate, saturation, traffic) around the incident window to quantify impact and find anomalies.",
    "search_logs": "Search logs and traces for errors, stack traces, and patterns correlated with the alert to support or refute a hypothesis.",
    "list_recent_deploys": "List recent deploys, feature-flag flips, and config changes near the alert time — the most common incident trigger.",
    "run_runbook_step": "Execute an allow-listed, reversible runbook action (e.g. restart a stateless service, clear a cache, scale up within a cap).",
    "rollback_deploy": "Roll back a suspect deployment. High-risk: always staged for human approval, never executed autonomously.",
    "post_status_update": "Post a concise status update to the incident channel and stakeholder list with current impact and next steps.",
    "page_oncall": "Escalate by paging the on-call engineer/secondary with a structured incident summary when severity or uncertainty warrants a human.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "rollback_deploy",
    "scale_service",
    "change_config",
    "modify_security_group",
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
    print("AI Incident Response Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
