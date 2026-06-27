# SEO Content Brief Agent

> An SEO brief agent that builds content briefs from real SERP analysis — intent, structure, subtopics, questions — without fabricating metrics or promising rankings.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces a weak or off-target SEO content brief that a human reviews before use. It works from provided data, never guarantees rankings, and cannot publish or take action — those tools are absent from its registry.
- **Authority boundary:** Generates a structured SEO content brief — intent, outline, entities, internal links — grounded in provided data. A human reviews and writes. It never guarantees rankings, fabricates metrics, or publishes.
- **Verification test:** Confirm the brief makes no ranking guarantee and uses provided data; confirm no publish tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish tools absent. Human gates: a human writes and publishes. Confidence escalation: thin data flagged. Cost ceiling: bounded per brief. Audit trail: brief and inputs logged. Escalation path: unclear intent flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/seo-brief-generator#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/seo-brief-generator
