# Production-Grade AI Code Review Agent

> An evidence-based code review agent for real PRs: security, correctness, concurrency, performance — with file:line findings, risk scores, and a human-escalation gate.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Posts an incorrect or noisy review comment that a human can dismiss. It cannot merge, push, approve, or modify code — write and merge tools are absent from its registry.
- **Authority boundary:** Reads a diff, evaluates it for bugs, security, and style, and posts review comments and suggestions. It never merges, pushes, approves a PR, or edits the branch. A human reviewer decides.
- **Verification test:** Attempt to call a merge, push, or approve-PR tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: merge/push/approve tools absent. Human gates: a reviewer decides and merges. Confidence escalation: low-confidence findings flagged as suggestions. Cost ceiling: bounded per diff. Audit trail: comments and rationale logged. Escalation path: security-sensitive findings flagged for a human.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/code-review-assistant#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/code-review-assistant
