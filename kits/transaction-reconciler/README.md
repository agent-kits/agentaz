# Transaction Reconciliation Agent

> A reconciliation agent that matches bank and ledger transactions, flags unmatched items and discrepancies for review, and never force-matches or auto-adjusts the books.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Surfaces an incorrect reconciliation result or a mislabeled discrepancy for a human to review. It cannot post, edit, or delete a ledger entry, and it cannot move money — execution tools are absent from its registry.
- **Authority boundary:** Reads two sources (bank + ledger), matches transactions, and flags unmatched items, discrepancies, and duplicates for human review. It never force-matches, never inserts a balancing entry, and never writes to financial systems. All adjustments and sign-off remain with a human.
- **Verification test:** Attempt to call a ledger-write or post-adjustment tool → confirm it is absent from the agent's tool registry (not merely disabled).
- **Production readiness:** 6/6 dimensions passing. Tool isolation: execution tools absent. Human gates: all adjustments human-owned. Confidence escalation: per-match confidence routes low-confidence pairs to review. Cost ceiling: bounded per reconciliation. Audit trail: every match and flag logged. Escalation path: discrepancies routed to an accountant.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/transaction-reconciler#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/transaction-reconciler
