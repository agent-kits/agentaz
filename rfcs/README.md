# AgentAz RFCs

Substantial changes to the AgentAz specification go through a lightweight, public
**Request for Comments (RFC)** process. Small fixes (typos, clarifications, examples) do
not need an RFC — just a normal change. RFCs are for changes to the *meaning* of the
standard: Trust Level definitions, boundary fields, the schema, or the validator's rules.

The point of this process is transparency and a dated record: every meaningful design
decision is proposed in public, with a timestamp, and its outcome is recorded.

## The steps

1. **Draft.** Copy `0000-template.md` to `NNNN-short-title.md` (next free number) and fill
   it in. Open a pull request adding it, with status **Draft**.
2. **Comment.** The RFC is open for comment for a **minimum of 7 days.** Anyone may respond
   in the pull request.
3. **Decision.** After the comment period, if no blocking concern is raised, the maintainer
   may mark it **Accepted** and merge. Otherwise it is revised, **Rejected**, or
   **Postponed**, with a one-line reason recorded in the RFC.
4. **Implement.** Accepted RFCs are reflected in `SPEC.md`, the schema, and — where relevant
   — the reference validator, and noted in `CHANGELOG.md`.

A silent comment period is a valid outcome: if 7 days pass with no blocking concerns, the
maintainer may accept. The process exists to keep decisions open and on the record, not to
require discussion that a young standard may not yet attract.

## Status values

`Draft` · `Accepted` · `Rejected` · `Postponed` · `Superseded by RFC-NNNN`

## Index

| RFC | Title | Status |
| --- | --- | --- |
| [0001](0001-trust-levels.md) | Trust Levels A0–A5 | Accepted |
