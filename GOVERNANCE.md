# Governance

AgentKits maintains the AgentAz™ specification and the public blueprint registry.
This document describes how the project is stewarded so that adopters can rely on
its stability.

## Stewardship

- AgentKits is the current maintainer and steward of AgentAz™.
- The goal is a **neutral, stable, openly licensed** specification that any
  project or vendor can adopt without endorsing AgentKits.

## Stability guarantees

- **AgentAz v1.0 is frozen.** No breaking changes within the 1.x line.
- Additive, backward-compatible fields may be introduced as minor versions.
- Any breaking change ships as a new major version (2.0) with a migration note in
  `CHANGELOG.md`.
- The canonical schema URL for v1.0 is permanent:
  `https://www.agent-kits.com/agentaz/agentaz-v1.0.schema.json`.

## Decision-making

- Changes are proposed via GitHub issues/PRs and reviewed by the maintainers.
- Specification changes require a documented rationale and a CHANGELOG entry.
- We welcome co-stewardship from serious adopters; open an issue to discuss.

## Trademarks

"AgentAz" and "AgentKits" are trademarks of AgentKits. The open licenses cover the
code, schema, and specification text — not the names or marks.
