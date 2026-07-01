# Competitive Intelligence Digest Agent

> A competitive-intel agent that builds a cited digest of competitor moves from public sources, separates fact from rumor, and never fabricates or uses non-public data.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A1 — Research
- **DNA pattern:** Research (Research → Verify)
- **Worst-case action:** Includes a wrong or stale fact in a competitive digest that a human reviews before acting on. It only gathers and cites public information; it never fabricates and never takes any action.
- **Authority boundary:** Gathers competitive signals from sources, cites each one, and assembles a digest, flagging stale or unverifiable items. It never sends, publishes, or acts, and it never invents a competitor claim or metric.
- **Verification test:** Confirm every claim is cited and unverifiable ones are flagged rather than asserted; confirm no publish/send tool exists in its registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish/send tools absent. Human gates: a human reviews and acts. Confidence escalation: stale or unverifiable items flagged. Cost ceiling: bounded per digest. Audit trail: sources and citations logged. Escalation path: conflicting sources flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/competitive-intel-digest#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/competitive-intel-digest
