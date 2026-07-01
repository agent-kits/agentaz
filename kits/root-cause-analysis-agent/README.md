# Incident Root-Cause Analysis Agent

> Pulls logs, metrics, traces, and recent changes into one timeline, ranks root-cause hypotheses, and gates any published RCA behind a human. Diagnoses, never remediates.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Planning (Gather → Correlate → Hypothesize)
- **Worst-case action:** Prepares an incorrect root-cause analysis or a misleading incident status update that a human reviews before it is published. It cannot perform any remediation — rollback, restart, scale, deploy, and config-change tools are absent from its registry — so it cannot worsen an incident by acting.
- **Authority boundary:** Reads telemetry and change history and prepares an RCA for human approval; publishing the RCA and updating the status page are the only writes, both approval-gated. No remediation, no self-published conclusions, no system changes.
- **Verification test:** Feed an incident with two near-equally-evidenced causes and confirm the agent escalates instead of publishing; remove part of the evidence window and confirm it reports incompleteness and escalates rather than concluding.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: remediation tools (rollback, restart, scale, deploy, config-change) are absent; only the gated publish and status-update writes exist. Human gates: publish_rca and update_status_page require explicit human approval before anything goes out. Confidence escalation: weak leads, thin hypothesis margins, or incomplete evidence route to a human rather than publishing. Cost ceiling: bounded reasoning turns and a per-trace spend cap. Audit trail: the incident, evidence examined, ranked hypotheses, and approvals are recorded in an append-only log. Escalation path: high-severity or under-evidenced incidents escalate to the incident commander / on-call.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/root-cause-analysis-agent#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/root-cause-analysis-agent
