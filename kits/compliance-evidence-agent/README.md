# Compliance Evidence & Audit-Trail Agent

> Maps each change to your control catalog, assembles tamper-evident evidence, and gates filing behind a human — it records, it doesn't decide compliance.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Planning (Map → Assemble → Gate)
- **Worst-case action:** Prepares an incomplete or mis-mapped evidence record that a human compliance owner reviews before it is filed. It cannot file records autonomously, modify source systems, grant access, or alter prior audit entries — write tools other than the gated commit are absent from its registry.
- **Authority boundary:** Maps events to a configured control catalog and assembles evidence for human approval; committing a record and requesting sign-off are the only writes, both approval-gated. No source-system modification, no self-approval, no mutation of prior entries.
- **Verification test:** Inject a tampered or reordered entry into the audit log and confirm chain verification returns false; submit an incomplete record on a regulated resource and confirm the agent escalates instead of filing.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: source-system write, access-grant, and entry-mutation tools are absent; only the gated commit writes. Human gates: request_signoff and commit_evidence require explicit human approval before filing. Confidence escalation: ambiguous mappings and below-threshold completeness route to a human rather than filing. Cost ceiling: bounded reasoning turns and a per-trace spend cap. Audit trail: append-only, HMAC-chained log with verifiable integrity. Escalation path: incomplete, regulated, or low-confidence records route to the named compliance owner.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/compliance-evidence-agent#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/compliance-evidence-agent
