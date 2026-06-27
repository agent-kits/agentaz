# AgentAz™ — open-source AI-agent governance + 60 reference blueprints

A small, open spec for writing down what an AI agent is allowed to do — and what its
**worst-case action** is — *before* you ship it.

AgentAz is design-time only. It doesn't run anything or wrap your code; it's a vocabulary for
documenting an agent's authority, failure modes, and escalation path in a file you can review,
diff, and hand to a security or compliance team. Your runtime still does the enforcing — AgentAz
just makes the intent reviewable.

This repo holds the spec and a reference registry: **60 agent blueprints** (13 flagship), each
tagged with a Trust Level, a written-out worst-case action, and a machine-readable `agentaz.json`
that validates against the v1.0.0 schema.

> The browsable version — search, the risk-assessment tool, downloads — lives at https://www.agent-kits.com.
> This repo is the raw source.

## What's in here

```
SPEC.md                          The AgentAz v1.0 spec
schema/agentaz-v1.0.schema.json  JSON Schema (draft-07) the contracts validate against
kits/<slug>/agentaz.json         The governance contract for one agent
kits/<slug>/kit.json             Full blueprint: prompt, tools, workflow, examples, failure modes
kits/<slug>/run.py               Runnable demo: native tool-use loop + enforced approval gate
kits/<slug>/evals/run.py         Deterministic safety check for the gate (no API key needed)
kits/<slug>/requirements.txt     Python dependencies for the demo
kits/<slug>/README.md            Plain-English summary + attribution
flagships.json                   The 13 reference kits
LICENSE (Apache-2.0)             Code & schema
docs/CONTENT-LICENSE.md (CC-BY-4.0)  Spec text & blueprint content
```

## Using it

- **Validate** any `agentaz.json` against `schema/agentaz-v1.0.schema.json` (JSON Schema draft-07).
- **Score** any agent's governance — paste a system prompt or an `agentaz.json` into the free, deterministic [AgentAz Compliance Scanner](https://www.agent-kits.com/scan); it runs in your browser and returns a grade plus a fix-list.
- **Run** any blueprint live — each kit page has a browser playground that executes the real loop with your own API key, with the same approval gate as `run.py`.
- **Use the vocabulary** in your own agents — it's open, and using it doesn't imply we've
  reviewed or endorsed your agent.
- **Browse** the rendered blueprints at https://www.agent-kits.com.

## Status

AgentAz **v1.0.0 is frozen** — no breaking changes within 1.x, and the schema `$id` URL
(https://www.agent-kits.com/agentaz/agentaz-v1.0.schema.json) is permanent. It's early: expect the spec to grow at the edges (more examples,
clearer guidance) without breaking what's here. Issues and PRs welcome — see `CONTRIBUTING.md`.

## License & names

Code and schema are Apache-2.0 (`LICENSE`). Spec text and blueprint content are CC-BY-4.0
(`docs/CONTENT-LICENSE.md`). “AgentAz” and “AgentKits” are trademarks of AgentKits — the open
licenses cover the work, not the names.

## How this repo is maintained

It's generated from the main AgentKits source and published one-way, so don't hand-edit files
here — changes happen upstream and the repo is regenerated. File issues/PRs per `CONTRIBUTING.md`.
