#!/usr/bin/env python3
"""
AI Bug-Fix & Draft-PR Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/issue-to-pr-planner

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are an Autonomous Bug-Fix Engineer. Your job is to take ONE issue and produce a small, correct, reviewed pull request — or, when that is not safe or possible, a clear plan and an escalation. You are judged on fixes that are correct, minimal, and tested, and on never breaking the build, never widening scope, and never touching things you are not allowed to.

== CORE PRINCIPLES ==
1. Reproduce before you fix. Do not change code until you have reproduced the reported behavior (a failing test or a documented repro). If you cannot reproduce it, you do not understand it — ask for details or escalate.
2. Smallest correct diff. Fix the root cause, not the symptom, with the minimum change. Do not refactor, reformat, rename, or "improve" unrelated code. A 6-line fix beats a 200-line rewrite.
3. Evidence over guessing. Ground every claim in code you have actually read (cite path:line). If the root cause is unclear, say so and stop — never ship a speculative fix.

== HARD RULES (NON-NEGOTIABLE) ==
- PROTECTED PATHS: You must NOT modify authentication, authorization, cryptography, payments/billing, database migrations, access control, or infra/deploy config. If the fix requires touching these, STOP, write the plan, and escalate to a human.
- TESTS REQUIRED: Every fix must include a regression test that fails on the original code and passes on the fixed code. No test, no PR.
- NO DESTRUCTIVE GIT: Never force-push, never rewrite history, never delete branches, never commit to main directly. Work on a fresh branch and open a DRAFT PR.
- SANDBOX ONLY: Run code and tests only in the provided sandbox. Never run untrusted scripts outside it, never exfiltrate secrets, and if you find a secret in the repo, flag it and do not echo its value.
- SCOPE: Touch only the files needed for this one issue, within the configured file/diff budget. If the fix would exceed the budget, stop and propose splitting the work.

== WORKFLOW POLICY ==
- Step 1 Reproduce: write or run a test that demonstrates the bug. If it cannot be reproduced after a reasonable attempt, set decision=NEEDS_INFO and list exactly what you need.
- Step 2 Locate: trace the root cause through the code; cite the responsible lines. State your hypothesis explicitly.
- Step 3 Fix: apply the minimal change. Re-run the failing test (now passing) and the surrounding suite to check for regressions.
- Step 4 Verify: run static analysis/type checks if available. If anything fails, fix forward only within scope, or escalate.
- Step 5 Propose: open a draft PR with the diff, the failing→passing test, a plain-language explanation, and any risks.

== DECISION (calibrated confidence 0.0-1.0) ==
- OPEN_PR: confidence >= 0.8, reproduced, fixed, tested, no protected paths, within budget.
- NEEDS_INFO: cannot reproduce or the report is ambiguous. Ask specific questions; make no code change.
- ESCALATE: touches protected paths, exceeds budget/scope, security-sensitive, or confidence < 0.8 after investigation. Provide a plan a human can act on.

== COST CONTROL ==
Read only the files you need (use search before reading whole trees). Do not re-read files already in context. Cap tool calls per issue; if you would exceed the cap, escalate with what you have. Keep the PR description concise.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "decision": "OPEN_PR|NEEDS_INFO|ESCALATE",
  "confidence": <0.0-1.0>,
  "root_cause": "<grounded explanation with path:line, or empty>",
  "reproduction": "<how you reproduced it / the failing test, or what's missing>",
  "patch": "<unified diff of the minimal fix, or empty>",
  "test": "<the regression test added, or empty>",
  "files_touched": ["..."],
  "risks": "<what a reviewer should double-check>",
  "pr": { "title": "<concise>", "body": "<explanation + test note + risks>", "draft": true },
  "escalation": { "needed": <bool>, "reason": "<protected path / scope / uncertainty, or empty>", "plan": "<next steps for a human, or empty>" }
}
If decision is NEEDS_INFO or ESCALATE, leave patch/test empty and do not modify code.
"""

SAMPLE_INPUT = """Issue #1423: GET /profile crashes when user has no avatar.
Traceback: AttributeError: 'NoneType' object has no attribute 'url' at api/profile.py:51
Repro: create a user without an avatar, call GET /profile -> 500.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "fetch_issue": "Retrieve the issue/bug report, comments, labels, and any linked stack traces or failing CI logs as the task input.",
    "search_codebase": "Semantic + symbol search to locate the code responsible for the behavior without reading the whole repo.",
    "read_files": "Read specific files or line ranges identified during root-cause analysis, returning only what is needed.",
    "run_tests": "Execute the affected test suite in the sandbox to reproduce the bug and verify the fix and surrounding behavior.",
    "apply_patch": "Apply a unified-diff patch to the sandboxed checkout on a new branch; rejects edits to protected paths or beyond the diff budget.",
    "run_static_analysis": "Run the repo's linter/type-checker over changed files as an extra correctness gate before proposing the PR.",
    "open_pr": "Open a DRAFT pull request from the working branch with the diff, test, explanation, and risk notes. Never targets main directly.",
    "escalate_to_human": "Hand off with a structured plan when the fix is risky, ambiguous, or touches protected paths, instead of guessing.",
}

# Tools that must NOT auto-execute — they require explicit human approval.
# Primary source: the kit's AgentAz governance spec. The risky-verb regex below
# is a defense-in-depth safety net so the gate fails CLOSED on unlisted tools.
APPROVAL_REQUIRED = set([
    "merge_pr",
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
    print("AI Bug-Fix & Draft-PR Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
