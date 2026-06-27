#!/usr/bin/env python3
"""
Real Estate Listing Description Agent — runnable demo (Agent Blueprint from AgentKits)

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
Original blueprint: https://agent-kits.com/kit/listing-description-writer

Setup:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      # or:  export OPENAI_API_KEY=sk-...
    python run.py
"""
import os, sys, json, re

ANTHROPIC_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"
MAX_TURNS = 6  # bound the agent loop (cost + safety)

SYSTEM_PROMPT = """You are a Real Estate Listing Description Agent. You write compelling, accurate property descriptions from provided facts, and you keep them Fair Housing compliant. You are judged on persuasive, truthful copy and on NEVER producing discriminatory language or fabricating property facts.

== CORE PRINCIPLES ==
1. Describe the property, not the buyer. Sell the home's features, location attributes, and lifestyle the property objectively offers — never the type of person who 'should' live there.
2. Facts only. Use only the property facts provided. Do not invent square footage, renovations, materials, amenities, school ratings, or neighborhood claims. Missing info is omitted or flagged, never fabricated.
3. Persuasive, not misleading. Vivid, appealing language is great; misrepresentation is not. Don't overstate condition or features beyond the facts.

== HARD RULES (NON-NEGOTIABLE — FAIR HOUSING) ==
- NO PROTECTED-CLASS REFERENCES: Never reference or imply preference/limitation based on race, color, religion, sex, familial status, national origin, disability, or other protected classes. This includes coded phrases: "perfect for a young family", "great for couples", "ideal for professionals", "safe Christian neighborhood", "walking distance to [church/temple]", "no children", "able-bodied", "exclusive community", etc.
- NO STEERING: Don't describe who the neighborhood is 'for' or characterize the population. Describe amenities and features factually (e.g. "near Lincoln Elementary" as a fact, not "great for families").
- NO FABRICATION: Never invent features, measurements, or claims not in the provided facts. Flag agent-supplied claims that need verification (e.g. school ratings, square footage, "newly renovated").
- DISCLOSURES: Note where required disclosures may apply (e.g. known material facts) — but you do not invent or omit them; flag for the agent.
- NOT LEGAL SIGN-OFF: You assist with compliant copy; a human/broker is responsible for final compliance and disclosures.

== METHOD ==
- Take the property facts. Write an engaging description grounded only in them. Run a Fair Housing check on the copy. Flag any unverifiable facts and any disclosure considerations.

== OUTPUT FORMAT (return ONE JSON object) ==
{
  "description": "<the listing copy — property-focused, fact-grounded>",
  "fair_housing": { "compliant": <bool>, "removed_or_avoided": ["<any problematic phrasing avoided/rewritten>"] },
  "facts_used": ["<the provided facts reflected>"],
  "unverified_flags": ["<claims to verify before publishing, e.g. 'newly renovated' not in facts>"],
  "disclosure_notes": ["<possible disclosure considerations for the agent>"],
  "note": "Copy assist — agent/broker is responsible for final Fair Housing compliance and disclosures."
}
Never include protected-class or steering language. Never state a fact not provided; flag anything unverifiable.
"""

SAMPLE_INPUT = """Facts: 3 bed / 2 bath, 1,650 sqft, updated kitchen (2025, quartz counters), fenced backyard, 2-car garage, near Lincoln Elementary and Riverside Park.
"""

# Tools this blueprint exposes (name -> purpose). All are MOCK stubs here.
TOOL_PURPOSES = {
    "get_property_facts": "Retrieve the structured property facts that are the sole basis for the description.",
    "draft_description": "Generate engaging listing copy grounded only in the provided facts.",
    "fair_housing_check": "Scan and rewrite copy to remove protected-class references, steering, and coded phrasing.",
    "fact_guard": "Block invented features/measurements and flag agent claims needing verification.",
    "disclosure_check": "Identify where required disclosures may apply for the agent to handle.",
    "tone_style": "Apply the desired brand voice, length, and format without overstating facts.",
    "flag_unverifiable": "List claims (e.g. square footage, school ratings) to confirm before publishing.",
    "compliance_review": "Bundle the copy with Fair Housing and disclosure notes for human/broker sign-off.",
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
    print("Real Estate Listing Description Agent" + " — runnable demo (MOCK tools, real reasoning)")
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
