# AI Contract Review Agent

> A contract-review agent: reads clause by clause against your playbook, flags risky and missing terms with severity, and proposes fallback language. Not legal advice.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Surfaces an incorrect risk assessment or misses a risky clause, flagged for a lawyer to review. It cannot sign, send, approve, or alter a contract — execution tools are absent from its registry.
- **Authority boundary:** Reads a contract, flags risky or non-standard clauses, and suggests redlines for human review. It never signs, sends, approves, or commits to a contract. A lawyer makes every decision.
- **Verification test:** Attempt to call a sign, send, or contract-write tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: signing/sending tools absent. Human gates: a lawyer decides. Confidence escalation: low-confidence clauses flagged. Cost ceiling: bounded per review. Audit trail: flags and rationale logged. Escalation path: ambiguous clauses routed to counsel.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/contract-clause-reviewer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/contract-clause-reviewer
