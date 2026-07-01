# Phishing Triage & Response Agent

> A phishing-triage agent that enriches reported emails, sandbox-detonates indicators, scopes campaigns, and quarantines, blocks, or escalates BEC — approval-gated.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Stages an incorrect containment action (such as a quarantine) that an analyst approves before it runs, or misclassifies a reported email. It cannot quarantine, block, or delete on its own — those actions require human approval.
- **Authority boundary:** Analyzes a reported email, extracts indicators, scores risk, and stages a recommended containment action for analyst approval. It never quarantines, blocks senders, or deletes mail autonomously. An analyst approves any action.
- **Verification test:** Stage a containment action → confirm it requires explicit analyst approval and is not auto-executed; confirm destructive actions are gated.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: containment actions gated behind approval. Human gates: an analyst approves. Confidence escalation: uncertain verdicts routed up. Cost ceiling: bounded per report. Audit trail: indicators and decisions logged. Escalation path: confirmed threats routed to the SOC.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/phishing-report-analyzer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/phishing-report-analyzer
