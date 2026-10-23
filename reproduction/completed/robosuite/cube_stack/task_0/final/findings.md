# Findings: robosuite/cube_stack/task_0

## Root causes observed
- Adjacent-cube interference: v00 failed103/108 during descent with open fingers contacting the taller green neighbor; public motion residual about0.031m. Seed113 completed but final images showed displaced green and red cubes separated; target displacement is the supported hypothesis, not a privileged-state fact.
- Rotated-pregrasp convergence: v01 geometric yaw adjustment produced10 initial pregrasp timeouts103,108,109,110,113,114,118,119,123,124. Public103 trace reported146 ticks and0.247m residual; final keyframe showed partial wrist rotation above the scene. No provider or segmentation failure was implicated.

## What fixed them
- v00:22/25 task success,23/25 program_ok.
- v01:15/25 task/program success. Runtime cube-to-cube direction rotates the observed tool opening axis perpendicular to the neighbor. This regressed seven previously successful seeds; rotation alone was insufficient.
- v02:25/25 task/program success. Only changed the move helper to replan/reissue the same perception-derived pose after typed timeout, bounded at3 calls, with no retry for other failure statuses. All10 v01 failures flipped; no regression. Original103/108/113 failures also flipped. Public final images103/113 show released red cube on green. Selected development total409-533 ticks, not close to the1000-tick ceiling.
- Conservative budget accounting: v00,v01,v02 count as3 unique sources and3/3 versions for adjacent interference; no relabeling or further attempts.

## Development vs unseen
25/25 development101-125,25/25 program_ok;5/5 unseen126-130,5/5 program_ok. Unseen measured exactly once after source/library SHA freeze;419-634 ticks. The observed partition generalizes, though it is a five-scene measurement. No source changed after freeze; heldout1-100 remains coordinator-owned.

## Generalizable patterns
- Target skill: transport.md. Trigger: an empty-gripper rotated free-space pregrasp has a typed timeout and a partially reached pose, with no observed obstacle contact. Keep the same public position/orientation/frame; this is a controller convergence remedy, not a collision remedy. In the snippet, position is the existing runtime target, downward is the observed tool quaternion after runtime yaw adjustment, frame is the public base frame, and report starts with motions=[]. The pregrasp is0.15m above the perception-derived cube grasp. Call cap250 for pregrasp. Each call costs up to cap ticks and3 calls can consume750 ticks; measured full selected policies409-533 dev and419-634 unseen, with jaws empty during pregrasp and carrying the cube only after closing. Preserve the whole-episode1000 ceiling.

```python
def move(position, cap=220):
    for attempt in range(3):
        motion = move_to_pose(Pose(position, downward, frame), tolerance=0.015, max_steps=cap)
        report["motions"].append(motion)
        if motion.ok:
            return
        if motion.status != "timeout":
            break
    raise ValueError("motion failed after bounded convergence retries")
```

Evidence: v01 to v02 changed only this helper;15/25 to25/25, flipping103,108,109,110,113,114,118,119,123,124. This is a proposal, not independently verified or promoted. The neighbor rotation and cloud top-plane selection are retained task-level observations; no standalone general promotion claim is made for them.

## Skill report
23 consulted sections:12 useful,11 not-applicable,0 misleading,0 wrong. Every opened section is graded in skill_report.json. Useful guidance: authoritative scene language, finalized artifact triage, sandbox constraints; localization guards/prompts/public surface geometry; staged width-relative cube grasp, contact-aware closure and public lift verification; explicit post-release holds. Bottle/cabinet/container and pre-probe patterns were skipped. Whole-policy success records application, not isolated causal skill efficacy. One new transport proposal,0 edits. Official campaign.py validator:OK, library SHA aad60a7cd5c26ab6.

### Consulted section grades

