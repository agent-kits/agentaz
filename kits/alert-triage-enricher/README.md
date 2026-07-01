# AI SOC Alert Triage Agent

> A SOC tier-1 agent that enriches and correlates alerts, scores severity with MITRE mapping, and recommends contain, dismiss, or escalate — never auto-containing blindly.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Mis-prioritizes a security alert or stages an inappropriate remediation that a human reviews before it runs. Any remediation is verified-low-risk and requires human approval; it cannot execute a remediation on its own.
- **Authority boundary:** Enriches, deduplicates, and prioritizes alerts, and may stage a verified low-risk remediation for human approval. It never executes remediation autonomously and never changes production on its own. A responder approves any action.
- **Verification test:** Stage a remediation → confirm it requires explicit human approval and is not auto-executed; confirm high-risk actions are gated.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: remediation gated behind approval. Human gates: responder approves any action. Confidence escalation: low-confidence alerts routed up. Cost ceiling: bounded. Audit trail: enrichment and decisions logged. Escalation path: high-severity routed to on-call.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/alert-triage-enricher#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/alert-triage-enricher
