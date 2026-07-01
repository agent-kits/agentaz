# Goal Decomposition & Planning Agent

> A planning agent that decomposes a goal into an ordered, dependency-mapped subtask plan, gating irreversible steps. It plans and validates; it never auto-executes.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Produces a flawed plan or subtask breakdown that a human reviews before acting on. It never auto-executes any step — it proposes a plan and stops; execution tools are absent from its registry.
- **Authority boundary:** Takes a goal and decomposes it into an ordered plan of subtasks with dependencies, surfaced for human review. It never executes a step, calls downstream tools, or commits resources. A human approves and runs the plan.
- **Verification test:** Confirm the agent outputs a plan only and does not execute any subtask; confirm no execution tool exists in its registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: execution tools absent. Human gates: a human approves and runs. Confidence escalation: ambiguous goals clarified, not assumed. Cost ceiling: bounded per plan. Audit trail: plan and rationale logged. Escalation path: under-specified goals flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/goal-decomposer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/goal-decomposer
