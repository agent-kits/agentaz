# Workflow Routing Agent

> A routing agent that classifies incoming requests and sends them to the right workflow with a confidence and reason, escalating ambiguous or high-risk ones to humans.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Routes a request to the wrong handler, caught before anything runs. It only routes and does not execute the work itself — execution tools are absent from its registry.
- **Authority boundary:** Reads an incoming request, classifies it, and routes it to the appropriate handler or queue with a confidence score. It never performs the downstream work and never executes actions. The receiving handler does the work.
- **Verification test:** Confirm the agent emits a routing decision only and does not execute the routed task; confirm no execution tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: execution tools absent. Human gates: handlers do the work. Confidence escalation: low-confidence routes sent to a default/human queue. Cost ceiling: bounded per request. Audit trail: routing decisions logged. Escalation path: unclassifiable requests routed to triage.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/workflow-router#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/workflow-router
