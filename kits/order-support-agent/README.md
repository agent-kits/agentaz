# E-commerce Order Support Agent

> An e-commerce support agent that verifies the customer, answers order questions, processes returns and refunds within policy caps, and escalates disputes.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Drafts an incorrect order reply or misreads order status, caught before a human sends. It cannot cancel, refund, modify an order, or send autonomously — those tools are absent from its registry.
- **Authority boundary:** Looks up order status read-only, drafts a suggested reply, and routes or escalates. A human sends and takes any account action. It never cancels, refunds, modifies orders, or sends on its own.
- **Verification test:** Attempt to call a cancel-order, refund, or send tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: order-action/send tools absent. Human gates: a human sends and acts. Confidence escalation: sensitive or uncertain cases escalated. Cost ceiling: bounded per ticket. Audit trail: lookups and drafts logged. Escalation path: account actions routed to an agent.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/order-support-agent#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/order-support-agent
