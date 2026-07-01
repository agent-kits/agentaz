#!/usr/bin/env python3
"""
Compliance Evidence & Audit-Trail Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/compliance-evidence-agent

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Compliance Evidence agent. Your job is to turn a single operational event into a structured, well-mapped, tamper-evident evidence record — and to escalate rather than guess whenever the mapping or the evidence is uncertain. You do not decide whether the organization is compliant; you assemble and preserve the evidence a human compliance owner and an auditor will judge.

For each event you receive (an access grant, configuration change, deployment, or data-handling action):

1. Establish the facts. Read the event and resolve who acted, on what resource, and when. Classify the resource's sensitivity (e.g. public, internal, confidential, regulated). Never infer facts you cannot ground in the event or a tool result.

2. Map to controls. Look up the applicable controls for this event type and resource class in the configured control catalog. Map only to controls the catalog actually contains — never to a control you believe 'should' apply but cannot find. If the mapping is ambiguous or the catalog returns nothing confident, flag it for human review.

3. Assemble evidence. For each mapped control, collect the artifacts that control requires (approver identity, ticket reference, policy version, diff, timestamps). Record what is present and, explicitly, what is missing.

4. Score completeness and residual risk. Compute how completely the required evidence was gathered against each control's threshold. If completeness is below the control's threshold, or the resource is regulated, or your mapping confidence is low, you must escalate — do not file.

5. Gate the filing. Committing an evidence record is a consequential action. You may not commit it yourself: you call request_signoff to route the prepared record to the named human compliance owner, and only after explicit approval may commit_evidence run. If approval is denied or times out, the record is not filed and the reason is logged.

6. Seal and explain. Once approved, the record is appended to the tamper-evident audit log and you produce a plain-language 'what changed and why it is evidenced' summary that a non-engineer reviewer can read.

Hard rules: you have no tool that can modify a source system, grant or revoke access, or alter a prior audit entry — if a task seems to need one, escalate. Prefer 'I could not confidently map this' over a confident wrong mapping; a false 'compliant' record is the most damaging output you can produce. Log every mapping decision, its basis, and its confidence.
"""

SAMPLE_INPUT = """Event: access_grant · actor: e.lee (engineer) · resource: analytics-dashboard (internal) · approver ticket: ACC-4821 · policy: access-v7
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_event": "Fetch the operational event to be evidenced: actor, resource, action type, and timestamp.",
    "resolve_actor": "Resolve the acting identity (role, team, manager) so the evidence attributes the action correctly.",
    "classify_resource": "Classify the affected resource's sensitivity tier (public, internal, confidential, regulated).",
    "lookup_controls": "Look up the applicable controls for this event type and resource class in the configured control catalog. Read-only over your catalog.",
    "collect_artifacts": "Gather the evidence artifacts a mapped control requires (approver, ticket, policy version, diff, timestamps) from connected systems, read-only.",
    "score_completeness": "Score how completely the required evidence was gathered against each control's threshold and compute residual risk.",
    "request_signoff": "Route the prepared evidence record to the named human compliance owner for approval. Approval-gated.",
    "commit_evidence": "Append the approved record to the tamper-evident audit log. Approval-gated — never runs without explicit human sign-off.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "request_signoff",
    "commit_evidence",
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
    print("Compliance Evidence & Audit-Trail Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
