# Findings: libero-pro/libero_goal_swap/task_2

## Root causes observed

- **Generated grasp off object (seed51, v00 pilot).** Contact-GraspNet returned one candidate near `(0.364, -0.102, -0.068)` while public bottle points centered near `(0.580, 0.000)` and extended to `z≈0.137`. The program rejected it before moving.
- **Horizontal tool reorientation timeout (seed51, v01 pilot).** The side-grasp wrist rotation stalled after 159 ticks and never contacted the bottle.
- **Over-deep vertical descent (seed51, v02 pilot).** The approach above the bottle converged in 57 ticks, but the intended mid-body pose stalled at the bottle neck after another 126 ticks.
- **Terminal release misclassified (seed51, v03 pilot).** The release caused task success at tick 345. `open_gripper()` returned `terminated`, and v03 raised despite the task having succeeded.

## What fixed them

- Use the public wine-bottle cloud's 5th and 95th Z percentiles, and target 80% of that span with the robot's observed downward tool orientation. v03 succeeded on the seed51 pilot, compared with unsuccessful v00–v02 pilots.
- Derive the cabinet top plane from `localize_object("black cabinet")`, use the median XY of points within 12 mm of its 90th Z percentile, and carry the bottle above the wood rack before lowering. This complete v04 sequence passed 15/15 development seeds; no individual placement ablation was run.
- Treat the public `terminated` flag during release as graceful completion and stop issuing control ticks. v03 was `task_success=true, program_ok=false` on seed51; v04 was true for both on seed51 and all 15 development seeds.
- The campaign's pilot gate prevented full 51–65 sweeps of v00–v03. Those versions are invalid as selected policies; their seed51 records remain in `debug/v00_pilot` through `debug/v03_pilot`.

## Development vs unseen

The frozen v04 program passed **15/15 development seeds 51–65** and **15/15 exact-once unseen-check seeds 66–80**, with `program_ok=true` in all 30. Development runs used 335–355 control ticks and unseen runs 337–354, within the 1000-tick limit. It generalized across the assigned seeded scenes; held-out seeds 1–50 remain coordinator-owned and unmeasured by this worker.

## Generalizable patterns

### grasp.md — Downward neck grasp for upright narrow bottles

Trigger: an upright bottle is visible, a lateral wrist rotation or generated side grasp fails, and the top can be reached from above. `bottle` is the successful `localize_object("wine bottle", ...)` result, `state` is `get_robot_state()`, and `frame` is its base frame. `quantile`, `pose_at`, and `move_checked` are the helpers in the frozen program. The measured seed51 costs were 57 ticks to pre-grasp, 36 to grasp, 14 to close, and 345 for the entire pick/place.

```python
bottle_points = bottle.point_cloud.points
bottle_x = quantile((point[0] for point in bottle_points), 0.5)
bottle_y = quantile((point[1] for point in bottle_points), 0.5)
bottle_bottom = quantile((point[2] for point in bottle_points), 0.05)
bottle_top = quantile((point[2] for point in bottle_points), 0.95)
grasp_mid_z = bottle_bottom + 0.80 * (bottle_top - bottle_bottom)
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
grasp_pose = pose_at((bottle_x, bottle_y, grasp_mid_z), downward, frame)
best_pre = pose_at((bottle_x, bottle_y, grasp_mid_z + 0.12), downward, frame)
open_gripper()
move_checked("pre_grasp", best_pre, 250)
move_checked("grasp", grasp_pose, 180)
closed = close_gripper()
```

Evidence: v00–v02 failed seed51 before completing a grasp; v04 completed seed51 and 51–65 at 15/15. The bottle was in the gripper throughout lift and transport; the held object needed clearance above the wooden rack.

### transport.md — Place on a segmented horizontal fixture top

Trigger: a fixture's visible mask contains side walls and a top surface; the program must place an upright object on that top. `grasp_pose`, `gz`, `bottle_bottom`, and `move_checked` are from the successful grasp above. First reach the pre-grasp stand-off above the bottle, close, and lift while holding it. On seed51, lift, lateral transport, and lowering cost 112, 68, and 49 ticks. The held bottle extends `gz - bottle_bottom` below the end-effector.

```python
cabinet = localize_object("black cabinet", camera_name="agentview", target_frame=frame)
cabinet_points = cabinet.point_cloud.points
surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.012]
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)
grasp_clearance = gz - bottle_bottom
transit_z = max(gz + 0.30, surface_z + grasp_clearance + 0.15)
lift_pose = pose_at((gx, gy, transit_z), grasp_pose.quaternion_wxyz, frame)
move_checked("lift", lift_pose, 200)
above_target = pose_at((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame)
move_checked("transport", above_target, 260)
release_z = surface_z + grasp_clearance + 0.012
release_pose = pose_at((target_x, target_y, release_z), grasp_pose.quaternion_wxyz, frame)
move_checked("lower", release_pose, 200)
```

Evidence: this complete sequence passed all 15 development and 15 unseen seeds. The isolated contribution of the top-plane selector was not separately measured.

## Skill report

See `skill_report.json` for section-by-section grades. The shared localization and geometry guidance was useful. The cylindrical side-grasp section was misleading for this scene: v01 timed out at the horizontal wrist rotation, while the downward neck alternative passed.

## Blocked modes

None. All observed seed51 pilot failure modes were repaired by v04; no development or unseen failure remained.

## Non-privileged API audit

PASS. The selected program uses only task context, robot state, text localization, public point clouds, motion and gripper calls. Bottle/target geometry is recomputed at runtime, with no seed or privileged simulator branch. The frozen source and `fix_code.py` share SHA256 `3629cae5274b16d6dbc704540d35c014084e29decb8fcc9eb5410fb5d190e78f`.
