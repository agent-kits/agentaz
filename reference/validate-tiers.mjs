// AgentAz tier report (reference) — runs the deterministic validator across this repo.
// Usage from repo root: node reference/validate-tiers.mjs
// Reproducibility is the point: same spec files in -> same tiers out, for anyone.
import { readdirSync, readFileSync } from "node:fs";
const MUTATION = /\b(rollback|delete|deploy|scale|refund|charge|pay|wire|cancel|terminate|drop|truncate|provision|grant|revoke|quarantine|purge|transfer|disable|shutdown|publish|commit|execute|remove|modify[_-]?(config|security|access|record))/i;
const present = (v) => v == null ? false : Array.isArray(v) ? v.length > 0 : typeof v === "object" ? Object.keys(v).length > 0 : typeof v === "string" ? v.trim().length > 0 : !!v;
function computeTier(spec) {
  const tb = spec.tool_boundary ?? {};
  const absent = tb.execution_tools_absent === true;
  const approval = tb.approval_required_tools ?? [];
  const oldShape = !tb.auto_executable_tools && Array.isArray(tb.allowed_tools);
  const autoPool = tb.auto_executable_tools ?? tb.allowed_tools ?? [];
  if (absent && approval.length === 0) return { band: "ADV", computable: !oldShape };
  const riskyAuto = absent ? [] : autoPool.filter((t) => MUTATION.test(t));
  const bounded = present(spec.audit) && present(spec.cost_boundary) && present(spec.loop_boundary);
  if (riskyAuto.length) return { band: bounded ? "A4" : "A5", computable: true };
  if (approval.length) return { band: "A3", computable: true };
  if (!autoPool.length) return { band: "A0", computable: true };
  return { band: "ADV", computable: !oldShape };
}
const bandOf = (t) => { const d = +(String(t).match(/A(\d)/) || [])[1]; return isNaN(d) ? "?" : d <= 2 ? "ADV" : "A" + d; };
const kits = readdirSync("kits");
let agree = 0; const diffs = [];
for (const slug of kits) {
  let spec; try { spec = JSON.parse(readFileSync("kits/" + slug + "/agentaz.json")); } catch { continue; }
  const r = computeTier(spec);
  if (bandOf(spec.trust_level) === r.band) agree++;
  else diffs.push(slug + ": declared " + spec.trust_level + " -> computed " + r.band + (r.computable ? "" : "  [spec gap: pre-2.0 shape]"));
}
console.log("AgentAz validator 2.0.0-draft — " + kits.length + " specs");
console.log("Computed tier matches declared tier: " + agree + "/" + kits.length);
diffs.forEach((d) => console.log("  " + d));
