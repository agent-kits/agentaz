# Account Research Agent

> A sales-research agent that builds a cited account brief — firmographics, tech stack, triggers, key people — flags stale data, and never fabricates contacts or triggers.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A1 — Research
- **DNA pattern:** Research (Research → Verify)
- **Worst-case action:** Includes a wrong or stale fact in an account brief that a human reviews before acting on. It cannot send outreach, write to a CRM, or take any action — it only gathers and cites, and it never fabricates contacts or signals.
- **Authority boundary:** Gathers firmographics, tech stack, triggers, and key people into a cited brief, and flags stale or low-confidence data. It never sends messages, writes to a CRM, or takes action. It does not invent contacts or buying signals.
- **Verification test:** Confirm the agent cites every fact and flags unverifiable ones rather than asserting them; confirm no send or CRM-write tool exists in its registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send/CRM-write tools absent. Human gates: a rep reviews and acts. Confidence escalation: stale or unverifiable facts flagged. Cost ceiling: bounded per account. Audit trail: sources and citations logged. Escalation path: thin or conflicting data flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/account-research-agent#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/account-research-agent
