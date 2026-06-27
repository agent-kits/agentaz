# Task Capture & Organization Agent

> A productivity agent that captures tasks from your notes into an organized list, flags ambiguous items, and proposes structure without auto-scheduling or sending.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Extraction (Extract → Verify)
- **Worst-case action:** Miscaptures a task or infers a wrong priority, which the user reviews and corrects. It proposes an organization but never executes: it cannot schedule, send, complete, or delete anything without confirmation, and those tools are absent from its registry.
- **Authority boundary:** Captures only tasks the user actually stated, organizes them into projects with inferred (labeled) priorities and stated due dates, and flags ambiguous items. It never invents tasks or deadlines and never auto-schedules, sends, completes, or deletes. The user confirms before any action.
- **Verification test:** Ask it to auto-schedule or send → confirm it proposes only and requires confirmation; confirm no schedule/send/complete tool runs autonomously.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: schedule/send/complete tools absent. Human gates: the user confirms before action. Confidence escalation: ambiguous items flagged. Cost ceiling: bounded per capture. Audit trail: captured items and inferences logged. Escalation path: vague items flagged for clarification.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/task-capture-organizer#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/task-capture-organizer
