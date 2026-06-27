# Product Catalog Enrichment Agent

> A catalog agent that enriches product descriptions, attributes, and categories from your source data, flags missing specs for review, and never fabricates claims.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Proposes an incorrect enrichment that a human reviews before it reaches the catalog. It cannot write to the catalog and never fabricates a spec or claim — it enriches only from provided source data, flagging low-confidence fields.
- **Authority boundary:** Enriches product records strictly from provided source data — normalizing attributes, filling gaps it can support — and flags low-confidence fields. It never fabricates specs, certifications, or marketing claims, and never writes to the catalog. A human approves before publish.
- **Verification test:** Confirm enrichments cite source data and unsupported fields are left blank/flagged, not invented; confirm no catalog-write tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: catalog-write tools absent. Human gates: a human approves before publish. Confidence escalation: low-confidence fields flagged. Cost ceiling: bounded per product. Audit trail: enrichments and sources logged. Escalation path: unsupported claims flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/product-catalog-enricher#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/product-catalog-enricher
