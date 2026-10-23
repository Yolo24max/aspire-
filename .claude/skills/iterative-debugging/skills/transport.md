---
name: transport
description: Motion patterns for moving objects between locations — multi-step waypoints, safe transit sequences, staged Cartesian moves, collision avoidance during transport. Grows through experiment.
---

# Transport — Motion Patterns

> This skill covers **how to move** once an object is grasped: waypointing, safe transit,
> intermediate stops, and collision avoidance. Discovered through experiment — add each
> validated pattern as its own subsection (trigger → code → evidence), modeled on
> *Pre-Probe IK Conditioning* below; tables are only for one-line lookups.

---

## Waypoint Sequences

Add a subsection per multi-step motion pattern that prevents collisions, slip, or IK failures
during transport (trigger condition → waypoint code → why it works + evidence). Use the table
only for one-line pointers to those subsections.

| Pattern | Trigger | Section |
|---|---|---|
| IK pre-probe | Low-Z placement target | *Pre-Probe IK Conditioning* below |

---

## Bounded public pose convergence after a rotated pregrasp timeout

**Trigger.** After a runtime-derived jaw yaw change, a public Cartesian motion toward
a free-space pregrasp stand-off has returned a typed timeout at a partially reached
pose. Reissue the same target only for `timeout`; stop for other failure statuses.
Use the current observed pose and a stand-off0.15m above the cloud-derived grasp.
The jaws are empty during this approach. Do not retry a known obstructed contact.

`position`, `downward` and `frame` are the existing public perception-derived
target, orientation and robot base frame. Initialize `report = {"motions": []}`
before calling this helper; it records every public result.

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

For the pregrasp call use `cap=250`. Each call costs at most `cap` ticks;
three calls can consume750 ticks, so preserve the1000-tick whole-episode ceiling.
There is no carrying motion in this free-space pregrasp scope.

**Evidence.** A fresh independent cube_stack verifier applied the helper verbatim
and passed4/5 development seeds101–105 on its first policy. Seed102 exercised the
intended branch: a144-tick pregrasp timeout followed by an identical target
retry succeeded in29 ticks. The four successful whole policies cost423–477 ticks.

**Limits.** The same seed later failed at contact-stage descent despite three
timeout retries. This entry provides bounded free-space convergence attempts,
not a contact-convergence or collision guarantee, a yaw estimator, or a complete
placement recipe. Verification measures transmission on this task; it is neither
a causal ablation nor evidence of transfer to another task.

---

## Pre-Probe IK Conditioning

Before grasping, pre-visit the placement target at multiple approach heights. This seeds the
IK solver so it stays on the correct branch when placing after the grasp.

```python
# BEFORE grasping, probe the target at decreasing heights:
for probe_z in (target_z + 0.08, target_z + 0.06, target_z + 0.04, target_z + 0.02):
    move_to_pose(Pose((target_x, target_y, probe_z), downward, base_frame),
                 tolerance=0.03, max_steps=200)
go_home()
# NOW grasp — IK is conditioned for placement
```

**Why it works**: IK solvers maintain local branch continuity from their last configuration.
Visiting the placement target before grasping seeds the solver on the branch that can reach
that XY at low Z — so after grasp + home reset, the arm finds the same branch.

**When to use**: Any task where the placement target is at low Z with an observed XY. When
branch conditioning is not enough, request collision-aware planning explicitly:
`move_to_pose(..., strategy=MotionStrategy(trajectory_planner="curobo"))`.

---

## Safe Transit (Lateral Escape Before Lift)

Add a subsection here (trigger → code → evidence) when the arm must move laterally before
lifting to avoid sweeping through obstacles (opened drawers, adjacent objects, cabinet edges).

---

## Placement Approach

Add a subsection here (trigger → code → evidence) for approach sequences above the target
(hover height, descent speed, drop vs. lower) that prevent bounce, tip, or miss.

### Segmented Fixture Top Placement

**Trigger.** Place a held upright bottle on the visible top of a flat cabinet. Observe the
cabinet before the arm occludes it. Use `quantile` from `grasp.md`, the measured grasp pose
and bottle-bottom cloud quantile, and the public `Pose` constructor.

```python
frame = get_robot_state().base_frame
cabinet = localize_object("black cabinet", camera_name="agentview", target_frame=frame)
if not cabinet.ok or len(cabinet.point_cloud.points) < 500:
    raise ValueError("cabinet not localized")
surface_z = quantile((p[2] for p in cabinet.point_cloud.points), 0.90)
top_points = [p for p in cabinet.point_cloud.points
              if abs(float(p[2]) - surface_z) < 0.012]
if len(top_points) < 100:
    raise ValueError("cabinet top not found")
target_x = quantile((p[0] for p in top_points), 0.5)
target_y = quantile((p[1] for p in top_points), 0.5)
gx, gy, gz = grasp_pose.position
clearance = gz - bottle_bottom
transit_z = max(gz + 0.30, surface_z + clearance + 0.15)
for stage, position, cap in (
    ("lift", (gx, gy, transit_z), 200),
    ("transport", (target_x, target_y, transit_z), 260),
    ("lower", (target_x, target_y, surface_z + clearance + 0.012), 200),
):
    pose = Pose(position, grasp_pose.quaternion_wxyz, frame)
    if not move_to_pose(pose, tolerance=0.025, max_steps=cap).ok:
        raise ValueError(stage + " failed")
open_gripper()
```

**Why it works and evidence.** The visible top-plane points set the cabinet target; the
held bottle's measured clearance keeps its bottom above that plane during transit. An
independent verifier using this placement sequence passed `libero_goal_swap/task_2` seeds
51–55 (5/5). The original whole policy passed 15/15 development, 15/15 unseen and 50/50
held-out; no isolated placement ablation was run.

### Physics Settling After Release

After releasing a grasped object, the object needs a few control ticks to settle before the
episode's success predicate is evaluated — observation calls do not advance time.

**`set_gripper(1.0)` does NOT buy those ticks.** When the jaw is already at the requested
width the adapter returns immediately with `steps_executed = 0`, so a program relying on it to
settle gets **no** ticks at all. Measured on `libero_goal_task/task_1` and independently on
`libero_spatial_task/task_4`, which lost a whole program version to the false hypothesis. On
LIBERO, Robosuite and RoboCasa `set_gripper` now also *refuses* any value between 0.0 and 1.0
with `unsupported`, so there is no partial-width call to fall back on either.

Advance time with something that actually steps. A one-tick hold of the arm's own measured
joints is the cheapest, and it commands the gripper explicitly rather than relying on a latched
value:

```python
open_gripper()
state = get_robot_state()
for tick in range(settle_ticks):       # measure how many you need; do not assume
    step(RobotAction(arms={"primary": ArmCommand(
        "joint_position",
        state.joint_positions["primary"],
        gripper_position=1.0,
        embodiment=state.embodiment,   # required: the default is "robosuite"
    )}))
```

Check `steps_executed` on whatever you use, rather than assuming a call advanced time.

---

## Basket / Container Placement

General rule: transit at `rim_z + 0.30`, release at `rim_z + 0.10`. Never descend inside the
container — drop from above.

**NEVER call `go_home()` while holding a grasped object.** Going home during transport opens the
arm configuration and drops the object. Transport in one continuous arc: lift → translate →
descend → release.

| Object type | Transit height | Release height | Notes |
|---|---|---|---|
