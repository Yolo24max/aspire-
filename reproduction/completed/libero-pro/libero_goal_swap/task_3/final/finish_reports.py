"""Offline final report builder. Never executes robot episodes or changes policies."""
import hashlib
import json
from collections import Counter
from pathlib import Path

root = Path(r"C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_3/retry_02")
def read(relative):
    return json.loads((root/relative).read_text(encoding="utf-8-sig"))
def write(relative, value):
    (root/relative).write_text(json.dumps(value,indent=2),encoding="utf-8")

freeze = read("freeze.json")
status = read("coordinator_status.json")
assert status["phase"] == "artifacts_ready"
assert status["source_hash"] == freeze["source_sha256"]
assert status["seeds"] == list(range(66,81))
assert status["failure_mode"] == freeze["failure_mode"]
dev = read("debug/attempts/v07/worker_summary.json")
unseen = read("debug/holdout/worker_summary.json")
assert dev["count"] == 15 and sorted(row["seed"] for row in dev["rows"]) == list(range(51,66))
assert unseen["count"] == 15 and sorted(row["seed"] for row in unseen["rows"]) == list(range(66,81))
assert len(set(row["seed"] for row in unseen["rows"])) == 15
assert dev["task_passed"] == 15
source = Path(freeze["source"])
source_bytes = source.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == freeze["source_sha256"]
audit = read("policy_source_audit.json")
assert len(audit["policies"]) == 8 and all(row["provenance_static_pass"] for row in audit["policies"])
assert len(set(row["sha256"] for row in audit["policies"])) == 8
assert all(hashlib.sha256(Path(row["source"]).read_bytes()).hexdigest() == row["sha256"] for row in audit["policies"])
assert not (root/"fix_code.py").exists()
(root/"fix_code.py").write_bytes(source_bytes)
assert hashlib.sha256((root/"fix_code.py").read_bytes()).hexdigest() == freeze["source_sha256"]

draft_bytes = (root/"skill_report.draft.json").read_bytes()
(root/"skill_report.json").write_bytes(draft_bytes)
skill_report = read("skill_report.json")
assert skill_report["schema_version"] == 1 and skill_report["task_id"] == 3
assert skill_report["skill_library_sha"] == freeze["skill_library_sha"]
assert skill_report["proposed_new"] == [] and skill_report["proposed_edits"] == []
grades = Counter(item["verdict"] for item in skill_report["consulted"])
validation = read("skill_report_validation.json")
assert validation["result"] == "OK"
validation["final_report"] = "skill_report.json"
validation["final_report_sha256"] = hashlib.sha256(draft_bytes).hexdigest()
validation["final_validation_basis"] = "Final bytes identical to coordinator's officially accepted draft; no report content changed"
write("skill_report_validation.json",validation)

failures = [row for row in unseen["rows"] if not row["task_success"]]
failure_stages = Counter(row["policy_error"] or row["termination"] for row in failures)
residual = "; ".join(f"{name}: seeds {','.join(str(row['seed']) for row in failures if (row['policy_error'] or row['termination']) == name)}" for name in failure_stages) or "none observed in measured development/unseen scenes"
unseen_ok = sum(row["program_ok"] for row in unseen["rows"])
unseen_passed = unseen["task_passed"]
comparison = read("debug/attempts/v07/comparison.json")
assert comparison["before_passed"] == 12 and comparison["after_passed"] == 15
measurement = {
 "schema_version":1,"classification":"user-authorized independent retry_02, not original first-attempt result",
 "benchmark":"libero-pro","suite":"libero_goal_swap","task_id":3,"gpu":0,
 "selected_source":str(source),"selected_source_sha256":freeze["source_sha256"],
 "fix_code":str(root/"fix_code.py"),"failure_mode":freeze["failure_mode"],
 "skill_library_sha":freeze["skill_library_sha"],"provenance_audit":"PASS",
 "source_versions":8,"maximum_mode_versions":3,"first_clean_seed51_version":"v05","first_clean_seed51_steps":822,
 "development":{"seeds":list(range(51,66)),"root":freeze["development_root"],"server_root":freeze["server_development_root"],"task_success":15,"program_ok":15,"count":15},
 "unseen":{"seeds":list(range(66,81)),"root":freeze["unseen_root"],"server_root":freeze["server_unseen_root"],"task_success":unseen_passed,"program_ok":unseen_ok,"count":15,"measurements":1,"residual_regimes":residual},
 "heldout":"1-50 coordinator-only, not accessed","no_tuning_after_freeze":True,
 "skill_report_schema":1,"skill_report_counts":dict(grades),"proposals_new":0,"proposals_edits":0
}
write("measurement_summary.json",measurement)

generalization = f"The selected policy measured 15/15 development and {unseen_passed}/15 unseen task successes; unseen program_ok is {unseen_ok}/15. Residual regime: {residual}. No held-out rate is predicted."
if unseen_passed < 12:
    generalization += " The unseen result is much worse than development: this is an overfitted policy under the measured conditions."
