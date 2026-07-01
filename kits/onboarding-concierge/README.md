# Onboarding Concierge Agent

> An onboarding agent that answers new-hire questions from your company docs with citations, tracks the checklist, and escalates HR-sensitive questions to humans.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Gives a wrong answer to a new hire that they can verify against the cited source. It answers only from provided onboarding documents, routes HR-sensitive or uncovered questions to a human, and cannot take any action or make commitments — execution tools are absent.
- **Authority boundary:** Answers new-hire questions strictly from provided onboarding and company documents, with citations, and tracks the onboarding checklist. It routes HR-sensitive, personal, or uncovered questions to a human. It never invents policy, makes commitments on the company's behalf, or takes action.
- **Verification test:** Ask an HR-sensitive or not-in-docs question → confirm the agent routes it to a human rather than answering; confirm answers cite the source and no action tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: action tools absent. Human gates: HR owns sensitive matters. Confidence escalation: HR-sensitive and uncovered questions escalated. Cost ceiling: bounded per question. Audit trail: answers and citations logged. Escalation path: sensitive or unknown routed to HR.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/onboarding-concierge#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/onboarding-concierge
