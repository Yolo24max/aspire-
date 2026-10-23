# Skills Under Test

Proposals from `libero_goal_swap/task_2`. **They are staged here and are deliberately NOT in the shared library** — whether they get promoted is what your verdict decides. Do not go looking for them under `skills/`; this file is their only home. Re-solve the task from the library PLUS this file, without seeing the author's program.

The task's own program scores **50/50** held-out. Read that before drawing conclusions from your own score: on a task whose residual failure is kinematic, a low score of your own is expected and is **not** by itself a refutation. Judge each proposal on whether it transmits and whether its mechanism reproduces.

---

## 1. → `grasp.md` — Downward Bottle Neck Grasp

**Trigger.** Use when an upright wine bottle is visible from agentview, a side wrist rotation is too costly or fails, and the current end-effector points downward. `quantile` is the helper in grasp.md Standard Pick-and-Place Template. The bottle is localized with the literal prompt in the snippet; pre-grasp is 0.12 m above the observed 80%-height neck target. Expect about 57+36+14 ticks for approach, contact and close on seed51; verify object retention after lift.

```python
state = get_robot_state()
frame = state.base_frame
bottle = localize_object("wine bottle", camera_name="agentview", target_frame=frame)
if not bottle.ok or len(bottle.point_cloud.points) < 100:
    raise ValueError("wine bottle not localized")
points = bottle.point_cloud.points
x = quantile((point[0] for point in points), 0.5)
y = quantile((point[1] for point in points), 0.5)
low = quantile((point[2] for point in points), 0.05)
high = quantile((point[2] for point in points), 0.95)
z = low + 0.80 * (high - low)
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
pre = Pose((x, y, z + 0.12), downward, frame)
grasp = Pose((x, y, z), downward, frame)
open_gripper()
if not move_to_pose(pre, tolerance=0.025, max_steps=250).ok:
    raise ValueError("pre-grasp failed")
if not move_to_pose(grasp, tolerance=0.025, max_steps=180).ok:
    raise ValueError("grasp failed")
close_gripper()
```

**Evidence.** v01 side reorientation timed out after 159 ticks on seed51; v04 downward neck grasp succeeded on seed51 and all development 51–65 (15/15) and unseen 66–80 (15/15).

---

## 2. → `transport.md` — Segmented Fixture Top Placement

**Trigger.** Use after grasping an upright bottle to place on a flat drawer cabinet top. `frame` is get_robot_state().base_frame; `quantile` is the standard grasp.md helper; `gx`, `gy`, `gz` are the measured grasp end-effector position, `bottle_bottom` is the bottle cloud's 5th Z percentile, and `grasp_pose` is the successful grasp pose. The snippet defines its own guarded `move_checked` wrapper and uses the public `Pose` constructor. Start from the 0.12 m vertical pre-grasp stand-off, close, then lift while holding the bottle; its lowest point is `grasp_clearance` below the end-effector. Seed51 lift, lateral transit and descent cost 112, 68 and 49 ticks.

```python
def move_checked(stage, pose, cap):
    answer = move_to_pose(pose, tolerance=0.025, max_steps=cap)
    if not answer.ok:
        raise ValueError(stage + " failed")
cabinet = localize_object("black cabinet", camera_name="agentview", target_frame=frame)
if not cabinet.ok or len(cabinet.point_cloud.points) < 500:
    raise ValueError("cabinet not localized")
cabinet_points = cabinet.point_cloud.points
surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.012]
if len(top_points) < 100:
    raise ValueError("cabinet top plane not found")
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)
grasp_clearance = gz - bottle_bottom
transit_z = max(gz + 0.30, surface_z + grasp_clearance + 0.15)
move_checked("lift", Pose((gx, gy, transit_z), grasp_pose.quaternion_wxyz, frame), 200)
move_checked("transport", Pose((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame), 260)
release_z = surface_z + grasp_clearance + 0.012
move_checked("lower", Pose((target_x, target_y, release_z), grasp_pose.quaternion_wxyz, frame), 200)
```

**Evidence.** The complete frozen v04 sequence placed the bottle on the cabinet in development 51–65 (15/15) and exact-once unseen 66–80 (15/15); no isolated top-plane ablation was performed.

---

## Edits

### `localize.md` § Prompt Registry

**Change.** Add `wine bottle` for an upright dark bottle and `black cabinet` for the closed drawer cabinet; segment before grasp, then verify the bottle and cabinet clouds using public depth. The seed51 top mask scores were about 0.926 and 0.455 respectively.

*Why:* Both literal prompts localized the intended objects on seed51 and the complete selected policy passed 15/15 development and 15/15 unseen seeds.

### `grasp.md` § Cylindrical Side Grasp (bottles, cans)

**Change.** Describe the downward-neck alternative when a side wrist pose times out: retain the measured initial downward end-effector quaternion and target 80% of the observed bottle Z span with a 0.12 m vertical stand-off. Point to the proposed Downward Bottle Neck Grasp snippet.

*Why:* On seed51 the horizontal side-grasp wrist move timed out after 159 ticks before contact; the downward alternative reached and carried the bottle, and v04 scored 15/15 development plus 15/15 unseen.


---

## Standing disputes — report on any your scene touches

- **Identity selectors.** `localize.md` orders them: the relation the instruction states, else the
  sign of the support gap, else the candidate's own height, else proximity. Tasks measured these
  head to head and got different answers on different scenes. **Compute all of them in-program and
  report the column.**
- **The near-base descent.** Two regimes with opposite remedies — settle-time (more ticks fix it)
  and a servo wall (they do not). The `>= ~50 ticks` duration bar is RETIRED; so is the
  outward-drift test, which one task measured backwards. What survives is **where it froze**
  (achieved z against commanded z) and **which axis is short**. Report both.
- **The jaw as a slip test.** Five numeric bars have been tried and all five failed; a jaw that
  *rises* is a distinct signal (something is prying it). If you deliberately spoil a grasp, report
  the jaw at close / after lift / before place for both it and a good one.
- **Release height.** Measure your band and grade on the landed pose, not the pass count.
- **The first `move_to_pose`.** `tries=3` and stage only if all three fail. Report what yours does.

Verifications have refuted claims outright while their symptoms held, and found helper functions
that entries CALL and that were defined nowhere. Treat "it passed" as the beginning of the question.
