# AI Incident Response Agent

> An on-call SRE agent: correlates alerts with metrics, logs, and recent deploys, proposes safe mitigations, drafts status updates, escalates SEV1 — with approval gates.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A4 — Limited Autonomy
- **DNA pattern:** Execution (Research → Plan → Execute → Verify)
- **Worst-case action:** Executes an allowlisted low-risk, reversible remediation step (e.g. restarting a stuck service) that turns out to be unnecessary. Every auto-executed step is sandboxed with a registered rollback. Irreversible or high-impact actions — production rollbacks, scaling, security or config changes — are never auto-executed; they require human approval.
- **Authority boundary:** May run a small allowlist of low-risk, reversible remediation steps automatically during an incident, each with a tested rollback and full audit trail. Anything risky or irreversible is proposed for human approval, not executed. It drafts status updates and escalates SEV1, but never makes an irreversible change on its own.
- **Verification test:** Trigger a high-risk action (e.g. scale-down production) → confirm it routes to human approval and is NOT auto-executed, and confirm every auto-executed step has a registered rollback.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: only reversible/low-risk tools are auto-executable; risky tools are gated. Human gates: irreversible actions require approval. Confidence escalation: low confidence routes to on-call. Cost ceiling: bounded per incident. Audit trail: every action and rollback logged append-only. Escalation path: SEV1 routed to human on-call.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/incident-responder#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/incident-responder
