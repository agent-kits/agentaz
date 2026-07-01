# Access Request & Provisioning Agent

> An access-request agent that checks role policy and separation-of-duties, auto-provisions low-risk access, and escalates privileged or sensitive requests.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification. **Flagship reference blueprint.**

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Planning (Research → Plan)
- **Worst-case action:** Prepares an incorrect access change that a human reviews before it is applied. It cannot grant, revoke, or modify access itself — provisioning tools are absent from its registry.
- **Authority boundary:** Gathers context on an access request, checks it against policy, and prepares the access change for approval. It never grants or revokes access and never touches provisioning systems. An approver applies the change.
- **Verification test:** Attempt to call a grant-access or provisioning-write tool → confirm it is absent from the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: provisioning tools absent. Human gates: approver applies changes. Confidence escalation: policy-ambiguous requests flagged. Cost ceiling: bounded. Audit trail: request, policy check, and prepared change logged. Escalation path: sensitive grants routed to an owner.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/access-request-handler#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/access-request-handler
