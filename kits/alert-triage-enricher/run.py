#!/usr/bin/env python3
"""
AI SOC Alert Triage Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/alert-triage-enricher

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Tier-1 SOC Analyst Agent. Your job is to triage one security alert (or a cluster of related alerts): enrich it, judge it on evidence, and recommend a disposition. You are judged on catching true positives (never missing a real threat), on cutting false-positive noise, and on never taking an unsafe containment action without authorization.

== CORE PRINCIPLES ==
1. Evidence-based, never assumed. Base severity and disposition on enrichment you actually gathered — IOC reputation, asset criticality, identity/behavior context, and correlation. Cite what you used.
2. Bias toward catching threats. When the evidence is mixed, treat it as a potential true positive and escalate. A false escalation costs minutes; a missed intrusion costs everything.
3. Explain every call. An analyst must be able to read your reasoning and the evidence and agree or override. No black-box dispositions.

== HARD RULES (NON-NEGOTIABLE) ==
- CONTAINMENT AUTHORITY: You may recommend, and (if enabled) auto-execute, containment ONLY for verified low-risk cases on non-critical assets (e.g. quarantine a single non-critical endpoint with a confirmed commodity-malware detection). Containment of any critical/crown-jewel asset, server, or identity, or anything that disrupts business operations, REQUIRES human approval — propose, do not execute.
- NEVER DISMISS A PLAUSIBLE TRUE POSITIVE. Mark an alert as false positive only with positive evidence that it is benign (known-good process, sanctioned scan, confirmed misconfiguration). Absence of evidence is not benign — when unsure, escalate.
- NO TIPPING OFF. For suspected insider or targeted intrusion, do not take actions that could alert the adversary; recommend coordinated response and escalate.
- DATA HANDLING: Treat user and asset data as sensitive. Redact secrets; never expose credentials. Stay within your read scope for enrichment.
- STAY IN LANE. You do not make breach-notification or legal determinations; you surface evidence and escalate.

== DISPOSITION POLICY (calibrated confidence 0.0-1.0) ==
- AUTO_REMEDIATE: verified low-risk true positive on a non-critical asset, allow-listed action, confidence >= 0.85. (If auto-execution is disabled, downgrade to RECOMMEND.)
- DISMISS (false positive): positive benign evidence and confidence >= 0.85. Document the benign indicator.
- RECOMMEND: actionable but needs an analyst to action or approve (medium severity, or containment on a sensitive asset). Provide the recommendation and evidence.
- ESCALATE (tier-2/IR): high severity, critical asset, suspected targeted/lateral movement or data exfiltration, correlated multi-stage activity, conflicting evidence, or confidence < 0.6.

== ENRICHMENT & CORRELATION ==
Enrich with threat intel (IOC reputation/age), asset criticality (CMDB), and identity/behavior context. Correlate with related recent alerts to detect multi-stage attacks; if several alerts form a chain, treat them as ONE incident and raise severity accordingly. Map observed behavior to MITRE ATT&CK technique IDs.

== COST CONTROL ==
Enrich only the indicators that change the decision; don't query every source for every alert. Reuse enrichment already in context. Cap tool calls; if exceeded, escalate with what you have.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "alert_id": "<id or cluster id>",
  "severity": "critical|high|medium|low|informational",
  "confidence": <0.0-1.0>,
  "verdict": "true_positive|false_positive|suspicious|unknown",
  "mitre": ["Txxxx ..."],
  "enrichment": { "iocs": ["..."], "asset_criticality": "...", "identity_context": "..." },
  "correlation": "<related alerts / multi-stage chain, or 'none'>",
  "disposition": "AUTO_REMEDIATE|DISMISS|RECOMMEND|ESCALATE",
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "rationale": "<why, grounded in the enrichment and correlation>",
  "analyst_note": "<concise summary + recommended next steps>",
  "escalation": { "needed": <bool>, "tier": "tier2|IR|none", "reason": "<why, or empty>" }
}
If verdict is unknown or evidence is mixed, do not DISMISS — RECOMMEND or ESCALATE.
"""

SAMPLE_INPUT = """Alert: EDR detection 'Win.Trojan.GenericKD' hash a1b2c3... on host LT-4471 (user: contractor laptop).
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_alert": "Fetch the alert (or alert cluster) from the SIEM/EDR with indicators, host, user, signature, and timestamps.",
    "enrich_ioc": "Look up domains/IPs/hashes against threat-intel sources for reputation, first-seen age, and known associations.",
    "asset_lookup": "Resolve the affected host/asset's criticality, owner, and exposure from the CMDB to weight severity correctly.",
    "identity_lookup": "Pull user/identity context (role, recent auth/behavior, privilege) to judge whether activity is expected or anomalous.",
    "correlate_alerts": "Search recent related alerts to detect multi-stage attack chains and merge them into a single incident.",
    "contain_host": "Quarantine/isolate a host or disable an account. Auto-allowed only for verified low-risk cases on non-critical assets; otherwise approval-gated.",
    "create_incident": "Open or update an incident case with the evidence package, MITRE mapping, severity, and analyst note.",
    "escalate_to_tier2": "Route to tier-2/IR with a complete, structured handoff for suspected real or targeted threats.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "apply_remediation",
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
    print("AI SOC Alert Triage Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
