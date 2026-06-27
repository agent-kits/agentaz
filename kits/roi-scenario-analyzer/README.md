# ROI Scenario Analysis Agent

> An ROI agent that models scenarios from your inputs, states every assumption, shows the math, and labels results as estimates, never guaranteeing returns.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Produces a misleading ROI estimate that a human reviews before relying on it. It cannot commit budget, approve an investment, or take any action — outputs are clearly labeled estimates and execution tools are absent from its registry.
- **Authority boundary:** Computes ROI and payback scenarios strictly from the inputs provided, labels every result an estimate (never a guarantee), and surfaces assumptions for review. It never commits budget, approves spend, or invents figures. A human decides.
- **Verification test:** Confirm outputs are labeled estimates with stated assumptions, not guarantees; confirm no budget-commit or approval tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: commit/approval tools absent. Human gates: a human decides. Confidence escalation: sensitivity and assumptions surfaced. Cost ceiling: bounded per analysis. Audit trail: inputs and assumptions logged. Escalation path: missing inputs flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/roi-scenario-analyzer#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/roi-scenario-analyzer
