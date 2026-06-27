# Community Question Triage Agent

> A community triage agent that routes and answers incoming questions from your knowledge base, flags duplicates, and sends spam, abuse, and safety issues to moderators.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Escalation (Research → Evaluate → Plan → Escalate)
- **Worst-case action:** Misroutes a community question or drafts a wrong suggested answer, caught before a human posts. It cannot post, send, or moderate autonomously — those tools are absent from its registry.
- **Authority boundary:** Reads community questions, classifies and prioritizes them, drafts a suggested answer from known resources, and routes or escalates. A human posts and moderates. It never posts, bans, or sends on its own.
- **Verification test:** Attempt to call a post, send, or moderate tool → confirm it is absent from the agent's registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: post/moderate tools absent. Human gates: a human posts. Confidence escalation: sensitive or uncertain questions escalated. Cost ceiling: bounded per question. Audit trail: classification and drafts logged. Escalation path: sensitive topics routed to a moderator.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/community-question-triager#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/community-question-triager
