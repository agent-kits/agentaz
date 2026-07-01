# RFC-0001: Trust Levels A0–A5

- **Status:** Accepted
- **Author(s):** AgentKits / AgentAz maintainer
- **Created:** 2026-06-30
- **Note:** Retroactive. This documents a foundational design decision already present in
  AgentAz v1.0, entered into the RFC record for provenance and future reference.

## Summary

AgentAz classifies an AI agent by a single **Trust Level** on a six-step ladder, **A0–A5**,
determined by the agent's authority over irreversible action — that is, how far it can run
before a human must intervene.

## Motivation

Risk in an AI agent is not driven by how capable it is, but by the most harmful irreversible
thing it can do without human approval. Teams needed one comparable axis for that, instead of
ad-hoc prose per project. A small, ordered scale makes agents comparable, reviewable, and —
because the level follows from the agent's structure — computable rather than merely asserted.

## Proposal

Six Trust Levels, defined by authority over irreversible action:

| Level | Meaning |
| --- | --- |
| **A0** | No tools. Cannot act at all. |
| **A1** | Read-only. Gathers or analyzes; cannot change any external system. |
| **A2** | Advisory. Produces recommendations or drafts; still cannot change any external system. |
| **A3** | Gated action. Can perform consequential actions, but every one is behind a human approval gate. |
| **A4** | Bounded autonomy. Performs some consequential actions autonomously, within declared cost, loop, and audit bounds. |
| **A5** | Unbounded autonomy. Performs consequential actions autonomously, without a gate or declared bounds. |

The level is derived from the agent's declared tool boundary (which tools are
auto-executable versus approval-required, and whether execution tools are absent), together
with its declared bounds and audit trail. The advisory band (A1/A2) reflects an authoring
distinction (pure read vs. produces recommendations); the action bands (A3–A5) are
determined structurally.

## Rationale & alternatives

**Why anchor on worst-case action, not capability?** Capability lists grow without bound and
don't predict harm. The worst irreversible action, and whether a human gates it, is the
single fact that determines blast radius.

**Why six levels?** They map cleanly to the meaningful thresholds: no tools (A0), can't
mutate (A1/A2), gated mutation (A3), bounded autonomous mutation (A4), unbounded autonomous
mutation (A5). Fewer levels lose the gated/bounded/unbounded distinctions that matter most;
more levels add resolution the structure can't support.

**Alternatives considered:** a numeric 0–100 risk score (rejected — false precision, not
reproducible); a free-text risk label (rejected — not comparable or computable).

## Impact

- **Backward compatibility:** foundational to v1.0; no break.
- **Validator:** the reference validator computes the band from spec structure.
- **Version:** present since v1.0.0.

## Decision

**Accepted** as the foundational classification of AgentAz. Recorded 2026-06-30.
