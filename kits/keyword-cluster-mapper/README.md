# Keyword Cluster Mapping Agent

> An SEO agent that clusters your keywords into topic groups and maps intent, never fabricates search metrics, and never guarantees rankings.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces a flawed keyword clustering that a human reviews before acting on. It computes clusters only from provided data, never fabricates search-volume or difficulty metrics, and never guarantees rankings; execution tools are absent.
- **Authority boundary:** Clusters keywords by intent and similarity from provided data, labels metrics it was given, and surfaces the mapping for review. It never invents search metrics, never guarantees rankings, and never publishes or takes action. A human decides.
- **Verification test:** Confirm metrics come from provided data (not invented) and no ranking is guaranteed; confirm no publish/action tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish/action tools absent. Human gates: a human decides. Confidence escalation: ambiguous intent flagged. Cost ceiling: bounded per set. Audit trail: clusters and inputs logged. Escalation path: thin data flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/keyword-cluster-mapper#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/keyword-cluster-mapper
