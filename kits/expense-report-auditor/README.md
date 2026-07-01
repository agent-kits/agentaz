# Expense Audit & Compliance Agent

> An expense-audit agent that checks each line against policy, flags out-of-policy items, duplicates, and fraud signals, then approves, holds, or escalates.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Flags a compliant expense or misses a non-compliant one, surfaced for human review. It cannot approve, reject, reimburse, or pay an expense — execution tools are absent.
- **Authority boundary:** Reviews expense reports against policy, flags violations and anomalies, and surfaces them for review. It never approves, rejects, or reimburses. A human in finance decides.
- **Verification test:** Attempt to call an approve, reject, or payment tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: approval/payment tools absent. Human gates: finance decides. Confidence escalation: ambiguous items flagged. Cost ceiling: bounded. Audit trail: flags and policy refs logged. Escalation path: violations routed to finance.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/expense-report-auditor#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/expense-report-auditor
