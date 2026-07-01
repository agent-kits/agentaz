# AgentAz™ Regulatory Crosswalk

**Crosswalk version 1.0 · Last reviewed 2026-06-30**

AgentAz is a *design-time* governance vocabulary. This crosswalk maps each AgentAz
dimension to the controls it helps satisfy in three frameworks an enterprise is likely
already audited against, so a machine-readable `agentaz.json` can serve as design-time
evidence toward the governance section of a security questionnaire.

Read each row as: *an agent that declares this AgentAz dimension is producing design-time
evidence toward these controls.* It is **evidence toward**, not a certification — the mapping
shows intent is documented, not that an auditor has verified the running system.

| AgentAz dimension | NIST AI RMF 1.0 | ISO/IEC 42001:2023 | OWASP Agentic (ASI) |
| --- | --- | --- | --- |
| Worst-case action & Trust Level (A1–A5) | MAP 1.1, MAP 5.1 (impact likelihood & magnitude) | A.5 — AI system impact assessment | ASI01 Goal Hijack · ASI10 Rogue Agents |
| Authority boundary | MAP 2 (categorization), GOVERN 1.4 | A.9.4 (intended use), A.9.2 | ASI03 Identity & Privilege Abuse |
| Tool boundary (least privilege) | MANAGE 2 (risk treatment) | A.4 (resources), A.9.2 (usage limits) | ASI02 Tool Misuse · ASI03 (“Least Agency”) |
| Human approval gate | MANAGE 4.1 (override), GOVERN 1.4 | A.9.2 (human oversight / override) | ASI09 Human-Agent Trust (supports ASI02) |
| Confidence escalation | MANAGE 4.1, MANAGE 2 | A.6.2 (operation), A.9.2 | ASI09 (decision-fatigue) · ASI01 |
| Cost ceiling *(partial)* | MANAGE 2 | A.6.2 | ASI08 Cascading Failures (blast-radius) |
| Loop bound / escape hatch | MANAGE 4.1 (monitoring) | A.6.2 | ASI08 Cascading Failures (circuit breakers) |
| Output boundary *(partial)* | MEASURE 2 (evaluation) | A.8, A.9.2 | ASI02 · ASI05 Unexpected Code Execution |
| Audit trail (tamper-evident) | MANAGE 4 (monitoring), GOVERN (documentation) | A.6.2 (lifecycle logging), A.5 | Cross-cutting — detection for ASI06 / ASI10 |

## What this crosswalk does *not* claim

AgentAz stays in one lane: design-time, machine-readable, blueprint-level. It does not cover
runtime proof, agent identity, or certification. Specifically out of scope:

- **OWASP ASI04 (Supply Chain), ASI05 (sandboxing of code execution), ASI06 (memory/RAG
  poisoning), ASI07 (inter-agent communication)** — runtime and infrastructure defenses.
  AgentAz documents design-time intent; these belong to your runtime and security layers.
- **NIST MEASURE bias/fairness depth and full TEVV methodology** — AgentAz is boundary-focused,
  not a fairness-testing methodology; treat as partial at best.
- **ISO/IEC 42001 A.7 (data governance) and A.10 (third-party relationships)** — largely outside
  a single blueprint's design-time spec.

A mapping is a starting point for a questionnaire, not a compliance verdict. Your auditor still
determines whether a control is satisfied in your environment.

## Sources

Mapped against the published structure of NIST AI RMF 1.0 (2023), ISO/IEC 42001:2023, and the
OWASP Top 10 for Agentic Applications (ASI01–ASI10, December 2025). These frameworks are revised
over time — the OWASP agentic list especially is new and evolving — so verify any row against the
current published control text before relying on it in an audit.
