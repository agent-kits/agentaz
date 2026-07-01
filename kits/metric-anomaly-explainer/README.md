# Metric Anomaly Investigation Agent

> An analytics agent that confirms a metric anomaly is real, localizes it by segment, and ranks evidence-backed hypotheses — correlation vs. causation, data-quality aware.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Proposes a wrong explanation for a metric movement that an analyst reviews before acting on. It runs read-only analysis only and cannot change data, dashboards, or take action — write tools are absent from its registry.
- **Authority boundary:** Investigates a metric anomaly across read-only data, forms and ranks likely explanations with supporting evidence, and flags uncertainty. It never asserts a single cause as fact, changes data, or takes action. An analyst confirms.
- **Verification test:** Confirm explanations are ranked hypotheses with evidence, not asserted certainties; confirm no data-write tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: read-only; write tools absent. Human gates: an analyst confirms. Confidence escalation: competing hypotheses surfaced. Cost ceiling: bounded per investigation. Audit trail: hypotheses and evidence logged. Escalation path: inconclusive cases flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/metric-anomaly-explainer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/metric-anomaly-explainer
