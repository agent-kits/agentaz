# Invoice Data Extraction Agent

> An invoice-extraction agent that parses invoices into validated JSON with per-field confidence, validates totals, and flags illegible or mismatched fields for review.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Extraction (Extract → Verify)
- **Worst-case action:** Extracts an incorrect field value, surfaced with a low-confidence flag for human review. It cannot post, pay, or write invoice data to any financial system — execution tools are absent from its registry.
- **Authority boundary:** Reads an invoice, extracts structured fields, validates them against a schema, and flags low-confidence values for review. It never posts to a ledger, pays, or writes to financial systems. A human verifies before any downstream use.
- **Verification test:** Attempt to call a ledger-write, payment, or post tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: payment/post tools absent. Human gates: a human verifies before use. Confidence escalation: low-confidence fields flagged. Cost ceiling: bounded per document. Audit trail: extracted fields and confidence logged. Escalation path: low-confidence extractions routed to review.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/invoice-extractor#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/invoice-extractor
