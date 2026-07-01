# AgentAz reference validator

`agentaz-validate.ts` is the reference implementation of AgentAz tier computation. It derives a
Trust Level **band** from a spec's structure rather than reading the declared `trust_level` —
so the same `agentaz.json` yields the same tier for anyone who runs it. That reproducibility is
what makes an AgentAz tier *verifiable* rather than asserted.

```
node reference/validate-tiers.mjs
```

**Status: v2.0.0-draft (advisory).** The validator confirms the declared tier for most blueprints
in this repo. Remaining differences are specs authored in the pre-2.0 `allowed_tools` shape, whose
approval gate is not yet *structurally* encoded; normalizing those to the
`auto_executable_tools` / `approval_required_tools` shape is the v2.0 prerequisite before the
validator becomes authoritative. Cryptographic signing of the computed result follows normalization.

The signed output attests *verifiable classification* — this tier was computed by a pinned
validator from this exact file, unaltered — **not** *verified safety* of the running agent.
