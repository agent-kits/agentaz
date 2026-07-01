# Insurance Claims Intake & Triage Agent

> An administrative claims-intake agent: validates FNOL completeness, screens coverage, flags fraud indicators for SIU, and routes. No coverage decisions.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Extraction (Extract → Verify)
- **Worst-case action:** Misclassifies or misroutes a claim, surfaced for human review. It cannot approve, deny, adjust, or pay a claim — execution tools are absent from its registry.
- **Authority boundary:** Intakes a claim, extracts structured data, and triages and routes it for human handling. It never approves, denies, or pays a claim. An adjuster makes every determination.
- **Verification test:** Attempt to call an approve, deny, or payment tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: decision/payment tools absent. Human gates: an adjuster decides. Confidence escalation: low-confidence extractions flagged. Cost ceiling: bounded. Audit trail: extraction and routing logged. Escalation path: complex claims routed to a senior adjuster.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/claims-intake-triager#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/claims-intake-triager
