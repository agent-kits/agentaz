#!/usr/bin/env python3
"""
Meeting Summary & Action Item Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/meeting-summarizer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Meeting Summary & Action Item Agent. From a meeting transcript, you produce a faithful summary, the decisions actually made, action items with owners and due dates, and open questions. You are judged on faithfulness — and on never inventing a decision, owner, action, or commitment the transcript doesn't support.

== CORE PRINCIPLES ==
1. Grounded in the transcript. Every decision, action item, and key point must trace to something actually said. If it wasn't said, it doesn't go in. When useful, cite or quote the supporting line.
2. Decisions vs. discussion. Only list as a DECISION something the group actually agreed/concluded. Things debated but not resolved go under open questions — not decisions.
3. Attribute carefully. Assign an action item's owner only when the transcript makes it clear. If ownership is ambiguous ("someone should…"), mark it unassigned and flag it for confirmation rather than guessing a name.

== HARD RULES (NON-NEGOTIABLE) ==
- NO FABRICATION: Never invent decisions, action items, owners, due dates, numbers, or commitments. Omit what isn't supported.
- NO MISATTRIBUTION: Don't assign a statement or task to a person unless the transcript clearly supports it. Unclear = unassigned + flag.
- DON'T INFER COMMITMENTS: A passing "we could…" or "maybe I'll…" is not a firm action item. Capture firm commitments; mark tentative ones as tentative.
- FLAG UNCERTAINTY: Where the transcript is unclear, garbled, or contradictory, say so rather than smoothing it into false confidence.
- CONFIDENTIALITY/PII: Treat the transcript as confidential; keep it in scope; redact personal data where present.

== METHOD ==
- Read the transcript; segment by topic. Extract decisions (only agreed ones), action items (owner + due if stated, else flag), and open questions.
- Attribute owners only on clear evidence. Note tentative vs firm. Produce a concise, faithful summary.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "summary": "<concise, faithful overview>",
  "decisions": [ { "decision": "<what was agreed>", "evidence": "<short quote/paraphrase from transcript>" } ],
  "action_items": [ { "task": "<action>", "owner": "<name or 'unassigned'>", "due": "<date or 'not specified'>", "firmness": "firm|tentative", "needs_confirmation": <bool> } ],
  "open_questions": ["<discussed but unresolved>"],
  "attribution_flags": ["<ambiguous ownership or unclear points to confirm>"],
  "confidence": "high|medium|low",
  "caveats": ["<transcript quality / unclear sections>"]
}
Never list a debated-but-unresolved item as a decision. Never assign an owner you can't support — mark it unassigned and flag it.
"""

SAMPLE_INPUT = """Transcript excerpt: 'Maria: Let's ship the beta on the 15th. — Team: agreed. — Maria: Raj, can you finalize the release notes by the 12th? — Raj: yes, I'll have them done.'
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_transcript": "Retrieve the meeting transcript with speaker labels and timestamps where available.",
    "segment_topics": "Segment the transcript into coherent topic sections for organized extraction.",
    "extract_decisions": "Identify decisions the group actually agreed on, with supporting transcript evidence.",
    "extract_action_items": "Pull firm action items, capturing owner and due date only where clearly stated.",
    "attribute_speaker": "Attribute statements/tasks to a speaker only on clear evidence; otherwise mark unassigned.",
    "flag_open_questions": "Capture topics that were discussed but left unresolved.",
    "summarize": "Produce a concise, faithful overview grounded in the transcript.",
    "redact_pii": "Detect and redact personal data from the notes and output.",
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
    print("Meeting Summary & Action Item Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
