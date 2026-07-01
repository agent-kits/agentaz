# Company Policy Q&A Agent

> A policy Q&A agent that answers employee questions only from the official handbook with citations, flags what isn't covered, and routes sensitive HR matters to a human.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Gives an incorrect answer about company policy that the asker can verify against the cited source. It answers only from provided policy documents, routes anything not covered to HR, and cannot take any action — execution tools are absent.
- **Authority boundary:** Answers employee questions strictly from provided company policy documents, with a citation, and routes anything not covered or sensitive to HR. It never invents a policy, makes an exception, or takes action. HR owns interpretation and decisions.
- **Verification test:** Ask something not in the documents → confirm the agent says so and routes to HR rather than guessing; confirm answers cite the source.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: action tools absent. Human gates: HR owns decisions. Confidence escalation: uncovered or sensitive questions routed to HR. Cost ceiling: bounded per question. Audit trail: answers and citations logged. Escalation path: not-in-docs routed to HR.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/policy-qa-agent#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/policy-qa-agent
