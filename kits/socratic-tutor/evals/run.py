#!/usr/bin/env python3
"""
Safety evals for Socratic Tutor Agent — deterministic, no API key required.

These checks verify the runtime approval gate in run.py: high-risk tools must
be blocked (never auto-executed), and read/low-risk tools must run. This turns
the kit's safety claim into something you can verify in one command:

    python evals/run.py

Exit code 0 = all checks passed.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run import is_gated, run_mock_tool, TOOL_PURPOSES, APPROVAL_REQUIRED  # noqa: E402

checks = []

# 1. Every tool the kit marks approval-required must be gated.
for t in sorted(APPROVAL_REQUIRED):
    checks.append(("approval-required tool '" + t + "' is gated", is_gated(t) is True))

# 2. Clearly destructive verbs are gated even if not explicitly listed (fail-closed).
for t in ["rollback_deploy", "delete_records", "refund_payment", "send_email", "scale_service"]:
    checks.append(("destructive '" + t + "' blocked by safety net", is_gated(t) is True))

# 3. A gated tool returns a 'blocked' result and does NOT execute.
gated_probe = next(iter(sorted(APPROVAL_REQUIRED)), "rollback_deploy")
res = run_mock_tool(gated_probe, {})
checks.append(("gated tool returns blocked status", res.get("status") == "blocked"))

# 4. A non-gated read tool (if any) executes normally.
read_tool = next((n for n in TOOL_PURPOSES if not is_gated(n)), None)
if read_tool:
    res2 = run_mock_tool(read_tool, {})
    checks.append(("read tool '" + read_tool + "' executes", res2.get("status") == "ok"))

passed = sum(1 for _, ok in checks if ok)
print("-" * 60)
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name)
print("-" * 60)
print(str(passed) + "/" + str(len(checks)) + " safety checks passed")
sys.exit(0 if passed == len(checks) else 1)
