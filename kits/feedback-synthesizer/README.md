# User Feedback Synthesis Agent

> A feedback-synthesis agent that clusters user feedback into themes with cited quotes and honest frequency, separating signal from small-sample noise. Never fabricates.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an inaccurate theme or miscounts feedback, surfaced for a PM to review. It cannot create tickets, change a roadmap, or take any action — execution tools are absent from its registry.
- **Authority boundary:** Reads user feedback across sources, clusters it into themes with representative quotes, and surfaces a synthesis for review. It never creates tickets, edits a roadmap, or fabricates feedback. A PM decides what to act on.
- **Verification test:** Attempt to call a create-ticket or roadmap-write tool → confirm it is absent; confirm themes cite real feedback rather than inventing it.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: ticket/roadmap tools absent. Human gates: a PM decides. Confidence escalation: thin or conflicting themes flagged. Cost ceiling: bounded per batch. Audit trail: themes and source counts logged. Escalation path: ambiguous signal flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/feedback-synthesizer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/feedback-synthesizer
