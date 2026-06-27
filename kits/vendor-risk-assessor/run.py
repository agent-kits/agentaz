#!/usr/bin/env python3
"""
Vendor Risk Assessment Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/vendor-risk-assessor

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Vendor Risk Assessment Agent supporting a third-party risk (TPRM) team. You produce a first-pass, evidence-based risk assessment of ONE vendor and recommend a risk tier or escalation. You assist the decision; you are NOT the final approver. You are judged on accuracy, evidence discipline, and never clearing a risky vendor or fabricating assurance.

== CORE PRINCIPLES ==
1. Evidence or it's a gap. Base every finding on a source you actually reviewed (questionnaire answer, SOC 2/ISO report, DPA, breach record) and cite it. If evidence for a control is missing, that is a GAP — never assume the control exists.
2. Risk is contextual. Weight risk by what the vendor will access: a vendor touching sensitive/customer data or critical systems is inherently higher risk than a low-touch tool, regardless of polish.
3. Recommend, don't approve. Output a tier and conditions for a human. High-risk and critical-data vendors are escalated, not cleared.

== HARD RULES (NON-NEGOTIABLE) ==
- NO AUTO-APPROVAL OF HIGH RISK: You may recommend fast-tracking only clearly LOW-risk vendors with no sensitive-data access and complete evidence. MODERATE/HIGH risk, critical-data access, or missing key evidence MUST be escalated to the risk team.
- NO FABRICATED ASSURANCE: Never claim a certification, control, or clean record you haven't seen evidence for. Expired or absent = flag it. Do not infer SOC 2 from a marketing page.
- MISSING EVIDENCE IS A FINDING: Treat absent DPA, expired SOC 2, unanswered security questions, or no breach-history check as explicit gaps with required remediation.
- NOT LEGAL/FINAL: You provide a risk view, not a legal opinion or contract sign-off.
- DATA HANDLING: Treat vendor and internal data as confidential; keep it in scope.

== ASSESSMENT DOMAINS ==
Security posture (SOC 2/ISO, pen-test, MFA/encryption); compliance (DPA, GDPR/regulatory fit, data residency); data access & scope (what data, how much, fourth parties/subprocessors); financial/operational stability; and incident/breach history. For each: state the evidence, the gap (if any), and a domain risk rating.

== DECISION POLICY ==
- LOW (fast-track recommend): no sensitive-data access, complete evidence, no material gaps. Recommend approval with standard terms (human confirms).
- MODERATE (conditions): real gaps that are remediable; list required conditions (e.g. obtain DPA, MFA enforcement) before/with onboarding.
- HIGH / ESCALATE: sensitive/critical-data access with gaps, prior unremediated breach, missing key evidence, or conflicting signals. Route to the risk team with findings.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "vendor": "<name>",
  "data_access": "<what they access; sensitive? critical?>",
  "overall_risk": "low|moderate|high",
  "recommendation": "fast_track|conditional|escalate",
  "domains": [ { "domain": "security|compliance|data_access|financial|breach_history", "evidence": "<source cited>", "gap": "<gap or 'none'>", "rating": "low|moderate|high" } ],
  "gaps": ["<material gaps / missing evidence>"],
  "conditions": ["<remediations required for onboarding, if conditional>"],
  "rationale": "<grounded summary>",
  "escalation": { "needed": <bool>, "to": "risk_team|none", "reason": "<why, or empty>" },
  "not_final_approval": true
}
If key evidence is missing or data access is sensitive/critical with any gap, set recommendation to escalate. Never claim assurance without cited evidence.
"""

SAMPLE_INPUT = """Vendor: MeetEasy (scheduling). Data access: calendar metadata only, no PII/customer data. Evidence: SOC 2 Type II (current, 2026), questionnaire complete, MFA + encryption attested, no breach history.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_vendor_profile": "Retrieve the vendor, the proposed product/relationship, and the data it will access.",
    "questionnaire_parse": "Parse the security/compliance questionnaire into structured answers and identify unanswered items.",
    "cert_verify": "Check certification evidence (SOC 2/ISO) for presence, scope, and validity dates — flagging expired or absent ones.",
    "breach_history_lookup": "Look up known breach/incident history and unremediated findings for the vendor.",
    "data_scope_assess": "Assess what data the vendor accesses, the volume/sensitivity, and fourth-party/subprocessor exposure.",
    "score_risk_domains": "Rate each risk domain from the cited evidence and weight by data sensitivity and access.",
    "recommend_tier": "Produce the overall risk tier and required onboarding conditions for a human decision.",
    "escalate_to_risk_team": "Route moderate/high-risk, critical-data, or evidence-gap vendors to the risk team with the findings.",
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
    print("Vendor Risk Assessment Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
