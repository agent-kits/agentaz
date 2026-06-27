# Daily Planning Agent

> A daily-planning agent that turns your tasks and calendar into a realistic time-blocked plan with breaks, flags overcommitment, and never edits your calendar.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Proposes a suboptimal daily schedule that the user reviews and adjusts. It proposes only and cannot book, schedule, send, or block calendar time without confirmation — those tools are absent from its registry.
- **Authority boundary:** Takes the user's tasks and constraints and proposes a prioritized daily plan. The user confirms. It never books meetings, blocks calendar time, sends invites, or schedules anything autonomously.
- **Verification test:** Ask it to block the calendar → confirm it proposes only and requires confirmation; confirm no calendar-write tool runs autonomously.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: calendar-write tools absent. Human gates: the user confirms. Confidence escalation: conflicts and overcommitment flagged. Cost ceiling: bounded per plan. Audit trail: plan and inputs logged. Escalation path: infeasible plans flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/daily-planner-agent#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/daily-planner-agent
