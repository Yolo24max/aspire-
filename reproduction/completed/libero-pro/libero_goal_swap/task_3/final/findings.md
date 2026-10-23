# Findings: libero-pro/libero_goal_swap/task_3, independent retry_02

This is the user-authorized independent retry, not the original first-attempt result. No earlier task strategies, task history, sibling results, native assets, credentials, or controller implementation were read.

## Root causes observed

- Program scope (seed 51, v00): Global AST statement rejected before action. v01 replaced it with explicit helper arguments.
- Slow execution convergence (51, v01/v02): valid public IK; fixed final trajectory wait expired while the elbow continued approaching. Public step trace distinguishes this from the earlier collision hypothesis.
- Drawer end-stop (51, v03): first two pulls succeeded; final requested stroke exceeded observed travel.
- Missing eligible top-down grasp (51, v04): CGN returned three oblique candidates, but top_down selection returned None.
- Bowl retention (v05: 52,62,63; v06: 52,62): bowl remained on the table after nominal lift. Public v06 trace showed large transient lateral travel during a single joint-target lift before the jaw closed empty.
- Post-pull perception (v05/v06: 65): top handle score 0.347656 and lower handle score 0.328125 fell below the 0.35 cutoff despite an open drawer image.
- Frozen unseen residual: none observed in measured development/unseen scenes.

## What fixed them

- v01 removed Global, fixing the program rejection without claiming task success.
- v03 used documented solve_ik plus move_to_joints with a larger bounded allowance. Empty-gripper standoff succeeded in 181 ticks.
- v04 limited pull to 0.85 runtime observed cabinet depth and verified opening before grasping.
- v05 added a runtime cloud-derived near-rim fallback: first clean seed 51 success at 822 ticks, followed by 11/15 development task successes.
- v06 changed only contact depth relative to observed upper bowl quantile: 11/15 to 12/15, seed 63 flipped, no regressions.
- v07 combined short lift segments and an independently motivated handle-confidence correction: 12/15 to 15/15, seeds 52,62,65 flipped, no regressions. This is a whole-policy comparison; neither v07 component has isolated causal efficacy established by this experiment.

## Development vs unseen

The selected policy measured 15/15 development and 15/15 unseen task successes; unseen program_ok is 15/15. Residual regime: none observed in measured development/unseen scenes. No held-out rate is predicted.

Selected source: C:\Users\24683\Documents\ChatGPT\RSI\ASPIRE\outputs\runs\2026-10-19_16-40-30_goal-swap-server\libero-pro\libero_goal_swap\task_3\retry_02\code\v07_staged_lift_confidence.py
SHA-256: 11fdfca995faf2c82c7eee9f1174ee2f31c6e9e696ac055ada4dc2fd41fff026
Development root: C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_3/retry_02/debug/attempts/v07
Unseen root: C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_3/retry_02/debug/holdout
Both sweeps cover all fifteen assigned seeds; every episode ran in a fresh independent process through the root queue. Unseen 66-80 was measured exactly once after freeze. Held-out 1-50 remains coordinator-only.

v00 measured 0/1 at the stricter seed-51 gate; it was not swept across all development seeds. No unmeasured v00 rate is fabricated.

## Generalizable patterns

None proposed for promotion. Applied frozen-library patterns and their limits are graded in skill_report.json. The newly authored rim/lift combination remains single-task evidence; v07's two changes were not independently ablated.

## Skill report

Schema version 1; canonical frozen-library hash eb66214c23cc9d5a. All 27 consulted sections are graded: 14 useful, 0 misleading, 0 wrong, 13 not-applicable. The official coordinator validator accepted the byte-identical draft. No new or edited skill is proposed.

## Blocked modes

No residual development failures. Bowl-grasp reached its three-version limit and is resolved on development; its limit record is debug/blocked/bowl-grasp.md. Any unseen residual is measurement-only and receives no tuning: none observed in measured development/unseen scenes.

## Non-privileged API audit

PASS. Policies use math-only imports and documented public CaP calls. Runtime clouds provide all task-dependent object poses, dimensions, handle order/axis/pull direction and held-offset placement. Generic relative offsets, fractions, quantiles, tolerances and step budgets were tuned from public evidence. No native simulator access, assets, reward/success queries, filesystem/network, reflection or seed-specific branches occur in policy source. All eight immutable numbered sources are hashed and statically audited. The frozen source hash was unchanged throughout unseen measurement; fix_code.py is an exact byte copy made after full coverage and audit.

## Measurement limit

Every successful development run terminated during lowering before release/settling. Outcome program_ok/task_success are both true with task_succeeded. The policy's result records the terminated motion as an error string; this does not change the authoritative successful outcome. No post-release landed-pose efficacy is claimed.

## Artifact index

artifact_index.md and artifact_index.json list all retry-owned runs; video_index.csv contains absolute video paths. measurement_summary.json contains exact local/server roots and source identity. Freeze identity, source/static audit, budget and official report-validation evidence remain in separate files.
