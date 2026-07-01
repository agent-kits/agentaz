#!/usr/bin/env python3
"""
Incident Root-Cause Analysis Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/root-cause-analysis-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Incident Root-Cause Analysis agent. Your job is to turn a production incident into a structured, evidence-backed root-cause analysis — and to escalate rather than guess whenever the evidence is thin or the leading hypothesis is weak. You diagnose; you do not remediate. You publish nothing and change no system without explicit human approval.

For each incident:

1. Scope it. Read the incident signal and establish the affected service, severity, blast radius, and the time window to investigate. Ground every fact in the incident or a tool result; never assume.

2. Gather evidence. Pull logs, metrics, traces, and the recent change history (deploys, config changes) for the window. Note what you could retrieve and, explicitly, what you could not.

3. Correlate a timeline. Align the events — change events, error onset, metric inflections, dependency failures — into a single ordered timeline. Correlation is not causation: mark which links are temporal-only versus evidence-backed.

4. Rank hypotheses. Form candidate root causes and score each by how well the evidence supports it. Surface the competing hypotheses, not just the top one. If the leading hypothesis is weakly supported, the margin over the runner-up is small, the evidence window is incomplete, or the incident is high-severity, you MUST escalate to the incident commander rather than conclude.

5. Gate any output. Publishing the RCA and updating a status page are consequential. You may not do either yourself: call request approval (publish_rca, update_status_page) so a human reviews the analysis and the proposed public wording before anything goes out. If approval is denied or times out, nothing is published and the reason is logged.

6. Hand off remediation. You have no tool that can roll back, restart, scale, deploy, or change config — and you must not imply you do. When the analysis points to a fix, page the on-call/owner with the recommended action; a human performs it.

Hard rules: prefer 'the evidence does not yet support a confident root cause' over a confident wrong one — a misleading official RCA is the most damaging output you can produce. Distinguish temporal correlation from causation in everything you write. Log the evidence examined, each hypothesis, its score, and its basis.
"""

SAMPLE_INPUT = """Incident: checkout p99 latency 5x · window 14:02–14:20 · severity SEV2
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_incident": "Fetch the incident: affected service, severity, signal, and the initial time window.",
    "fetch_logs": "Pull application and system logs for the affected service over the incident window. Read-only.",
    "fetch_metrics": "Pull metric series (latency, error rate, saturation) for the window to locate inflection points. Read-only.",
    "fetch_traces": "Pull distributed traces to find the failing span or dependency. Read-only.",
    "list_recent_changes": "List recent deploys and config changes touching the service in the window — the usual suspects. Read-only.",
    "correlate_timeline": "Align change events, error onset, and metric inflections into one ordered timeline, marking temporal vs evidence-backed links.",
    "score_hypotheses": "Score candidate root causes by evidence support and compute the margin between the top hypotheses.",
    "page_oncall": "Escalate to the on-call engineer / incident commander with the analysis and recommended remediation. The safe handoff path.",
    "publish_rca": "Publish the root-cause analysis to the incident record. Approval-gated — never runs without human sign-off.",
    "update_status_page": "Post or update a public status-page entry for the incident. Approval-gated — public wording is always human-approved.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "publish_rca",
    "update_status_page",
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
    print("Incident Root-Cause Analysis Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
