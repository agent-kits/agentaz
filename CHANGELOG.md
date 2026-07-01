# Changelog

All notable changes to the AgentAz™ specification and the AgentKits registry are
documented here. The specification follows [Semantic Versioning](https://semver.org/).

## AgentAz Specification

### v2.0.0 — Draft / Unreleased (2026)
*Breaking line: Trust Levels become **computed**, not declared.*
- **Deterministic tier validator** (reference implementation, `reference/agentaz-validate.ts`,
  version `2.0.0-draft`): `computeTier(spec) → band` derives the Trust Level from the spec's
  structure (gated vs. auto-executable tools, absent execution tools, declared bounds) rather
  than reading a hand-authored `trust_level`. Same spec in, same tier out — for anyone — which
  moves a tier from *asserted* to *reproducible*.
- A re-runnable report (`reference/validate-tiers.mjs`) computes tiers across the full corpus.
- **Status:** draft, advisory only. Running the validator over the v1.x corpus shows it confirms
  the declared tier for the large majority of blueprints; the remaining cases are specifications
  authored in the pre-2.0 `allowed_tools` shape, whose approval gate is not yet *structurally*
  encoded. v2.0 therefore requires a one-time normalization of those specifications to the
  `auto_executable_tools` / `approval_required_tools` shape before the validator becomes
  authoritative. Signing of the computed result is planned and will follow normalization.
- **Framing:** the signed output attests *verifiable classification* (this tier was computed by a
  pinned validator from this exact file, unaltered) — not *verified safety* of the running agent.

### v1.1.0 — Additive (2026)
*Backward-compatible: no schema change, no field added or removed.*
- **Regulatory crosswalk** (`CROSSWALK.md`): maps each AgentAz dimension to the controls it
  helps satisfy in **NIST AI RMF 1.0**, **ISO/IEC 42001:2023**, and the **OWASP Top 10 for
  Agentic Applications (ASI01–ASI10, Dec 2025)**, with out-of-scope gaps stated explicitly. Lets
  a machine-readable `agentaz.json` serve as design-time evidence toward an enterprise compliance
  questionnaire. The crosswalk is versioned and dated independently, since the referenced
  frameworks are revised over time.

### v1.0.0 — Frozen (2026)
- First stable, frozen release of the AgentAz™ design-time governance specification.
- Canonical JSON Schema published at
  `https://www.agent-kits.com/agentaz/agentaz-v1.0.schema.json`.
- Trust Levels A0–A5 classified by **worst-case action**.
- Core boundaries: tool, output, cost, loop, human-handoff, audit.
- Reference implementation and schema licensed under Apache-2.0; specification
  text under CC-BY-4.0.

> v1.0 is frozen: no breaking changes will be made within the 1.x line. Additive,
> backward-compatible fields may appear in 1.x; any breaking change ships as 2.0.
