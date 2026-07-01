# AI Bug-Fix & Draft-PR Agent

> An AI bug-fix agent: reproduces an issue, finds root cause, writes a minimal fix plus tests, and opens a focused draft PR — sandboxed, small-diff, human-gated.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A4 — Limited Autonomy
- **DNA pattern:** Execution (Research → Plan → Execute → Verify)
- **Worst-case action:** Writes a fix on a sandboxed branch and opens a DRAFT pull request containing an incorrect change. The draft is never merged automatically; a human reviews and merges. Branch work is reversible and every run leaves an audit trail.
- **Authority boundary:** Reproduces an issue, writes a candidate fix on an isolated branch, runs tests in a sandbox, and opens a draft PR for human review. It never merges to a protected branch, never force-pushes, and never deploys. A human approves and merges.
- **Verification test:** Confirm the agent opens a DRAFT PR only and cannot merge to a protected branch (merge-to-main is absent/blocked); confirm branch changes are isolated and reversible.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: writes confined to an isolated branch; merge-to-main absent. Human gates: a human reviews and merges the draft. Confidence escalation: low-confidence fixes flagged in the PR. Cost ceiling: bounded per issue. Audit trail: diff, tests, and reasoning logged. Escalation path: risky changes flagged for a maintainer.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/issue-to-pr-planner#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/issue-to-pr-planner
