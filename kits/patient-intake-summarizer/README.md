# Patient Intake Summary Agent

> A patient-intake agent that turns intake forms into a structured clinician summary, flags red-flag symptoms and missing info, and never diagnoses or gives medical advice.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an inaccurate intake summary that a clinician reviews before relying on it. It cannot make a clinical or diagnostic decision and cannot write to the medical record — those tools are absent from its registry.
- **Authority boundary:** Reads provided intake information and assembles a structured summary for a clinician, flagging gaps and uncertainties. It never diagnoses, never recommends treatment as a decision, and never writes to the EHR. A clinician reviews and decides.
- **Verification test:** Attempt to call an EHR-write or diagnostic-decision tool → confirm it is absent; confirm the summary defers clinical judgment to a human.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: EHR-write/diagnosis tools absent. Human gates: a clinician decides. Confidence escalation: gaps and uncertainties flagged. Cost ceiling: bounded per intake. Audit trail: summary and sources logged. Escalation path: missing or conflicting info flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/patient-intake-summarizer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/patient-intake-summarizer
