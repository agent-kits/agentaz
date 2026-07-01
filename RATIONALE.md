# AgentAz™ — Origin & Design Rationale

*First published 2026. Maintained in the open at github.com/agent-kits/agentaz.*

This document records what AgentAz is, why it exists, and the reasoning behind its
design. It is a plain-English companion to the formal specification — the "why," not the
"what." It also serves as a dated, public record of the design decisions behind AgentAz.

## What AgentAz is

AgentAz is a small, design-time vocabulary for describing **how much authority an AI agent
has, and what stops it from doing harm.** An agent is described in a short machine-readable
file (`agentaz.json`) that declares its worst-case action, its tool boundary, its human
gates, its cost and loop limits, and its audit trail. From that structure, a **Trust Level
(A0–A5)** can be computed.

It is deliberately narrow: design-time, blueprint-level, machine-readable. It does not run
your agent, watch it in production, or certify it. It describes intent in a form a human or
a machine can check.

## Why it exists

As AI agents move from demos to production, the hard question stops being "can it do the
task?" and becomes "what is the worst thing it can do, and what prevents that?" Today that
question is usually answered in prose, informally, per team — which means it can't be
compared, audited, or verified.

AgentAz exists to make that answer **structured and checkable.** If two agents both declare
an `agentaz.json`, you can compare their authority the same way you compare two APIs by
their schema. A security reviewer can read the boundary instead of guessing. A tier can be
**computed** from the structure rather than asserted by the author.

## The design decisions, and why

**Classify by worst-case action, not by capability.** What makes an agent risky is not how
clever it is — it's the most harmful irreversible thing it can do without a human. So the
Trust Level is anchored on the worst-case action and whether it is gated, not on the
agent's feature list.

**Six Trust Levels (A0–A5), by authority over irreversible action.** A0 has no tools; A1–A2
are advisory (can't change the world); A3 can act but only behind a human gate; A4 acts
autonomously within declared bounds; A5 acts autonomously without bounds. The ladder maps to
the single thing that matters for risk: *how far can this run before a human must intervene?*

**Boundaries are first-class.** Tool boundary (least privilege), human-approval gate,
confidence escalation, cost ceiling, loop bound, output boundary, and a tamper-evident audit
trail are named, declarable fields — because these are the controls that actually contain an
agent, and naming them makes them reviewable.

**Tiers should be computed, not claimed.** A trust level an author simply *types* is a
marketing label. A trust level a shared validator *derives from the file* is verifiable:
same file in, same tier out, for anyone. This is why the reference validator is public — a
standard whose classification can't be independently reproduced isn't a standard.

**Design-time, not runtime — on purpose.** AgentAz stays in one lane. It documents intended
boundaries; it does not prove your running system honors them. Enforcement is your runtime's
job. Keeping the scope narrow is what makes the vocabulary small enough to actually adopt.

## What AgentAz is not

It is not a safety certification, not a runtime monitor, not an agent framework, and not a
guarantee. A high tier means "this design places strong limits on the agent," not "this
agent is safe." Those are different claims, and AgentAz only makes the first.

## How it evolves

Changes to the specification go through a public, dated RFC process (see `rfcs/`). Proposals
are open for comment for at least 7 days before they can be accepted. This keeps the design
history transparent and on the record.
