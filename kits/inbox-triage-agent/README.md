# Inbox Triage Agent

> An inbox-triage agent that classifies and prioritizes email, drafts routine replies, flags phishing, and escalates high-stakes messages. Never auto-sends sensitive mail.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Mislabels or misprioritizes a message, surfaced for the user to correct. It cannot send, delete, archive irreversibly, or take account actions — those tools are absent from its registry.
- **Authority boundary:** Reads incoming mail, classifies and prioritizes it, suggests labels, and surfaces what needs attention. The user confirms actions. It never sends, never deletes, and never acts on the user's behalf without confirmation.
- **Verification test:** Attempt to call a send, delete, or account-action tool → confirm it is absent; confirm labels are suggestions the user confirms.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send/delete tools absent. Human gates: the user confirms actions. Confidence escalation: ambiguous mail flagged. Cost ceiling: bounded per batch. Audit trail: classifications logged. Escalation path: important or sensitive mail surfaced first.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/inbox-triage-agent#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/inbox-triage-agent
