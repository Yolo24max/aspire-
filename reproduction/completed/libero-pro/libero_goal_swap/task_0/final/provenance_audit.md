# Non-privileged API audit: v06

Status: PASS for source/provenance inspection; development sweep pending. This is not a performance claim.

- Authoritative goal is read with `get_task_context().language`. The middle-of-three selector is a task-semantic hypothesis checked against three runtime observed heights, not a seed branch or native object ID.
- Cabinet and handles are obtained through public text segmentation/localization and calibrated mask projection into the public robot base frame. Initial scene coordinates, object dimensions, pixel locations and native assets are absent from executable constants.
- Grasp center is a robust quantile of the selected runtime mask. Horizontal handle axis is calculated from its public point-cloud covariance; normal sign uses the runtime cabinet center. Tool orientation is constructed from these axes.
- Drawer stroke is 1.25 times cabinet point-cloud depth along the derived normal, with generic action-amplitude bounds of 0.20–0.28 m. These bounds are tuned manipulation offsets, not stored object geometry or hidden joint limits. The executed seed-51 stroke was computed at runtime; its observed numeric value is not copied into code.
- Other distances (10 cm staging, 8 mm surface allowance, 12 mm pose tolerance, 2 cm localization slack, 1 cm displacement verification) are generic relative offsets/tolerances tuned from public execution failures. Quantiles, score/point-count guards and clustering separation ratios are generic observation filters. No observed world coordinates, dimensions, seed identities or pixels were copied into constants.
- Steps/retries: per-motion waypoint budgets 100/140, maximum three timeout retries and four pull segments. These tune the control budget and do not manually step native physics.
- The policy imports only `math`. It uses documented observation/perception, `Pose`, `MotionStrategy`, gripper and motion calls. Public terminal/truncated flags end normal control flow; reward and hidden success are not read by the policy.
- No filesystem/network, simulator unwrapping, native reward/geometry, reflection/private attributes, held-out data, baseline programs, real-robot files or other tasks were accessed.
- Runtime task grading is read only from finalized coordinator-owned outcomes. `fix_code.py` remains absent pending full measured development/unseen protocol.

## Skill-library byte normalization
Coordinator normalized only local Windows CRLF to server/Git LF in six shared Markdown files; no semantic skill content changed or proposal was promoted. Canonical/server library SHA is91d636a706623f4e, equivalent to the previously recorded local CRLF4ce1afabf2c47cb0. Final skill report uses the canonical SHA.

## Frozen v08 selection audit
PASS. v08 retains v06 public geometry and terminal handling. It adds a generic30degree rotation at the current measured EEF pose after two runtime-depth-relative pull segments, while holding the drawer handle; quaternion axes remain derived from runtime normal. The change uses documented Pose/motion APIs, no new native state or constants copied from observations. All15 development scenes passed with the exact frozen source SHA256 f887cdf810fc31953ed69dd918806bbdc82189e7faa1495332516e1ec89c7e23. Selection was frozen before any unseen result.

## Final handoff audit
Non-privileged API audit: PASS. All15development and15unseen archived source/program.py files byte-match the frozen v08 and fix_code.py hash f887cdf810fc31953ed69dd918806bbdc82189e7faa1495332516e1ec89c7e23. Exactly one unseen measurement per seed, no unseen-driven changes. fix_code.py was created only after complete measured development/unseen coverage. Root owns batch-equivalence diagnostic and held-out1-50 evaluation; worker did not execute them. artifact_inventory.json lists30 immutable run paths; all_camera_video_index.json/.md list all60 nonempty videos with absolute local/server paths.
