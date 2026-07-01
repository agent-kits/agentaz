# Real Estate Listing Description Agent

> A listing agent that writes accurate property descriptions from provided facts — Fair-Housing compliant, never fabricating features or using discriminatory language.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Writes an inaccurate or non-compliant listing description that an agent reviews before publishing. It writes only from provided property facts, stays Fair Housing compliant, never invents features, and cannot publish — those tools are absent from its registry.
- **Authority boundary:** Writes a property listing description strictly from provided facts, in Fair-Housing-compliant language that describes the property and not the buyer. A licensed agent reviews and publishes. It never invents features, never uses discriminatory or steering language, and never publishes.
- **Verification test:** Confirm the description uses only provided facts and Fair-Housing-compliant language; confirm no publish tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish tools absent. Human gates: a licensed agent publishes. Confidence escalation: unverifiable claims flagged. Cost ceiling: bounded per listing. Audit trail: description and facts logged. Escalation path: potential compliance issues flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/listing-description-writer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/listing-description-writer
