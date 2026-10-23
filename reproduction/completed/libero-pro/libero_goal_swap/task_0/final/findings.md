# Findings: libero-pro/libero_goal_swap/task_0

## Root causes observed

- Initial long posture transit timed out while joints were still moving (seed51,v00/v01). Planning succeeded, but a single fixed final-servo interval was insufficient. Bounded public motion retries and independent measured pose checks enabled progress.
- Wrong grasp roll/contact depth (seed51,v02/v03). A deeply requested grasp stalled against the cabinet; a more outward but wrongly rolled grasp then held the bottle. `close_gripper().ok` was not evidence of holding the requested handle.
- Insufficient articulated travel (seed51,v04). Correct handle grasp visibly opened the middle drawer, but a short depth-relative stroke left the task incomplete.
- Missing public termination handling (seed51,v05). The benchmark succeeded during a pull; the program incorrectly raised on `ExecutionStatus.TERMINATED`, making `program_ok=False` despite `task_success=True`.
- Late pull clearance/stall (development53,55,59,60,63,v06). All five held and opened the middle drawer, but pull3 stabilized15–28mm short while the palm/wrist lay low over the nearby stove. The shared collision interpretation is supported by the successful later wrist-clearance intervention; it is not a claim of privileged contact diagnostics.
- Applying the tilt at initial contact was a measured regression (v07,all15development): the fingers met the closed cabinet face before grasping. Preserve this failed source and its artifacts.
- Residual unseen regimes, measured once without tuning:74/77 stalled at pull2 before reaching the later clearance stage;73 lost the handle during later travel and finished with a partially opened drawer and empty gripper. Occluded post-pull masks were too weak for reliable online grasp verification. These are observed residual regimes, not a predicted held-out rate.

## What fixed them

- Runtime public masks identify three drawer handles; robust point-cloud height ordering selects the middle. The horizontal handle covariance and observed cabinet center derive approach direction and normal sign. No world pose or object dimension is copied into executable constants.
- A horizontal approach with jaws spanning the bar thickness, plus a generic8mm outward surface allowance, fixed the seed51 wrong-object grasp. A fuller stroke based on1.25times observed cabinet depth reached actual seed51 benchmark success in v05. These initial seed51-only iterations are not represented as15-seed measurements.
- Public terminal flags now end normal program control flow. v05seed51 changed from task success/program failure to both fields passing with v06. No success/reward inspection is used inside the policy.
- The first full development baseline v06 scored10/15. Static tilt v07 scored0/15. Restoring the horizontal grasp and first two pulls, then tilting the wrist30degrees **at the current measured EEF position while still holding the drawer handle**, produced v08:15/15task success and15/15program completion. The tilt cost48–61ticks; complete development episodes cost559–604ticks of the1000tick budget. It flipped53,55,59,60,63 and retained all10previous successes.
- v08 was frozen as an exact byte copy before the unseen check. The unseen check produced12/15task success and13/15program completion. The frozen source was not changed or rerun on unseen seeds.

## Development vs unseen

15/15 on development51–65;12/15 on the single unseen66–80 check. The development result does not eliminate early constrained-pull stalls or grasp loss on unseen layouts. Root-owned held-out evaluation has not been performed by this worker.

Selected numbered source: `code/v08_late_tilt.py`; `code/frozen_candidate.py` and `fix_code.py` contain exactly the same bytes. SHA256:`f887cdf810fc31953ed69dd918806bbdc82189e7faa1495332516e1ec89c7e23`.

Immutable development runs: `debug/attempts/v08/<seed>/<run-id>`. Immutable unseen runs: `debug/holdout/<seed>/<run-id>`. `artifact_inventory.json` provides every absolute local/server path and its source hash. `all_camera_video_index.json` and `.md` contain all60camera videos from the30selected runs.

## Generalizable patterns

- Target skill file: `manipulation.md`.
- Trigger: a documented public motion returns an episode terminal/truncated flag during a task-level loop. In the motion helper, `motion` is its public `ExecutionResult` and `result` is the mutable program report; the helper returns a continuation boolean, and callers must return immediately on `False`. A terminal flag is an episode boundary, not proof of success. This block must replace an unconditional exception on any non-ok result.
- Exact working excerpt, copied from the selected program:

```python
if motion.terminated or motion.truncated:
    result["phase"] = "environment_ended"
    result["environment_terminated"] = bool(motion.terminated)
    result["environment_truncated"] = bool(motion.truncated)
    return False
```

- Evidence: seed51v05 had actual task success but program failure; v06 changed public terminal control flow and passed both fields. The same block appears unchanged in v08, whose15development task successes all also have `program_ok=True`. The later wrist-clearance maneuver is documented above as a measured task-specific finding; no context-free grasp/tilt snippet is proposed for promotion.

## Skill report

`skill_report.json` grades every section opened:24sections,10useful,0misleading,0wrong,14not-applicable. Detailed section names and evidence are in that validated file. One new terminal-control pattern is proposed; no shared-library files were edited by the worker.

Canonical skill-library SHA:`91d636a706623f4e`. Earlier local SHA`4ce1afabf2c47cb0` differed only because of Windows CRLF bytes; root normalized newlines to server/Git LF without semantic skill changes. The canonical report passes `campaign.py --validate-skill-report`.

## Blocked modes

- No remaining failure on the15development scenes after v08.
- Untuned unseen residuals: early constrained-pull stall74/77; later grasp loss73. No repair or second measurement was attempted after observing these seeds, as required by isolation protocol.

## Non-privileged API audit

PASS. Source imports only`math` and uses documented public task context, robot state, perception/projection, pose/motion and gripper APIs. Task-dependent centers, axes, normal sign, cabinet depth and target poses derive at runtime. Generic manipulation offsets, angles, quantiles, score filters and step limits are documented in `provenance_audit.md`; no seed branches, fixed world coordinates/dimensions/pixels, native simulator access, success/reward inspection, native assets, baseline programs, real-robot instructions or other task directories were used.

All30selected archived program sources match the frozen/fix hash. All60video files exist and are nonempty. Complete measured development/unseen coverage preceded creation of `fix_code.py`. The worker never launched episodes or accessed coordinator SSH/RPC internals. Root owns batch-equivalence diagnostics and held-out1–50.
