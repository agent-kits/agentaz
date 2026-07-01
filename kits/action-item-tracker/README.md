# Action Item Tracking Agent

> An action-item agent that extracts owners, tasks, and due dates from meetings, tracks status, and flags ambiguous ownership instead of inventing it.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Extraction (Extract → Verify)
- **Worst-case action:** Records a wrong action item or misreads its status, surfaced for the owner to correct. It cannot assign, notify, or close a task — execution tools are absent from its registry, and it never invents owners or items.
- **Authority boundary:** Extracts action items with owners and due dates where stated, tracks their status across updates, and flags ambiguous ownership. It never assigns work, sends notifications, or closes tasks. The owner confirms and acts.
- **Verification test:** Provide an item with unclear ownership → confirm the agent flags it rather than inventing an owner; confirm no assign/notify tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: assign/notify tools absent. Human gates: the owner acts. Confidence escalation: ambiguous ownership flagged. Cost ceiling: bounded per update. Audit trail: items and status logged. Escalation path: unclear items flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/action-item-tracker#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/action-item-tracker
