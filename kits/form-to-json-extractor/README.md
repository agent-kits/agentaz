# Form-to-JSON Extraction Agent

> A form-extraction agent that turns documents into schema-valid JSON, scores confidence per field, and flags illegible or missing fields instead of guessing.

Part of **AgentKits** — the open registry of production AI agent blueprints, governed by the **AgentAz™** specification.

## AgentAz™ governance

- **Trust Level:** A2 — Recommend
- **DNA pattern:** Extraction (Extract → Verify)
- **Worst-case action:** Returns an incorrect or missing field, marked absent rather than guessed, for human review. It never fabricates values and cannot write extracted data anywhere — execution tools are absent.
- **Authority boundary:** Reads a form, extracts only fields that are actually present, validates against a schema, and marks missing fields as absent. It never guesses or fabricates a value and never writes downstream. A human consumes the validated output.
- **Verification test:** Provide a form with a blank field → confirm the agent marks it absent and does not invent a value; confirm no write tool exists.
- **Production readiness:** 6/6 dimensions passing. Tool isolation: write tools absent. Human gates: output consumed by a human/system after review. Confidence escalation: ambiguous fields flagged. Cost ceiling: bounded per form. Audit trail: extracted fields logged. Escalation path: low-confidence forms routed to review.

Machine-readable contract: [`agentaz.json`](./agentaz.json) — validates against the frozen [AgentAz v1.0.0 schema](../../schema/agentaz-v1.0.schema.json).
Full blueprint (prompt, tools, workflow, examples): [`kit.json`](./kit.json).
Runnable demo: [`run.py`](./run.py) — a real native tool-use loop (Anthropic or OpenAI) with mock tools and a **runtime-enforced approval gate**. Verify the gate with [`evals/run.py`](./evals/run.py) — deterministic, no API key required. Install deps with [`requirements.txt`](./requirements.txt).

Run it live in your browser (your own API key): https://www.agent-kits.com/kit/form-to-json-extractor#run-live · Score any agent against this rubric: https://www.agent-kits.com/scan

## License & attribution

- **Code, configuration, and schema:** Apache-2.0 — see [`LICENSE`](../../LICENSE).
- **This blueprint's text and documentation:** CC BY 4.0 — see [`docs/CONTENT-LICENSE.md`](../../docs/CONTENT-LICENSE.md). Attribution: “AgentKits — https://www.agent-kits.com”.
- “AgentAz” and “AgentKits” are trademarks of AgentKits.

Rendered page: https://www.agent-kits.com/kit/form-to-json-extractor
