# Insurance Policy Coverage Agent

> An insurance agent that explains policy coverage from the actual document with citations, flags what's unclear, and never guarantees a claim will be paid.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Synthesis (Extract → Synthesize → Verify)
- **Worst-case action:** Gives an incorrect explanation of what a policy covers that a human reviews before relying on it. It cannot make a coverage determination, approve or deny a claim, or pay — those tools are absent from its registry.
- **Authority boundary:** Reads a policy document and explains coverage, limits, and exclusions in plain language with citations to the policy. It never makes a binding coverage determination, never approves or denies, and never pays. A licensed human decides.
- **Verification test:** Attempt to call a coverage-determination, approve/deny, or payment tool → confirm it is absent; confirm explanations cite the policy.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: determination/payment tools absent. Human gates: a licensed human decides. Confidence escalation: ambiguous policy language flagged. Cost ceiling: bounded per query. Audit trail: explanations and citations logged. Escalation path: edge cases routed to a human.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/policy-coverage-explainer#run-live · Score any agent against Microsoft’s guidance: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/policy-coverage-explainer
