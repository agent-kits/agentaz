# Prior Authorization Agent

> An administrative prior-auth agent: checks requests against payer rules, flags missing docs, and assembles a review-ready packet. No clinical or coverage decisions.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A3 — Human-Approved
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Assembles an incomplete or incorrect prior-authorization packet that a human reviews before submission. It cannot submit to a payer, cannot make a clinical or coverage determination, and cannot alter the medical record — submission and EHR-write tools are absent from its registry.
- **Authority boundary:** Reads clinical and administrative inputs, assembles a structured prior-auth packet against payer requirements, and flags gaps and missing documentation for review. A human approves and submits. It never submits to a payer, never makes a clinical or coverage decision, and never writes to the EHR.
- **Verification test:** Attempt to call a payer-submission or EHR-write tool → confirm it is absent from the agent's tool registry (not merely disabled).
- **Production readiness:** 6/6 dimensions passing. Tool isolation: submission and EHR-write tools absent. Human gates: approval required before submission. Confidence escalation: missing or uncertain fields routed to a reviewer. Cost ceiling: bounded per packet. Audit trail: assembly steps and flags logged. Escalation path: incomplete packets routed to a human reviewer.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/prior-auth-packet-assembler#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/prior-auth-packet-assembler
