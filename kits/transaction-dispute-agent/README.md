# Payment Dispute & Chargeback Agent

> A card-dispute agent: classifies reason codes, weighs friendly fraud vs. true fraud, and refunds, represents, or escalates — within network rules and refund caps.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Assembles an incorrect dispute case or recommended decision that a human reviews before action. It cannot file a chargeback, move money, or close a dispute — execution tools are absent from its registry.
- **Authority boundary:** Gathers evidence across sources, assembles the dispute case, and recommends a decision for human approval. It never files a chargeback, issues a refund, moves money, or closes the case. A human approves and acts.
- **Verification test:** Attempt to call a chargeback-file, refund, or money-movement tool → confirm it is absent from the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: filing/payment tools absent. Human gates: approval required before any action. Confidence escalation: weak evidence flagged. Cost ceiling: bounded. Audit trail: evidence and recommendation logged. Escalation path: disputes routed to a specialist.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/transaction-dispute-agent#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/transaction-dispute-agent
