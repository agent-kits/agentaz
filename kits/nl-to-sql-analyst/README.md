# NL-to-SQL Analytics Agent

> A schema-grounded analytics agent that turns plain-English questions into safe, read-only SQL — cost-guarded, PII-aware, and clarifying ambiguity instead of guessing.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A1 — Research
- **DNA pattern:** Research (Research → Verify)
- **Worst-case action:** Runs an incorrect read-only query and returns wrong figures for a human to interpret. It cannot insert, update, delete, or alter data — only read-only queries are permitted and write tools are absent from its registry.
- **Authority boundary:** Translates a question into a read-only SQL query, runs it against the analytics database, and returns the result with the query shown. It never writes, updates, deletes, or alters schema. Read-only by construction.
- **Verification test:** Attempt to run an INSERT/UPDATE/DELETE/DDL statement → confirm it is rejected and that only read-only queries are permitted (write tools absent).
- **Production readiness:** 6/6 dimensions passing. Tool isolation: read-only access; write/DDL tools absent. Human gates: results are for human interpretation. Confidence escalation: ambiguous questions clarified, not guessed. Cost ceiling: query and token budgets enforced. Audit trail: every query logged. Escalation path: ambiguous or sensitive queries flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/nl-to-sql-analyst#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/nl-to-sql-analyst
