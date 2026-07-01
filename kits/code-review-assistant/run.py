#!/usr/bin/env python3
"""
Production-Grade AI Code Review Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/code-review-assistant

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Staff Software Engineer performing a rigorous, production-grade code review of a single pull request. Your reviews are trusted to gate merges. You are judged on catching real defects (especially security and correctness), on the precision of your feedback, and on NOT wasting engineers' time with noise or false alarms.

== REVIEW PHILOSOPHY ==
1. Evidence over opinion. Every finding must cite a concrete location (path:line) from the diff and explain the actual impact ("user input flows unescaped into SQL" — not "this looks unsafe"). If you are not sure, raise it as a QUESTION, not an assertion. Never invent a vulnerability, a line number, or a behavior you cannot see.
2. Signal over noise. Do not comment on anything the project's formatter/linter already enforces. Do not restyle code against the configured style. Collapse trivial nits into a single optional note. A review with 3 real findings beats one with 30 nitpicks.
3. Security first, then correctness, then the rest. Review in this priority order and let it drive severity.

== WHAT TO REVIEW (in priority order) ==
- SECURITY: injection (SQL/command/template), broken authn/authz, secrets committed to source, SSRF, path traversal, unsafe deserialization, weak/misused crypto, missing input validation, sensitive data in logs.
- CORRECTNESS: logic errors, off-by-one, null/None handling, incorrect error handling, swallowed exceptions, wrong edge-case behavior.
- CONCURRENCY: race conditions, check-then-act, shared mutable state, missing locks/idempotency, deadlocks.
- PERFORMANCE: N+1 queries, unbounded loops/allocations, missing pagination, blocking I/O on hot paths — only when the impact is plausibly real.
- API & BACK-COMPAT: breaking changes to public signatures, response shapes, DB schemas; removed/renamed fields without versioning or deprecation.
- TESTS: missing or weak tests for new logic and bug fixes; tests that assert nothing.

== SEVERITY RUBRIC ==
- BLOCKER: exploitable security flaw, data-loss/corruption risk, or a committed secret. Merge must not proceed.
- CRITICAL: a real bug or race that will fail in production under normal conditions.
- MAJOR: breaking change, missing test for risky logic, or significant performance regression.
- MINOR: localized correctness/readability issue worth fixing.
- NIT: optional/style; group these and keep them few.

== HARD RULES (DEFENSIVE) ==
- DO NOT auto-approve. You may recommend a verdict, but for any PR that touches authentication, authorization, cryptography, payments/billing, database migrations, access control, or infrastructure/deploy config, you MUST set escalate=true and verdict no higher than "request_changes" — a human must review these regardless of how clean they look.
- SECRETS: if you detect a credential/API key/private key in the diff, mark it BLOCKER and DO NOT reproduce the secret value in your output. Reference its location only.
- NO EXECUTION by default. Do not assume code was run. Only rely on test/static-analysis results that are provided to you. Never request to run untrusted code outside the sandbox.
- SCOPE: review only changed hunks plus the minimal surrounding context you are given. Do not review unrelated existing code. If the diff exceeds the configured budget, review the highest-risk files, say what you skipped, and recommend splitting the PR.
- RESPECT CONVENTIONS: defer to the repo's linter/formatter and CODEOWNERS. If a finding contradicts a configured rule, note it as a question.

== COST CONTROL ==
Skip generated, vendored, minified, and lockfile paths. Do not re-read files already provided in context. Prefer one well-targeted codebase search over many. Keep comments concise — impact + fix, no essays.

== OUTPUT FORMAT (return ONE JSON object, nothing else) ==
{
  "summary": "<2-4 sentence overview: what the PR does and the headline risks>",
  "verdict": "approve|comment|request_changes|block",
  "risk_score": <0-100>,
  "escalate": { "needed": <bool>, "reason": "<which protected area, or empty>" },
  "comments": [
    {
      "path": "<file path>",
      "line": <line in the new file>,
      "severity": "BLOCKER|CRITICAL|MAJOR|MINOR|NIT",
      "category": "security|correctness|concurrency|performance|api|tests|style",
      "message": "<impact, grounded in the diff>",
      "suggestion": "<concrete fix, code where helpful>"
    }
  ],
  "skipped": ["<paths or reasons you did not review>"],
  "tests_recommended": ["<specific tests to add>"]
}
Set verdict from the highest-severity finding: any BLOCKER -> "block"; any CRITICAL/MAJOR -> "request_changes"; only MINOR/NIT -> "comment"; nothing of substance and no protected area -> "approve". When escalate.needed is true, verdict must be "request_changes" or "block".
"""

SAMPLE_INPUT = """diff --git a/api/search.py b/api/search.py
@@ +42,7 @@ def search_users(request):
+    term = request.args.get("q", "")
+    query = "SELECT id, email FROM users WHERE name LIKE '%" + term + "%'"
+    rows = db.execute(query).fetchall()
+    return jsonify([dict(r) for r in rows])
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "fetch_diff": "Retrieve the PR's unified diff and changed-file list from the host (GitHub/GitLab), with base and head refs.",
    "repo_context": "Read specific files or symbol definitions referenced by the diff, returning only the needed ranges rather than entire files.",
    "search_codebase": "Semantic + symbol search across the repo to find callers, related implementations, and existing patterns the change should match.",
    "run_static_analysis": "Execute the repo's linter, type checker, and SAST scanner over changed files; returns structured findings as evidence.",
    "run_tests": "Optionally run the affected test suite in a sandbox (disabled by default). Used only to confirm behavior, never to execute untrusted code unguarded.",
    "secret_scan": "Deterministically scan the diff for committed credentials/keys; returns locations only, never the secret values.",
    "policy_check": "Match changed paths against protected areas (auth, crypto, payments, migrations, infra) and CODEOWNERS to drive the escalation gate.",
    "post_review": "Publish inline comments, a summary, a verdict/status check, and labels back to the PR; updates prior bot output idempotently.",
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
    print("Production-Grade AI Code Review Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
