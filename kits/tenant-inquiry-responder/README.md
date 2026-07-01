# Tenant Inquiry Response Agent

> A real-estate agent that answers tenant inquiries from your listing data, follows Fair Housing rules, drafts replies without committing, and escalates emergencies.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Drafts a wrong answer to a tenant inquiry, caught before a human sends. It answers only from the listing and policy, stays Fair Housing compliant, escalates emergencies and legal matters, and cannot send or take account actions — those tools are absent from its registry.
- **Authority boundary:** Answers prospective- and current-tenant inquiries from the listing and provided policy, in Fair-Housing-compliant language, and drafts replies for a human to send. It escalates emergencies, maintenance, and legal or discrimination-sensitive matters to a human. It never sends, makes commitments, or takes account actions.
- **Verification test:** Send an emergency or Fair-Housing-sensitive inquiry → confirm it escalates to a human rather than answering; confirm no send/account-action tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send/account-action tools absent. Human gates: a human sends and acts. Confidence escalation: emergencies and sensitive matters escalated immediately. Cost ceiling: bounded per inquiry. Audit trail: drafts and routing logged. Escalation path: emergencies/legal routed to property management.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/tenant-inquiry-responder#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/tenant-inquiry-responder
