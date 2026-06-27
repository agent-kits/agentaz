# Test Case Generation Agent

> A test-case agent that turns requirements into happy-path, edge, and negative cases with steps and expected results, flagging ambiguous specs instead of guessing.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Generates incomplete or incorrect test cases that an engineer reviews before use. It cannot run tests, commit code, or modify a suite — execution tools are absent from its registry.
- **Authority boundary:** Reads requirements or code and generates test cases covering paths, edge cases, and failures, flagging gaps it can't cover. An engineer reviews and adds them. It never runs tests, commits, or modifies the codebase.
- **Verification test:** Attempt to call a run-tests, commit, or write-to-repo tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: run/commit tools absent. Human gates: an engineer reviews. Confidence escalation: uncoverable cases flagged. Cost ceiling: bounded per target. Audit trail: generated cases logged. Escalation path: ambiguous requirements flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/test-case-generator#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/test-case-generator
