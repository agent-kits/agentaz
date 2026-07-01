# AI Customer Support Agent

> An AI support agent that grounds in your KB and CRM, then resolves, drafts, routes, or escalates — with confidence thresholds, refund caps, and human review.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Drafts an incorrect reply or misroutes a ticket, caught before a human sends or acts. It cannot send messages on its own, and it cannot take account actions such as refunds, cancellations, or data changes — those tools are absent from its registry.
- **Authority boundary:** Reads an incoming ticket, classifies and prioritizes it, drafts a suggested reply, and routes or escalates it. A human sends the reply and takes any account action. It never sends autonomously and never refunds, cancels, or modifies an account.
- **Verification test:** Attempt to call a send-message, refund, or account-change tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send/account-action tools absent. Human gates: a human sends and acts. Confidence escalation: low-confidence or sensitive tickets escalated. Cost ceiling: bounded per ticket. Audit trail: classification, draft, and routing logged. Escalation path: sensitive issues routed to an agent.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/support-triage-router#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/support-triage-router
