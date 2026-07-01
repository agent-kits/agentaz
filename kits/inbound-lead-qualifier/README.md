# Inbound Lead Qualification Agent

> An inbound-lead agent that qualifies and scores leads against your ICP from real data, routes hot ones to sales, and never fabricates firmographics or intent.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Produces an inaccurate lead score or qualification, surfaced for a rep to review. It cannot email a lead, write to a CRM, or take any action — execution tools are absent from its registry.
- **Authority boundary:** Reads inbound lead information, scores it against your qualification criteria, and surfaces a recommendation with reasoning. It never contacts the lead, writes to a CRM, or routes autonomously. A rep decides and acts.
- **Verification test:** Attempt to call an email-lead or CRM-write tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: contact/CRM-write tools absent. Human gates: a rep decides. Confidence escalation: borderline leads flagged. Cost ceiling: bounded per lead. Audit trail: score and reasoning logged. Escalation path: high-value or ambiguous leads flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/inbound-lead-qualifier#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/inbound-lead-qualifier
