# PRD Drafting Agent

> A PRD agent that drafts a product requirements doc from your notes, flags assumptions and open questions, and never fabricates user research or success metrics.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces a weak or incomplete PRD draft that a human reviews and revises. It cannot publish, assign, or commit anything — it drafts grounded in the inputs and execution tools are absent from its registry.
- **Authority boundary:** Takes provided inputs and drafts a structured PRD — problem, goals, scope, requirements — grounded in those inputs, flagging assumptions and open questions. It never publishes, assigns work, or invents requirements. A PM reviews and owns the document.
- **Verification test:** Confirm the draft marks assumptions and open questions rather than inventing requirements; confirm no publish/assign tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: publish/assign tools absent. Human gates: a PM owns the doc. Confidence escalation: gaps flagged as open questions. Cost ceiling: bounded per draft. Audit trail: draft and assumptions logged. Escalation path: missing inputs flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/prd-drafter#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/prd-drafter
