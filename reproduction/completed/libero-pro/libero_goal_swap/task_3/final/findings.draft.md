# Findings draft: libero-pro/libero_goal_swap/task_3, independent retry_02
This is the user-authorized independent retry, not the original first-attempt result. No prior task strategies or results were read. FINAL DEVELOPMENT/UNSEEN SELECTION PENDING.

## Root causes observed
- Program scope, seed51 v00: Global AST statement rejected before any simulator ticks. Authored independently; public docs did not enumerate that statement restriction.
- Execution convergence, seed51 v01/v02: valid public IK solutions; a final trajectory waypoint's120-tick wait expired while an elbow continued moving toward its target. Public recorded joint errors declined materially over time. Initial low-transit collision hypothesis was revised after v02 high free-space failure showed the same slow progression.
- Drawer end-stop, seed51 v03: successful initial pulls followed by overlong final target; image showed open drawer, measured EEF stopped short of requested stroke.
- Missing eligible grasp, seed51 v04: CGN returned three oblique candidates, but top_down selector yieldedNone.
- Bowl retention: v05 failed52,62,63 after nominal lift; bowl remained on table. v06 deeper contact recovered63 but52,62 persisted. Public52 v06 EEF trace shows a large lateral excursion during the single joint-target lift, followed by jaws closing empty.
- Post-pull handle confidence: v05/v06 failed65 after opening the drawer. Correct top handle mask scored0.347656, below policy0.35 cutoff; lower handle scored0.328125. The image showed the top drawer open.

## What fixed them
- v01 removed Global via explicit helper arguments (program rejection fixed; manipulation still failed).
- v03 uses documented solve_ik followed by move_to_joints with a larger bounded servo allowance; handle standoff took181 ticks and succeeded. This is an empty-gripper convergence measurement.
- v04 shortened pull to0.85 runtime observed cabinet depth; all drawer motions and measured opening succeeded on51.
- v05 adds a cloud-derived near-rim top-down fallback. First clean51 success occurred at822 ticks; the subsequent full51-65 sweep measured11/15 successes and15/15 program_ok.
- v06 changes only contact depth relative to the observed upper bowl quantile:11/15→12/15, flipped63, no regressions.
- v07 (pending) combines staged lift and independent handle confidence correction. Its result must be described as a whole-policy comparison, never isolated causal proof for either component.

## Development vs unseen
v05:11/15 development; v06:12/15 development. v07 pending. Unseen66-80 untouched. v00 was0/1 at seed51 gate; full v00 development was intentionally not run under the stricter retry gate.

## Generalizable patterns
No new skill promotion proposed. Applied frozen-library patterns and their limits are graded separately. New task-specific rim/lift behavior has no independent transfer evidence.

## Skill report
The draft grades all27 opened library sections, includes canonical frozen-library SHA eb66214c23cc9d5a, and has empty proposal arrays. Coordinator's official report validator returnedOK.

## Blocked modes
Pending final v07. Policy budget is fully committed at8/8; bowl-grasp has reached its third version and no new policy source may be written.

## Non-privileged API audit
PASS. Public-only initial observations and runtime CaP API outputs; math-only imports; no native state, assets, rewards/success queries, filesystem/network or reflection in policies. All object poses/dimensions derive at runtime. Tuned quantities are generic relative offsets, fractions, quantiles, tolerances and budgets. Static audit covers all8 sources; v00 sandbox rejection is recorded separately.

## Important measurement limit
Successful runs terminate during lowering, before release/settling. Outcome.json has program_ok=true/task_success=true and task_succeeded; policy result catches the terminated motion as an error string. These are valid benchmark successes under the requested gate. No post-release landed-pose efficacy is claimed.
