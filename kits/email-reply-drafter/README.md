# Email Reply Drafting Agent

> An email agent that drafts contextual replies in your voice from the thread, never sends on its own, avoids unapproved commitments, and flags sensitive emails for review.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Evaluation (Research → Evaluate)
- **Worst-case action:** Drafts an incorrect or off-tone reply that a human reviews before sending. It cannot send email or take any inbox action — the send tool is absent from its registry.
- **Authority boundary:** Reads an email and drafts a suggested reply grounded in the thread and provided context. A human reviews and sends. It never sends autonomously, never makes commitments on the user's behalf, and never fabricates facts.
- **Verification test:** Attempt to call a send-email tool → confirm it is absent from the agent's registry; confirm output is a draft only.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send tools absent. Human gates: a human sends. Confidence escalation: sensitive or uncertain threads flagged. Cost ceiling: bounded per email. Audit trail: drafts logged. Escalation path: commitments or sensitive topics flagged for the user.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/email-reply-drafter#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/email-reply-drafter