- task-exploration.md / Initial Scene Analysis: useful - Applied to authoritative public seed101 scene and immutable pilot; v00 clean success on101, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- task-exploration.md / Triage from disk, not from a `run:` log line: useful - Applied to authoritative public seed101 scene and immutable pilot; v00 clean success on101, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- task-exploration.md / Sandbox constraints when writing probes: useful - Applied to authoritative public seed101 scene and immutable pilot; v00 clean success on101, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- task-exploration.md / Wrap every run in `timeout` — orphans starve the GPU: not-applicable - Single GPU controller owns all simulation launches and resource admission; worker never launched a simulator.
- localize.md / Standard Localization Helper: useful - Public red cube and green cube localization before grasp, cloud guards and top quantiles used; seed101 pilot clean success, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- localize.md / Key Signals: useful - Public red cube and green cube localization before grasp, cloud guards and top quantiles used; seed101 pilot clean success, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- localize.md / Prompting Strategy: useful - Public red cube and green cube localization before grasp, cloud guards and top quantiles used; seed101 pilot clean success, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- localize.md / Placement Z Notes: useful - Public red cube and green cube localization before grasp, cloud guards and top quantiles used; seed101 pilot clean success, no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- localize.md / Prompt Registry: not-applicable - Registry bottle/cabinet entries and same-shape candidate selector were unnecessary; distinct red/green prompts gave high confidence on public seed101.
- localize.md / Disambiguation: Two Similar Objects in Scene: not-applicable - Registry bottle/cabinet entries and same-shape candidate selector were unnecessary; distinct red/green prompts gave high confidence on public seed101.
- grasp.md / Standard Pick-and-Place Template: useful - Applied staged approach, width-relative grasp depth0.65, close_gripper and lift verification; v00 seed101 grasp verified and task succeeded in473 ticks; no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- grasp.md / Key Conventions: useful - Applied staged approach, width-relative grasp depth0.65, close_gripper and lift verification; v00 seed101 grasp verified and task succeeded in473 ticks; no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- grasp.md / Visible cube width-relative grasp depth: useful - Applied staged approach, width-relative grasp depth0.65, close_gripper and lift verification; v00 seed101 grasp verified and task succeeded in473 ticks; no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- grasp.md / Object Geometry Utilities: useful - Applied staged approach, width-relative grasp depth0.65, close_gripper and lift verification; v00 seed101 grasp verified and task succeeded in473 ticks; no isolated ablation. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.
- grasp.md / Cylindrical Side Grasp (bottles, cans): not-applicable - Task objects are cubes, so cylindrical side or bottle-neck grasps were not used.
- grasp.md / Downward Bottle Neck Grasp: not-applicable - Task objects are cubes, so cylindrical side or bottle-neck grasps were not used.
- transport.md / Waypoint Sequences: not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Pre-Probe IK Conditioning: not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Safe Transit (Lateral Escape Before Lift): not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Placement Approach: not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Segmented Fixture Top Placement: not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Basket / Container Placement: not-applicable - No low-Z IK failure, lateral trapping, cabinet, or container observed; cube-specific top-plane placement derived from runtime clouds, without target pre-probing.
- transport.md / Physics Settling After Release: useful - Used explicit measured joint holds with open normalized gripper for30 ticks after retreat; v00 seed101 stack succeeded; no isolated settling ablation. Constructor follows docs/api-reference.md with only mode,target,gripper_position. Selected v02 measured25/25 development and25/25 program success; this is whole-policy application evidence, not an isolated skill ablation.

## Blocked modes
none. Adjacent-interference allocation exhausted but mode resolved in v02. Root resource waits were not policy failures; no simulator/harness retry or environment alteration was performed by the worker.

## Non-privileged API audit
PASS. See api_audit.md. Only math import and documented public functions/constructors. Every task-dependent center, width, height and quaternion derives from runtime perception or robot state. Numerical constants are relative clearances, quantiles, tolerances and bounded tick/call budgets. No fixed world poses/dimensions/pixels, seed branches, assets, simulator state, raw success/reward or introspection. Only own artifacts and curated skills were consulted. Exact source SHA7fc56577e5ba890f62f109f65e544664d73fc8448ee9403e1673df040cb518db frozen before unseen; fix_code.py matches exactly. Root owns Stage2, independent audit/verifier and promotion.
