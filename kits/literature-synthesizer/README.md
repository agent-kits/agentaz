# Literature Synthesis Agent

> A literature-synthesis agent that reviews your sources, cites every claim, weighs evidence strength, surfaces conflicts, and never fabricates findings or citations.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A1 — Research
- **DNA pattern:** Research (Research → Verify)
- **Worst-case action:** Includes a wrong or overstated claim in a literature synthesis that a human reviews before relying on it. It only gathers and cites sources; it never fabricates a citation or finding and never takes any action.
- **Authority boundary:** Synthesizes provided or retrieved literature into a structured summary with citations, distinguishing well-supported findings from weak ones and flagging gaps. It never invents a citation, overstates evidence, or takes action.
- **Verification test:** Confirm every claim maps to a real cited source and confidence is qualified; confirm no fabricated citation and no action tool in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: action tools absent. Human gates: a human reviews. Confidence escalation: weak or conflicting evidence flagged. Cost ceiling: bounded per synthesis. Audit trail: sources and citations logged. Escalation path: thin evidence flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/literature-synthesizer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/literature-synthesizer
