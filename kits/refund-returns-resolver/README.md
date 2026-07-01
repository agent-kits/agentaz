# Refund & Returns Resolution Agent

> A refund and returns agent that checks eligibility against policy, approves within caps, detects abuse, and escalates out-of-policy and disputed cases to humans.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Prepares an incorrect refund or return decision that a human reviews before it is issued. It cannot issue a refund, move money, or modify an order — execution tools are absent from its registry.
- **Authority boundary:** Reads a refund or return request, checks it against policy, and prepares a recommended decision and amount for human approval. It never issues a refund, moves money, or changes an order. An agent approves and executes within policy.
- **Verification test:** Attempt to call an issue-refund, payment, or order-modify tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: refund/payment tools absent. Human gates: approval required before any refund. Confidence escalation: out-of-policy or high-value cases flagged. Cost ceiling: bounded per request. Audit trail: policy check and recommendation logged. Escalation path: exceptions routed to a supervisor.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/refund-returns-resolver#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/refund-returns-resolver
