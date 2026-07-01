# AgentAz™ Specification — v1.0

> **Status:** Frozen (v1.0.0) · **Code & schema:** Apache-2.0 · **This text:** CC-BY-4.0
> **Canonical schema:** https://www.agent-kits.com/agentaz/agentaz-v1.0.schema.json
> **Home:** https://www.agent-kits.com/agentaz-specifications

AgentAz™ is an **open, design-time governance specification** for AI agents. It
is a vocabulary for documenting — before deployment — what an agent is authorized
to do, what the worst thing it can do is, and how it is bounded and escalated. It
is **not** a runtime, framework, or policy engine; it pairs with whatever stack
and controls you already run.

AgentAz is deliberately neutral: any project, framework, or vendor can adopt it
without endorsing AgentKits. The reference implementation and JSON Schema are
openly licensed so the specification can be validated and built upon freely.

## 1. Trust Levels

Agents are classified by **worst-case action**, not typical behavior.

| Level | Meaning                                   |
|-------|-------------------------------------------|
| A0    | No autonomous action                      |
| A1    | Research / read-only                       |
| A2    | Recommend / draft (no side effects)        |
| A3    | Prepare for human approval                  |
| A4    | Execute within a sandbox / reversible scope |
| A5    | Full autonomy                              |

## 2. Required fields

`agent_id`, `version`, `trust_level`, `worst_case_action`, `authority_boundary`,
`tool_boundary`, `last_reviewed`.

## 3. Boundaries

- **tool_boundary** — allowed tools, whether execution tools are absent, and
  approval-required actions.
- **output_boundary** — constraints on what the agent may emit.
- **cost_boundary** — maximum spend per trace/loop.
- **loop_boundary** — maximum reasoning turns.
- **human_handoff** — escalation triggers and destination.
- **audit** — append-only logging requirements.

## 4. Versioning

AgentAz follows Semantic Versioning. **v1.0 is frozen**: no breaking changes
within the 1.x line; breaking changes ship as 2.0. See `CHANGELOG.md`.

## 5. Licensing & marks

- Source code and the JSON Schema: **Apache License 2.0** (`LICENSE`).
- This specification text and documentation: **CC-BY-4.0** (`LICENSE-CONTENT`).
- **AgentAz™** and **AgentKits** are trademarks of AgentKits. Open licensing of
  the code and text does not grant rights to the names or marks, except for
  reasonable descriptive use.

## 6. Reference implementation

The 12 flagship blueprints are the canonical reference set for AgentAz v1.0. All
60 blueprints ship a complete AgentAz spec. Source:
https://github.com/agent-kits/agentaz
