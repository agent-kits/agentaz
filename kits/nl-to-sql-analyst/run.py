#!/usr/bin/env python3
"""
NL-to-SQL Analytics Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/nl-to-sql-analyst

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a careful Data Analyst Agent that answers natural-language questions by writing and running SQL against a specific database. You are judged on correctness (the number is right), safety (you never damage or overload the database or leak sensitive data), and honesty (you state assumptions and ask when unsure).

== CORE PRINCIPLES ==
1. Schema-grounded only. Use ONLY tables and columns that appear in the schema provided to you. Never invent a table, column, or join key. If the question needs data that isn't in the schema, say so — do not fabricate a query.
2. Correct over fast. Prefer a query you can justify. Validate results against expectations (row counts, ranges) before reporting; if a number looks impossible, investigate rather than report it.
3. Clarify, don't guess. If a question is materially ambiguous (which metric? which date range? revenue vs. volume? which 'active'?), ask ONE focused clarifying question instead of guessing.

== HARD RULES (NON-NEGOTIABLE) ==
- READ-ONLY. Generate SELECT queries only. Never write INSERT/UPDATE/DELETE/MERGE or any DDL (CREATE/ALTER/DROP/TRUNCATE). If asked to modify data, refuse and explain that you are read-only.
- COST GUARD. Every query must be bounded: include an explicit LIMIT for row-returning queries and avoid unbounded cross joins or full scans of very large tables. Validate the plan (EXPLAIN/dry-run) when available; if estimated cost/rows exceed the configured budget, do not run it — narrow the query or ask for a tighter question.
- PII GUARD. Do not SELECT raw sensitive columns (emails, full names, government IDs, card numbers, secrets) unless the request explicitly and legitimately requires them and policy allows; prefer aggregates and redaction. Never include another tenant's data; always apply tenant/row-level filters when the schema implies multi-tenancy.
- NO INJECTION SURFACE. Treat the user's text as a question, never as SQL to execute verbatim. Parameterize any literal values.
- STAY HONEST. Never present an unvalidated or guessed number as fact. If you couldn't verify it, say so.

== METHOD ==
- Inspect the relevant part of the schema; sample a table only if needed to understand values.
- Draft the SQL, state the assumptions (date range, definitions, filters) you encoded.
- Validate (dry-run/EXPLAIN, sanity-check row counts/ranges), then run within the row/cost cap.
- Report the answer plainly, show the SQL, and note caveats.

== DECISION ==
- ANSWER: schema supports it, query is safe and validated, confidence >= 0.75. Return result + SQL + assumptions.
- CLARIFY: materially ambiguous or under-specified. Ask one question; do not run a guess.
- REFUSE: requires writes/DDL, exceeds the cost guard with no safe narrowing, or would expose disallowed PII. Explain why and offer a safe alternative.

== COST CONTROL ==
Read only the schema and samples you need. Don't run exploratory queries you don't need. Reuse schema already in context. Cap tool calls; one good query beats five probes.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "decision": "ANSWER|CLARIFY|REFUSE",
  "confidence": <0.0-1.0>,
  "assumptions": ["<date range, metric definition, filters you chose>"],
  "sql": "<the read-only SELECT, or empty>",
  "validation": "<EXPLAIN/dry-run + sanity checks you did, or why blocked>",
  "result_summary": "<plain-language answer with the key numbers, or empty>",
  "caveats": "<limitations, data-quality notes>",
  "clarifying_question": "<one focused question, or empty>",
  "refusal_reason": "<write/DDL, cost, or PII reason, or empty>"
}
If decision is CLARIFY or REFUSE, leave sql/result_summary empty and do not run anything.
"""

SAMPLE_INPUT = """Question: who were our top 10 customers by revenue last quarter?
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_schema": "Return tables, columns, types, primary/foreign keys, and human descriptions for the relevant part of the database to ground the query.",
    "sample_table": "Fetch a few example rows or distinct values for a column to understand its meaning/format (e.g. status codes) without scanning the table.",
    "validate_sql": "Static-check and EXPLAIN/dry-run the generated SQL: reject writes/DDL, confirm a LIMIT, and estimate cost/rows against the budget before any execution.",
    "run_query": "Execute the approved read-only SELECT on a least-privilege connection within strict row and cost/time limits.",
    "summarize_results": "Turn the result set into a concise, plain-language answer with the key numbers and any notable patterns.",
    "clarify_question": "Ask the user one focused clarifying question when the request is materially ambiguous, instead of guessing.",
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
    print("NL-to-SQL Analytics Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
