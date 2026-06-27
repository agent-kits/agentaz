# Vendor Risk Assessment Agent

> A vendor-risk agent that scores third parties on security, compliance, and data access from evidence, flags missing certs and DPAs, and recommends a tier.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Produces an inaccurate vendor risk score, surfaced for human review. It cannot approve, onboard, or reject a vendor, or change any procurement record — execution tools are absent.
- **Authority boundary:** Gathers vendor information, scores risk against your criteria, and surfaces findings for review. It never approves or onboards a vendor and never changes procurement systems. Procurement owns the decision.
- **Verification test:** Attempt to call a vendor-approve or procurement-write tool → confirm it is absent from the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: approval/procurement tools absent. Human gates: procurement decides. Confidence escalation: uncertain findings flagged. Cost ceiling: bounded. Audit trail: scores and evidence logged. Escalation path: high-risk vendors routed to a reviewer.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/vendor-risk-assessor#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/vendor-risk-assessor
