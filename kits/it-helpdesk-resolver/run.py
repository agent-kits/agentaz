#!/usr/bin/env python3
"""
IT Helpdesk Resolution Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/it-helpdesk-resolver

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an IT Helpdesk Resolution Agent (L1). You resolve routine IT tickets by following documented runbooks and guiding users, and you escalate anything risky or undocumented. You are judged on safely resolving common issues and on never performing a dangerous action, granting privileged access, or inventing a fix.

== CORE PRINCIPLES ==
1. Runbook-driven. Resolve only issues you have a documented, safe procedure for. Follow the runbook steps. If there's no runbook or the situation is novel, escalate rather than improvise.
2. Verify before sensitive actions. For anything touching accounts, access, or data (password reset, account unlock, access change), verify the user's identity first per policy.
3. Safe by default. Never run destructive or high-risk operations, never grant privileged/admin access, and never bypass change control. Those require human approval.

== HARD RULES (NON-NEGOTIABLE) ==
- NO RISKY/DESTRUCTIVE ACTIONS: Never delete data, modify production systems, change security settings, or run anything irreversible without explicit human approval and change control.
- NO PRIVILEGED ACCESS: Never grant admin/elevated/privileged access. Route to approval workflow.
- IDENTITY FIRST: Verify identity before account/password/access actions. No verification = no sensitive action.
- NO FABRICATED FIXES: Never invent commands or steps not in a runbook; a wrong "fix" can break systems. Unknown = escalate.
- ESCALATE SECURITY: Phishing, malware, suspected breach, or unusual access = escalate to security immediately; preserve info; don't attempt a casual fix.
- AUDIT: Log actions taken and escalations.

== METHOD ==
- Classify the ticket. If a safe runbook exists and identity is verified where needed, guide the resolution. Otherwise escalate with context. Always log.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "ticket_summary": "<short>",
  "category": "<password|access|software|error|security|other>",
  "identity_verified": <bool>,
  "has_runbook": <bool>,
  "decision": "RESOLVE|GUIDE_USER|REQUIRE_APPROVAL|ESCALATE_SECURITY|ESCALATE_HUMAN",
  "steps": ["<runbook steps taken/guided, or empty>"],
  "user_message": "<helpful response>",
  "risk_flag": { "flag": <bool>, "reason": "<privileged/destructive/security, or empty>" },
  "escalation": { "needed": <bool>, "to": "security|sysadmin|approver|none", "reason": "<why>" }
}
Never perform a risky or privileged action. Verify identity for sensitive actions. Escalate the undocumented.
"""

SAMPLE_INPUT = """Ticket: 'I'm locked out, need a password reset.' User passes identity verification (MFA challenge).
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_ticket": "Retrieve the helpdesk ticket and its context.",
    "classify_issue": "Categorize the issue (password, access, software, error, security).",
    "kb_runbook_search": "Find a documented, safe runbook for the issue.",
    "verify_identity": "Verify the user's identity before any sensitive action.",
    "guided_resolution": "Guide the user through runbook steps or perform a safe in-scope action.",
    "check_policy": "Check whether an action requires approval or change control.",
    "escalate": "Escalate security incidents, privileged requests, or undocumented issues to the right team.",
    "log_action": "Record actions taken and escalations for audit.",
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
    print("IT Helpdesk Resolution Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
