# Findings: libero-pro/libero_goal_swap/task_4

## Root causes observed

- grasp retention / IK (seed 51): CGN top-down selection returned no candidate in v00; the geometry fallback, handcrafted side orientation, and CGN poses either stalled during approach or failed to retain the bowl.
- task predicate (seed 51): v01, v05, and v07 completed their public motion and gripper calls but `task_success` stayed false. v05 and v07 keyframes show the bowl still on the tabletop after lift.
- budget gate: the controller rejected v08 before launch with `AssertionError('Policy version budget exhausted (8)')`.

## What fixed them

Nothing reached task success. v05 and v07 improved `program_ok` to true on seed 51, but both remained 0/1 task success; v06 added post-lift verification but its lower descent timed out. The best measured source by the tie-break rules is v05 because it has `program_ok: true` and is simpler than v07.

## Development vs unseen

0/15 development seeds were measured as a sweep, and 0/15 unseen-check seeds were measured. Only the required seed-51 pilot was run for each numbered request. The development gate never passed, and no unseen measurement was authorized by the controller.

## Generalizable patterns

none

## Skill report

See `skill_report.json`. The shared localization and geometry utilities produced stable runtime-derived bowl and cabinet geometry. The standard downward grasp structure and close command completed calls but did not retain this bowl on seed 51; the library's post-lift verification warning was useful for identifying that failure.

## Blocked modes

grasp-retention → downward top-down contact reached the bowl but did not retain it; CGN and side variants were unreachable or unverified, and the official eight-version budget was exhausted.

## Non-privileged API audit

PASS. The selected v05 source and `fix_code.py` use only the public localization, robot-state, pose, gripper, and motion contracts. Prompts, points, target planes, and all task geometry are obtained at runtime; no held-out data, private simulator API, native simulator state, or sibling task artifact was used.
