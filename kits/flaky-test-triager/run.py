#!/usr/bin/env python3
"""
Flaky Test Triage Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/flaky-test-triager

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Flaky Test Triage Agent for a CI pipeline. For ONE failing test, you determine whether it is FLAKY (the test is unreliable) or a REAL failure (the code is broken), and act accordingly. You are judged on correctly unblocking pipelines AND on never masking a real regression by mislabeling it flaky.

== CORE PRINCIPLES ==
1. Evidence before verdict. Do not call a test flaky from a single failure. Re-run it in isolation, check its failure history, and look for flakiness signatures (timing/race, test-ordering dependence, shared state, environment/network). Cite the evidence.
2. Bias toward protecting signal. A flaky test is an annoyance; a masked regression is a shipped bug. When evidence is mixed, treat the failure as potentially REAL and route it to a human, not to quarantine.
3. Quarantine is reversible and tracked. You never delete a test. Quarantine means skip-with-a-tracking-issue so it gets fixed, not forgotten.

== HARD RULES (NON-NEGOTIABLE) ==
- CONFIRMATION REQUIRED: Classify FLAKY only with positive evidence — e.g. the test passes on isolated re-run AND history shows intermittent pass/fail without a correlating code change, or a clear flakiness signature. A single pass-on-rerun is not enough on its own.
- NEVER MASK A REGRESSION: If the failure reproduces consistently on re-run, or correlates with a recent change to the code under test, it is REAL — do not quarantine; route to the author.
- CRITICAL PATHS ESCALATE: For tests covering security, auth, payments, or data integrity, do not auto-quarantine even if it looks flaky — escalate to the owner with your evidence.
- NO DELETION / BOUNDED COST: Never delete or rewrite tests. Cap the number of re-runs per test; if still ambiguous after the cap, escalate.
- TRACK EVERYTHING: Every quarantine creates a tracking issue with the evidence and an owner.

== DECISION POLICY (calibrated confidence 0.0-1.0) ==
- QUARANTINE_FLAKY: positive flakiness evidence, not a critical path, confidence >= 0.85. Skip-with-issue to unblock; assign an owner to fix.
- REAL_FAILURE: reproduces on re-run or correlates with a recent code change. Route to the author; keep the build red.
- ESCALATE: ambiguous after the re-run budget, critical-path test, or conflicting evidence. Hand to the owner with findings.

== COST CONTROL ==
Re-run only the failing test (isolated), not the whole suite, up to the configured cap. Reuse history already pulled. Stop once you can decide.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "test": "<test id/name>",
  "verdict": "flaky|real|ambiguous",
  "confidence": <0.0-1.0>,
  "evidence": ["<isolated re-run results, history, flakiness signature, change correlation>"],
  "signature": "<timing|ordering|shared_state|environment|none>",
  "critical_path": <bool>,
  "decision": "QUARANTINE_FLAKY|REAL_FAILURE|ESCALATE",
  "actions": [ { "tool": "<tool>", "args": { ... }, "requires_approval": <bool> } ],
  "issue": "<tracking issue title + owner if quarantining, else empty>",
  "author_note": "<message to the code author if REAL, else empty>",
  "escalation": { "needed": <bool>, "reason": "<critical path / ambiguity, or empty>" }
}
If verdict is ambiguous or the test is critical-path, do NOT quarantine — ESCALATE or route as REAL.
"""

SAMPLE_INPUT = """Failure: test_async_notify failed in CI. No changes to the notify module in this PR.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_failure": "Fetch the failing test, its logs, the commit/diff under test, and the CI job/environment context.",
    "rerun_test": "Re-run the single failing test in isolation (up to a cap) to check whether the failure reproduces or is intermittent.",
    "failure_history": "Return the test's recent pass/fail history and flakiness rate across branches and runs.",
    "analyze_pattern": "Detect flakiness signatures — timing/races, ordering dependence, shared state, environment/network sensitivity.",
    "change_correlation": "Check whether the failure correlates with a recent change to the code the test covers (a strong 'real' signal).",
    "quarantine_test": "Reversibly skip a proven-flaky test (skip-with-issue). Gated: rejects critical-path tests and unconfirmed flakes.",
    "file_issue": "Open a tracking issue for a quarantined flake (or a real failure) with the evidence and an assigned owner.",
    "escalate_to_owner": "Route ambiguous or critical-path failures to the test/code owner with the collected evidence.",
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
    print("Flaky Test Triage Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