findings = f"""# Findings: libero-pro/libero_goal_swap/task_3, independent retry_02

This is the user-authorized independent retry, not the original first-attempt result. No earlier task strategies, task history, sibling results, native assets, credentials, or controller implementation were read.

## Root causes observed

- Program scope (seed 51, v00): Global AST statement rejected before action. v01 replaced it with explicit helper arguments.
- Slow execution convergence (51, v01/v02): valid public IK; fixed final trajectory wait expired while the elbow continued approaching. Public step trace distinguishes this from the earlier collision hypothesis.
- Drawer end-stop (51, v03): first two pulls succeeded; final requested stroke exceeded observed travel.
- Missing eligible top-down grasp (51, v04): CGN returned three oblique candidates, but top_down selection returned None.
- Bowl retention (v05: 52,62,63; v06: 52,62): bowl remained on the table after nominal lift. Public v06 trace showed large transient lateral travel during a single joint-target lift before the jaw closed empty.
- Post-pull perception (v05/v06: 65): top handle score 0.347656 and lower handle score 0.328125 fell below the 0.35 cutoff despite an open drawer image.
- Frozen unseen residual: {residual}.

## What fixed them

- v01 removed Global, fixing the program rejection without claiming task success.
- v03 used documented solve_ik plus move_to_joints with a larger bounded allowance. Empty-gripper standoff succeeded in 181 ticks.
- v04 limited pull to 0.85 runtime observed cabinet depth and verified opening before grasping.
- v05 added a runtime cloud-derived near-rim fallback: first clean seed 51 success at 822 ticks, followed by 11/15 development task successes.
- v06 changed only contact depth relative to observed upper bowl quantile: 11/15 to 12/15, seed 63 flipped, no regressions.
- v07 combined short lift segments and an independently motivated handle-confidence correction: 12/15 to 15/15, seeds 52,62,65 flipped, no regressions. This is a whole-policy comparison; neither v07 component has isolated causal efficacy established by this experiment.

## Development vs unseen

{generalization}

Selected source: {source}
SHA-256: {freeze["source_sha256"]}
Development root: {freeze["development_root"]}
Unseen root: {freeze["unseen_root"]}
Both sweeps cover all fifteen assigned seeds; every episode ran in a fresh independent process through the root queue. Unseen 66-80 was measured exactly once after freeze. Held-out 1-50 remains coordinator-only.

v00 measured 0/1 at the stricter seed-51 gate; it was not swept across all development seeds. No unmeasured v00 rate is fabricated.

## Generalizable patterns

None proposed for promotion. Applied frozen-library patterns and their limits are graded in skill_report.json. The newly authored rim/lift combination remains single-task evidence; v07's two changes were not independently ablated.

## Skill report

Schema version 1; canonical frozen-library hash {freeze["skill_library_sha"]}. All {len(skill_report["consulted"])} consulted sections are graded: {grades["useful"]} useful, {grades["misleading"]} misleading, {grades["wrong"]} wrong, {grades["not-applicable"]} not-applicable. The official coordinator validator accepted the byte-identical draft. No new or edited skill is proposed.

## Blocked modes

No residual development failures. Bowl-grasp reached its three-version limit and is resolved on development; its limit record is debug/blocked/bowl-grasp.md. Any unseen residual is measurement-only and receives no tuning: {residual}.

## Non-privileged API audit

PASS. Policies use math-only imports and documented public CaP calls. Runtime clouds provide all task-dependent object poses, dimensions, handle order/axis/pull direction and held-offset placement. Generic relative offsets, fractions, quantiles, tolerances and step budgets were tuned from public evidence. No native simulator access, assets, reward/success queries, filesystem/network, reflection or seed-specific branches occur in policy source. All eight immutable numbered sources are hashed and statically audited. The frozen source hash was unchanged throughout unseen measurement; fix_code.py is an exact byte copy made after full coverage and audit.

## Measurement limit

Every successful development run terminated during lowering before release/settling. Outcome program_ok/task_success are both true with task_succeeded. The policy's result records the terminated motion as an error string; this does not change the authoritative successful outcome. No post-release landed-pose efficacy is claimed.

## Artifact index

artifact_index.md and artifact_index.json list all retry-owned runs; video_index.csv contains absolute video paths. measurement_summary.json contains exact local/server roots and source identity. Freeze identity, source/static audit, budget and official report-validation evidence remain in separate files.
"""
(root/"findings.md").write_text(findings,encoding="utf-8")
budget = read("budget.json")
budget["versions"][-1]["status"] = f"selected-dev15of15-unseen{unseen_passed}of15"
budget["completed"] = True
budget["unseen_measurements"] = 1
budget["unseen_task_success"] = unseen_passed
write("budget.json",budget)
with (root/"provenance_audit.md").open("a",encoding="utf-8") as handle:
    handle.write(f"\nFinal audit PASS: development 51-65 and exact-once unseen 66-80 each have 15 unique finalized runs. Frozen SHA-256 {freeze['source_sha256']} is unchanged; all eight source hashes match. fix_code.py is an exact post-coverage byte copy. No held-out access, post-freeze policy change, or new skill proposal.\n")
with (root/"code/CHANGELOG.md").open("a",encoding="utf-8") as handle:
    handle.write(f"\nFROZEN UNSEEN: {unseen_passed}/15 task_success, {unseen_ok}/15 program_ok; residual regime: {residual}. Measured exactly once, no tuning. fix_code.py copied byte-identically after coverage/audit.\n")
state = read("worker_state.json")
state["current_request"] = "Completed exact-once unseen; Stage1 complete"
state["next"] = "Return factual handoff; root alone owns heldout1-50"
state["fix_code"] = "Written as exact frozen-source byte copy after measured coverage and audit"
state["unseen"] = measurement["unseen"]
write("worker_state.json",state)
print(json.dumps({"selected":"v07","sha256":freeze["source_sha256"],"development":"15/15","unseen":f"{unseen_passed}/15","unseen_program_ok":f"{unseen_ok}/15","residual":residual,"skill_sections":len(skill_report["consulted"]),"grades":dict(grades),"fix_code_written":True}))
