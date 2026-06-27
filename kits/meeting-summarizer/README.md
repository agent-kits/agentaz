# Meeting Summary & Action Item Agent

> A meeting agent that turns a transcript into a faithful summary, cited decisions, and owned action items — never inventing a decision or owner the transcript lacks.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Produces an inaccurate summary or a wrong action item that participants review and correct. It cannot send, assign, schedule, or take any action — those tools are absent from its registry.
- **Authority boundary:** Reads a transcript, summarizes it, and extracts action items with owners and due dates where stated, flagging ambiguous ownership. Participants confirm. It never sends, assigns, or schedules, and it never invents owners or commitments.
- **Verification test:** Provide a transcript with unclear ownership → confirm the agent flags it rather than inventing an owner; confirm no send/assign tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: send/assign/schedule tools absent. Human gates: participants confirm. Confidence escalation: ambiguous items flagged. Cost ceiling: bounded per meeting. Audit trail: summary and items logged. Escalation path: unclear ownership flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/meeting-summarizer#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/meeting-summarizer
