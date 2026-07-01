# Purchase Order Matching Agent

> A 3-way-match agent that reconciles invoice, PO, and receipt, flags price and quantity variances and duplicates, and approves matches within tolerance or escalates.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an incorrect match or flags a valid one, surfaced for human review. It cannot approve, post, or pay against a purchase order — execution tools are absent from its registry.
- **Authority boundary:** Performs a three-way match across purchase order, receipt, and invoice, and flags discrepancies for review. It never approves a match, posts to a ledger, or releases payment. A human in finance decides.
- **Verification test:** Attempt to call an approve, post, or payment tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: approval/payment tools absent. Human gates: finance decides. Confidence escalation: partial or fuzzy matches flagged. Cost ceiling: bounded per match. Audit trail: matches and discrepancies logged. Escalation path: mismatches routed to AP.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/purchase-order-matcher#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/purchase-order-matcher
