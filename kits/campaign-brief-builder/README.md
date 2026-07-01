# Campaign Brief Builder Agent

> A marketing agent that builds a structured campaign brief from your inputs, flags assumptions and missing data, and never fabricates audience stats or guarantees results.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces a brief with a flawed assumption that a marketing lead reviews before acting on. It cannot launch, commit budget, or take action, it labels missing inputs rather than inventing them, and it never fabricates audience stats or guarantees results.
- **Authority boundary:** Builds a structured campaign brief grounded in the inputs provided, marks missing inputs and KPIs as TBD, and flags assumptions and decisions for a marketing lead. It never fabricates audience data or benchmarks, never guarantees results, and never commits budget. A lead approves.
- **Verification test:** Confirm missing data is marked TBD rather than invented and results are never guaranteed; confirm no launch/budget-commit tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: launch/commit tools absent. Human gates: a marketing lead approves. Confidence escalation: assumptions and decisions surfaced. Cost ceiling: bounded per brief. Audit trail: inputs and assumptions logged. Escalation path: missing inputs flagged as TBD.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/campaign-brief-builder#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/campaign-brief-builder
