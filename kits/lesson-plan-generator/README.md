# Lesson Plan Generation Agent

> A lesson-plan agent that builds structured, age-appropriate plans from your objectives, keeps content accurate, and flags where teacher judgment is needed.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Produces a weak or off-standard lesson plan that a teacher reviews and adapts before use. It cannot publish, assign, or deliver anything to students — execution tools are absent from its registry.
- **Authority boundary:** Generates a structured lesson plan — objectives, activities, materials, assessment — aligned to provided standards, for a teacher to review and adapt. It never delivers content to students, assigns work, or publishes. The teacher owns the plan.
- **Verification test:** Confirm the plan is a draft for a teacher and no student-facing delivery or assign tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: deliver/assign tools absent. Human gates: a teacher reviews and adapts. Confidence escalation: standard mismatches flagged. Cost ceiling: bounded per plan. Audit trail: plan and standards logged. Escalation path: unclear objectives flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/lesson-plan-generator#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/lesson-plan-generator
