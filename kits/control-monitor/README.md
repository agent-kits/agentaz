# Compliance Control Monitoring Agent

> A compliance agent that tests internal controls against real evidence, flags failures and missing evidence, and never marks a control compliant without proof.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Misses a failing control or flags a passing one, surfaced for a compliance reviewer. It cannot mark a control compliant, change its status, or close a finding — execution tools are absent from its registry.
- **Authority boundary:** Monitors compliance controls against evidence, flags likely failures and gaps, and surfaces them for review. It never marks a control compliant to pass an audit, changes control status, or closes findings. A compliance owner decides.
- **Verification test:** Attempt to call a mark-compliant or close-finding tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: status-change tools absent. Human gates: a compliance owner decides. Confidence escalation: ambiguous evidence flagged, not resolved. Cost ceiling: bounded per scan. Audit trail: control checks and evidence logged. Escalation path: failing controls routed to the owner.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/control-monitor#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/control-monitor
