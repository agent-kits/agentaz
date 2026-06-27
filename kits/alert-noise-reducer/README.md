# Alert Noise Reduction Agent

> An alert-tuning agent that scores alerts by actionability, dedupes, and time-box-suppresses proven noise — never silencing an alert tied to a real incident.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Recommends suppressing or grouping an alert that actually mattered, surfaced for review. It cannot silence, suppress, or close alerts on its own — execution tools are absent and critical alerts are never auto-suppressed.
- **Authority boundary:** Clusters and deduplicates alerts and recommends suppression or grouping rules for human approval. It never silences, suppresses, or closes alerts autonomously, and it never proposes suppressing a critical-severity alert. An engineer approves any rule.
- **Verification test:** Attempt to auto-suppress an alert → confirm suppression requires human approval and critical alerts are excluded; confirm no silence tool runs autonomously.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: suppression requires approval. Human gates: an engineer approves rules. Confidence escalation: uncertain groupings flagged. Cost ceiling: bounded per batch. Audit trail: groupings and recommendations logged. Escalation path: critical alerts always surfaced.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/alert-noise-reducer#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/alert-noise-reducer
