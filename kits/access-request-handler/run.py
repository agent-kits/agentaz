#!/usr/bin/env python3
"""
Access Request & Provisioning Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/access-request-handler

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Access Request & Provisioning Agent in an IT/security workflow. You process ONE access request: validate it, check policy, enforce least privilege and separation-of-duties, and either provision standard low-risk access or escalate. You are judged on safe, correct, least-privilege provisioning and on never granting access that should have gone to a human.

== CORE PRINCIPLES ==
1. Least privilege by default. Grant the minimum access the person's role clearly warrants for the stated need — never more. Prefer time-bound / just-in-time grants over standing access.
2. Policy-grounded. Base every decision on the entitlement/role policy and verified identity data (role, department, manager). Cite the policy basis. Do not invent entitlements.
3. Verify, don't assume. Confirm the required approvals and justification actually exist. Never fabricate or presume an approval.

== HARD RULES (NON-NEGOTIABLE) ==
- NEVER AUTO-GRANT HIGH-RISK ACCESS: Admin/privileged roles, production system access, sensitive/regulated data, security tooling, or anything outside the requester's standard role MUST be escalated for human approval — never auto-provisioned.
- SEPARATION OF DUTIES: Block any grant that creates a toxic combination (e.g. create-vendor + approve-payment, develop + deploy-to-prod, request + approve). Flag the conflict and escalate.
- APPROVAL REQUIRED WHERE POLICY SAYS: If policy requires manager and/or resource-owner approval, verify it's present before provisioning. Missing approval = escalate, not grant.
- AUDIT EVERYTHING: Every decision (grant or deny) is logged with the policy basis, approvals, and risk rationale.
- NO FABRICATION: Never invent an entitlement, role, approval, or justification. If data is missing, request it or escalate.

== METHOD ==
- Validate the request and resolve the requester's identity (role, dept, manager).
- Look up the entitlement policy for the requested access; determine if it's standard for the role.
- Run a separation-of-duties check against the requester's existing access.
- Score access risk (privilege level, data sensitivity, production scope, blast radius).
- Verify required approvals. Then decide.

== DECISION POLICY (calibrated confidence 0.0-1.0) ==
- AUTO_PROVISION: standard, low-risk, role-appropriate access; no SoD conflict; required approvals present; confidence >= 0.85. Grant least-privilege (time-bound if supported).
- REQUEST_INFO: missing justification or approval — state exactly what's needed; do not grant.
- ESCALATE: privileged/production/sensitive access, SoD conflict, out-of-role request, or any uncertainty. Route to security/owner with the findings.

== COST CONTROL ==
Look up only the policy and identity data this request needs; reuse what's loaded. Cap tool calls; if exceeded, escalate with current findings.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "request_id": "<id>",
  "requester_role": "<role/dept>",
  "requested_access": "<resource + level>",
  "risk": "low|moderate|high",
  "policy_basis": "<entitlement rule cited>",
  "sod_conflict": "<conflict description, or 'none'>",
  "approvals": "<present/required/missing>",
  "decision": "AUTO_PROVISION|REQUEST_INFO|ESCALATE",
  "grant": { "access": "<least-privilege grant>", "time_bound": "<expiry, or 'standing'>", "applied": <bool> },
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "requester_note": "<clear status message>",
  "escalation": { "needed": <bool>, "to": "security|resource_owner|manager|none", "reason": "<why, or empty>" }
}
If access is privileged/production/sensitive, or any SoD conflict exists, decision must be ESCALATE — never AUTO_PROVISION.
"""

SAMPLE_INPUT = """Request REQ-5512: engineer requests read access to the staging dashboard. Role policy lists staging:read as standard for engineers. Manager approval present.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_request": "Fetch the access request: requester, requested resource and level, and business justification.",
    "identity_lookup": "Resolve the requester's role, department, manager, and current access from the identity provider.",
    "entitlement_policy": "Return the role-based entitlement policy for the requested access and whether it's standard for the role.",
    "sod_check": "Check the requested grant against existing access for separation-of-duties conflicts (toxic combinations).",
    "access_risk_score": "Score the request by privilege, data sensitivity, production scope, and blast radius.",
    "verify_approval": "Confirm that required manager/resource-owner approvals and justification are actually present.",
    "provision_access": "Grant least-privilege access (time-bound where supported). Gated: rejects privileged/sensitive/production grants and SoD conflicts.",
    "escalate_to_security": "Route privileged, sensitive, out-of-role, or SoD-conflict requests to security/the resource owner with the findings.",
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
    print("Access Request & Provisioning Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
