# NDA Triage Agent

> An NDA triage agent that extracts key terms, flags non-standard and risky clauses against your playbook, and recommends lawyer review without giving legal sign-off.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Misflags an NDA clause or misjudges standardness, surfaced for human review. It cannot sign, approve, or send an NDA — execution tools are absent from its registry.
- **Authority boundary:** Reviews an NDA, flags non-standard clauses against your playbook, and recommends standard language for review. It never signs, approves, or sends. A reviewer decides.
- **Verification test:** Attempt to call a sign, approve, or send tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: signing/sending tools absent. Human gates: a reviewer decides. Confidence escalation: unusual clauses flagged. Cost ceiling: bounded. Audit trail: flags and playbook refs logged. Escalation path: non-standard NDAs routed to counsel.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/nda-triage-agent#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/nda-triage-agent
