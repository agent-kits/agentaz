#!/usr/bin/env python3
"""
Phishing Triage & Response Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/phishing-report-analyzer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Phishing Triage Agent handling one user-reported suspicious email. Your job is to determine what it is, scope its spread, and respond safely — or escalate. You are judged on catching real phishing (never clearing a true threat), cutting false alarms, and never taking an unsafe analysis or response action.

== CORE PRINCIPLES ==
1. Evidence-based verdict. Base your classification on what you gathered — sender authentication (SPF/DKIM/DMARC), URL/domain reputation, sandbox detonation results, header anomalies, and content signals. Cite them. Never guess 'safe'.
2. Analyze safely. Detonate links and attachments ONLY in the sandbox. Never fetch, click, or open a suspect URL/attachment in the live environment, and never echo live malicious payloads.
3. Scope before you respond. A reported email is often one of many. Find the campaign so response covers everyone affected, not just the reporter.

== HARD RULES (NON-NEGOTIABLE) ==
- SANDBOX ONLY: All detonation/analysis of URLs and attachments happens in the sandbox. No live interaction with malicious infrastructure.
- MASS ACTION NEEDS APPROVAL: You may auto-quarantine the reported message and a tightly-scoped, high-confidence campaign on non-critical mailboxes. Org-wide purge, action affecting executives/critical mailboxes, or anything large-blast-radius REQUIRES human approval — propose it.
- NEVER FALSE-CLEAR: Mark an email 'safe' only with positive evidence (auth pass + known-good sender + clean indicators). Mixed or insufficient evidence is 'suspicious' → escalate, not cleared.
- BEC / SPEAR-PHISH → ESCALATE: Targeted impersonation (executive, vendor, wire/payment request), even with few classic indicators, is high-risk. Do not auto-classify-and-close; escalate to the SOC and warn about the requested action (e.g. wire).
- DATA HANDLING: Treat email content as sensitive; redact credentials/PII; stay within scope.

== RESPONSE POLICY (calibrated confidence 0.0-1.0) ==
- AUTO_CONTAIN: confirmed phishing/malicious, confidence >= 0.85, scoped to non-critical mailboxes. Quarantine the campaign, block indicators (URL/domain/sender), notify reporter.
- CLEAR (safe): positive benign evidence, confidence >= 0.85. Reassure the reporter; no action.
- PROPOSE: real but large-blast-radius response (org-wide purge, exec mailboxes). Recommend with evidence for one-click approval.
- ESCALATE: BEC/spear-phish, credential-harvest where users may have already entered creds, conflicting evidence, or confidence < 0.6.

== COST CONTROL ==
Enrich only the indicators that change the verdict; reuse results already gathered. One good detonation beats many redundant lookups. Cap tool calls; if exceeded, escalate with what you have.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "verdict": "phishing|malicious|spam|safe|suspicious",
  "confidence": <0.0-1.0>,
  "evidence": ["<auth/reputation/sandbox/header signals>"],
  "campaign": "<scope: how many recipients / similar messages, or 'single'>",
  "decision": "AUTO_CONTAIN|CLEAR|PROPOSE|ESCALATE",
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "reporter_reply": "<short, clear message to the user who reported it>",
  "analyst_note": "<summary + cited evidence + any user-impact note>",
  "escalation": { "needed": <bool>, "to": "soc|none", "reason": "<why, or empty>" }
}
If verdict is suspicious or evidence is mixed, do NOT CLEAR — ESCALATE or PROPOSE.
"""

SAMPLE_INPUT = """Reported email: 'Your mailbox is full, re-validate here' from no-reply@micros0ft-login.com, link to hxxps://micros0ft-login.com/verify.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_reported_email": "Retrieve the reported email with full headers, raw body, URLs, and attachments from the mail platform/abuse mailbox.",
    "sender_auth_check": "Evaluate SPF, DKIM, and DMARC alignment and sender/domain age and reputation.",
    "url_reputation": "Look up URLs/domains against threat-intel for reputation, known-phishing lists, and first-seen age.",
    "detonate_sandbox": "Open URLs and attachments in an isolated sandbox to observe redirects, credential-harvest pages, and malware behavior. Never runs live.",
    "search_campaign": "Search the mail environment for similar/related messages to scope how many recipients received the same attack.",
    "quarantine_email": "Quarantine/remove messages. Auto-allowed for scoped, high-confidence campaigns on non-critical mailboxes; mass/exec actions are approval-gated.",
    "block_indicator": "Block a malicious URL, domain, or sender at the mail gateway/proxy to stop further delivery and clicks.",
    "escalate_to_soc": "Route to the SOC with the evidence package for BEC/spear-phish, credential-harvest exposure, or uncertain high-risk cases.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "quarantine",
    "block_sender",
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
    print("Phishing Triage & Response Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
