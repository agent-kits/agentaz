# Social Post Drafting Agent

> A social agent that drafts on-brand posts from your brief, never auto-posts, avoids fabricated claims, and flags sensitive topics and required disclosures for review.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Drafts an off-brand or inaccurate social post that a human reviews before posting. It cannot post or schedule to any platform, never fabricates claims, and prompts for required disclosures — posting tools are absent from its registry.
- **Authority boundary:** Drafts social posts grounded in provided material and brand voice, prompts for any required disclosures (such as #ad), and flags unverifiable claims. A human reviews and posts. It never posts, schedules, or invents claims.
- **Verification test:** Confirm drafts add no unverifiable claims and prompt for disclosures; confirm no post/schedule tool exists in the registry.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: post/schedule tools absent. Human gates: a human posts. Confidence escalation: unverifiable claims and missing disclosures flagged. Cost ceiling: bounded per batch. Audit trail: drafts logged. Escalation path: sensitive claims flagged.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/social-post-drafter#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/social-post-drafter
