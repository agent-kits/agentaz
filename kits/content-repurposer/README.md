# Content Repurposing Agent

> A content-repurposing agent that turns one source into posts, emails, and threads while preserving its facts and brand voice — never fabricating stats, quotes, or claims.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an off-base or inaccurate repurposed draft that a human reviews before publishing. It cannot publish or post to any channel — publishing tools are absent from its registry, and it never invents facts not in the source.
- **Authority boundary:** Takes a source piece and repurposes it into other formats, staying faithful to the source's facts and claims. A human reviews and publishes. It never publishes autonomously and never adds claims that aren't in the source.
- **Verification test:** Confirm repurposed drafts add no claims absent from the source; confirm no publish/post tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish tools absent. Human gates: a human publishes. Confidence escalation: claims not in source flagged. Cost ceiling: bounded per piece. Audit trail: drafts logged. Escalation path: ambiguous source material flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/content-repurposer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/content-repurposer
