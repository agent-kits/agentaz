# Resume Screening Agent

> A resume-screening agent that scores only job-relevant evidence, ignores protected attributes, cites every finding, and routes the decision to a human recruiter.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Produces a biased or incorrect screening assessment, surfaced for a recruiter to review. It cannot reject, advance, contact a candidate, or make any hiring decision — execution tools are absent from its registry.
- **Authority boundary:** Reviews a resume against job-relevant, documented criteria and surfaces a structured assessment for human review. It never rejects, advances, or contacts candidates, and never makes a hiring decision. A recruiter decides, and protected-characteristic factors are excluded.
- **Verification test:** Attempt to call a reject, advance, or candidate-contact tool → confirm it is absent; confirm the criteria exclude protected characteristics.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: decision/contact tools absent. Human gates: a recruiter decides. Confidence escalation: borderline candidates flagged for review, never auto-rejected. Cost ceiling: bounded per resume. Audit trail: assessment and criteria logged for fairness review. Escalation path: ambiguous cases routed to a recruiter.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/resume-screener#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/resume-screener
