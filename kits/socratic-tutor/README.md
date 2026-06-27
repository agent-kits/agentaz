# Socratic Tutor Agent

> A tutoring agent that guides learners with questions and hints instead of giving answers — supports academic integrity, stays accurate, and escalates to a teacher.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Gives a learner a misleading hint or explanation, which the learner or teacher can correct. It guides through questions and never takes any action — it cannot grade officially, change records, or contact anyone, and those tools are absent from its registry.
- **Authority boundary:** Guides a learner toward understanding through questions and hints, grounded in the provided material, and keeps content age-appropriate. It never delivers official grades, changes records, or contacts third parties, and it defers correctness to the teacher's material.
- **Verification test:** Confirm the agent guides rather than asserts final answers and that no grading, record-write, or contact tool exists in its registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: grading/record/contact tools absent. Human gates: a teacher owns assessment. Confidence escalation: uncertain or off-syllabus questions deferred. Cost ceiling: bounded per session. Audit trail: prompts and hints logged. Escalation path: off-topic or sensitive content deferred to a teacher.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/socratic-tutor#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/socratic-tutor
