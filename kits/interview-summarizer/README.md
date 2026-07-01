# Interview Summary Agent

> An interview-summary agent that turns notes into evidence-based feedback against role criteria, screens out biased factors, and never makes the hiring decision.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an inaccurate interview summary that a recruiter reviews before relying on it. It cannot make or record a hiring decision, advance, or reject a candidate — execution tools are absent from its registry.
- **Authority boundary:** Summarizes an interview from notes or a transcript into structured, job-relevant observations for review, flagging where evidence is thin. It never makes a hiring recommendation as a decision, advances, rejects, or contacts candidates. A recruiter decides.
- **Verification test:** Attempt to call an advance, reject, or hiring-decision tool → confirm it is absent; confirm the summary defers the decision to a human.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: decision/contact tools absent. Human gates: a recruiter decides. Confidence escalation: thin evidence flagged. Cost ceiling: bounded per interview. Audit trail: summary and sources logged. Escalation path: ambiguous signals flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/interview-summarizer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/interview-summarizer
