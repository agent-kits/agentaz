# Supply Chain Disruption Monitor

> A supply-chain monitor that detects disruptions from real sourced signals, rates severity and confidence, and recommends actions for approval without acting on its own.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Raises a false disruption alert or misses one, surfaced for a human to assess. It cannot reroute, reorder, or change a supplier or shipment — execution tools are absent from its registry.
- **Authority boundary:** Monitors signals for supply-chain disruptions, assesses likely impact, and surfaces prioritized alerts for review. It never reroutes shipments, places orders, or changes suppliers. A planner decides on any response.
- **Verification test:** Attempt to call a reorder, reroute, or supplier-change tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: action tools absent. Human gates: a planner decides. Confidence escalation: uncertain signals flagged, not acted on. Cost ceiling: bounded per scan. Audit trail: signals and assessments logged. Escalation path: high-impact disruptions surfaced first.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/disruption-monitor#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/disruption-monitor
