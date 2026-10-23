# Non-privileged API and provenance audit
FINAL STATUS: PASS

## Frozen selection and measured coverage
- Independent user-authorized retry_02; eight numbered policy sources total, no overwritten source path.
- Selected source: code/v07_staged_lift_confidence.py.
- SHA-256: 11fdfca995faf2c82c7eee9f1174ee2f31c6e9e696ac055ada4dc2fd41fff026.
- Frozen before unseen measurement. Development 51-65: 15/15 task_success and 15/15 program_ok.
- Unseen 66-80: exactly one run directory per seed, 15/15 task_success and 15/15 program_ok.
- Source hash remained unchanged; fix_code.py was created only after coverage and is an exact byte copy.
- Held-out 1-50 was never accessed or requested by this worker. Root alone owns Stage2.
- Canonical frozen skill-library SHA: eb66214c23cc9d5a, supplied by coordinator and confirmed by official report validation.

## Read and execution scope
Only this retry directory, its frozen shared_skills, docs/api-reference.md and docs/run-artifacts.md were read. Initial task evidence was the copied public seed51 language, robot state and scene keyframe. One observation-only runtime geometry probe used public APIs. No parent or sibling task data, prior chats/strategies, example/baseline code, native assets, credentials, implementation or controller internals were read. All episodes were requested through the root-owned queue and executed in fresh independent processes.

## Constant and geometry provenance
- Public task language identifies top drawer and bowl; top handle uses runtime mask-cloud height bounded against observed cabinet height.
- Runtime point clouds provide object positions and dimensions. XY covariance gives the handle axis; the observed cabinet center signs the pull normal.
- Drawer stroke is a fraction of runtime observed cabinet depth. Placement uses measured held-bowl/EEF offsets and observed handle-layer spacing.
- The bowl fallback uses a generic downward, radial-jaw strategy in the public robot base frame; its contact position derives from the runtime bowl cloud.
- Tuned values are generic relative offsets, score/point guards, quantiles, tolerances, step caps and dimensionless fractions.
- No observed world coordinate, object dimension, pixel location, seed identity, raw reward or success value was copied into executable constants or branches.

## API and source audit
Math is the only policy import. Static auditing of all eight numbered sources found no private names/attributes or forbidden calls. Policies use documented public CaP observations, perception, grasping, IK, joint motion, gripper and normalized action APIs. No native simulator access, raw reward/success query, filesystem/network or reflection occurs in policy source. v00's Global statement was a sandbox rejection before action, recorded separately; v01 removed it with explicit helper arguments.

## Measurement interpretation
The v07 development comparison changes two behaviors and is reported only as a whole-policy result. Successful episodes terminate during lowering before release/settling; no post-release landed-pose efficacy is claimed. No residual failure regime was observed on the measured development/unseen sets, and no held-out rate is predicted. No policy tuning or new skill proposal followed freeze/unseen measurement.

Supporting files: freeze.json, policy_source_audit.json, source_hashes.json, frozen_library_manifest.json, measurement_summary.json, budget.json, skill_report_validation.json and artifact_index.json.
Coordinator final handoff confirmation: all30 source/settings/video records PASS; official final skill_report validator OK; root provenance review PASS.
