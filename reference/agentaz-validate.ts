// AgentAz deterministic tier validator — v2.0 (draft / advisory).
//
// computeTier() reads an agentaz.json spec and DERIVES the Trust Level band from
// the spec's structure — it does not read the declared `trust_level`. Same file in,
// same tier out, for everyone: that is what makes a tier verifiable instead of claimed.
//
// Trust Levels classify an agent by its WORST-CASE ACTION = its authority over
// irreversible action. The band is computed from the tool boundary:
//   ADV (A1/A2) — no tool can mutate any external system (advisory / read-only).
//   A3          — consequential tools exist, but every one is behind a human gate.
//   A4          — executes a consequential action autonomously, within declared bounds.
//   A5          — executes a consequential action autonomously, with no bounds or gate.
//   A0          — no tools at all.
//
// NOTE (honest scope): the A1 vs A2 distinction (pure read vs. produces a
// recommendation) is an authoring judgment, not structurally computable — both have
// no mutating tools — so the validator reports the ADV band rather than inventing a
// split the spec can't support.

export const AGENTAZ_VALIDATOR_VERSION = "2.0.0-draft";

// Verbs that denote a consequential, externally-visible mutation. Intentionally
// NARROWER than the Scanner's warn-level regex: the Scanner can afford false
// positives (it only warns); a tier computation cannot, because over-flagging a
// content verb like "write_description" would mislabel an advisory agent as autonomous.
const MUTATION_VERB =
  /\b(rollback|delete|deploy|scale|refund|charge|pay|wire|cancel|terminate|drop|truncate|provision|grant|revoke|quarantine|purge|transfer|disable|shutdown|publish|commit|execute|remove|modify[_-]?(config|security|access|record))/i;

type ToolBoundary = {
  auto_executable_tools?: string[];
  approval_required_tools?: string[];
  allowed_tools?: string[];
  execution_tools_absent?: boolean;
};
type Spec = {
  tool_boundary?: ToolBoundary;
  audit?: unknown;
  cost_boundary?: unknown;
  loop_boundary?: unknown;
};

export type TierBand = "A0" | "ADV" | "A3" | "A4" | "A5";

export type TierResult = {
  band: TierBand;
  version: string;
  basis: string;
  /** True when the spec's tool_boundary is rich enough to compute a tier with confidence. */
  computable: boolean;
};

function present(v: unknown): boolean {
  if (v == null) return false;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v as object).length > 0;
  if (typeof v === "string") return v.trim().length > 0;
  return Boolean(v);
}

export function computeTier(spec: Spec): TierResult {
  const tb = spec.tool_boundary ?? {};
  const absent = tb.execution_tools_absent === true;
  const approval = tb.approval_required_tools ?? [];
  // Old-shape specs express tools as `allowed_tools` with no auto/approval split.
  const usingOldShape = !tb.auto_executable_tools && Array.isArray(tb.allowed_tools);
  const autoPool = tb.auto_executable_tools ?? tb.allowed_tools ?? [];
  const v = AGENTAZ_VALIDATOR_VERSION;

  // No execution tools at all → nothing can mutate the world → advisory.
  if (absent && approval.length === 0) {
    // If the kit is old-shape AND claims A3-style action elsewhere, the gate isn't
    // encoded structurally — flag as not-confidently-computable.
    return {
      band: "ADV",
      version: v,
      basis: "No execution tools present; agent cannot mutate any external system.",
      computable: !usingOldShape,
    };
  }

  const riskyAuto = absent ? [] : autoPool.filter((t) => MUTATION_VERB.test(t));
  const bounded = present(spec.audit) && present(spec.cost_boundary) && present(spec.loop_boundary);

  if (riskyAuto.length > 0) {
    return {
      band: bounded ? "A4" : "A5",
      version: v,
      basis: `Autonomous consequential tool(s) [${riskyAuto.join(", ")}] run without a gate${
        bounded ? ", within declared cost/loop/audit bounds." : " and without declared bounds."
      }`,
      computable: true,
    };
  }
  if (approval.length > 0) {
    return {
      band: "A3",
      version: v,
      basis: `Consequential tool(s) exist but all are behind a human gate [${approval.join(", ")}].`,
      computable: true,
    };
  }
  if (autoPool.length === 0) {
    return { band: "A0", version: v, basis: "No tools declared.", computable: true };
  }
  return {
    band: "ADV",
    version: v,
    basis: "Tools present but none mutate an external system; advisory.",
    computable: !usingOldShape,
  };
}
