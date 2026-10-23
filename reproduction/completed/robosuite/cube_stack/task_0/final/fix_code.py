import math
def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def locate(prompt):
    found = localize_object(prompt, camera_name="agentview", target_frame=get_robot_state().base_frame)
    if not found.ok or len(found.point_cloud.points) < 20:
        raise ValueError(prompt + " not localized")
    return found

def center_top(points):
    top = quantile((p[2] for p in points), 0.9)
    span = quantile((p[2] for p in points), 0.9) - quantile((p[2] for p in points), 0.1)
    tops = [p for p in points if float(p[2]) >= top - max(0.003, span * 0.1)]
    return (quantile((p[0] for p in tops), 0.5), quantile((p[1] for p in tops), 0.5), top)

def move(position, cap=220):
    for attempt in range(3):
        motion = move_to_pose(Pose(position, downward, frame), tolerance=0.015, max_steps=cap)
        report["motions"].append(motion)
        if motion.ok:
            return
        if motion.status != "timeout":
            break
    raise ValueError("motion failed after bounded convergence retries")

state = get_robot_state()
frame = state.base_frame
if "primary" not in robosuite.get_controller_metadata()["controllable_gripper_arms"]:
    raise ValueError("requires controllable gripper")
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
report = {"language": get_task_context().language, "motions": []}
result = report
picked = locate("red cube")
target = locate("green cube")
points = picked.point_cloud.points
x, y, top = center_top(points)
tx, ty, surface = center_top(target.point_cloud.points)
width_x = quantile((p[0] for p in points), 0.9) - quantile((p[0] for p in points), 0.1)
width_y = quantile((p[1] for p in points), 0.9) - quantile((p[1] for p in points), 0.1)
width = min(width_x, width_y)
# Rotate the observed tool around base Z so its opening axis avoids the neighbor.
qw, qx, qy, qz = downward
opening_x = 1.0 - 2.0 * (qy*qy + qz*qz)
opening_y = 2.0 * (qx*qy + qw*qz)
neighbor_angle = math.atan2(ty-y, tx-x)
delta = neighbor_angle + math.pi/2.0 - math.atan2(opening_y,opening_x)
while delta > math.pi/2.0:
    delta = delta - math.pi
while delta < -math.pi/2.0:
    delta = delta + math.pi
cs = math.cos(delta/2.0)
sn = math.sin(delta/2.0)
downward = (cs*qw-sn*qz, cs*qx-sn*qy, cs*qy+sn*qx, cs*qz+sn*qw)
if width <= 0:
    raise ValueError("invalid cube width")
grasp_z = top - 0.65 * width
bottom = quantile((p[2] for p in points), 0.05)
report["geometry"] = {"pick": (x,y,grasp_z), "target": (tx,ty,surface), "width": width, "bottom": bottom}
open_gripper()
move((x,y,grasp_z + 0.15),250)
move((x,y,grasp_z),220)
close_gripper()
lift_z = max(grasp_z + 0.18, surface + grasp_z - bottom + 0.12)
move((x,y,lift_z),250)
after = locate("red cube")
report["grasp_verified"] = quantile((p[2] for p in after.point_cloud.points),0.5) - quantile((p[2] for p in points),0.5) > 0.02
if not report["grasp_verified"]:
    raise ValueError("cube not lifted")
move((tx,ty,lift_z),250)
release_z = surface + grasp_z - bottom + 0.006
move((tx,ty,release_z + 0.04),180)
move((tx,ty,release_z),180)
open_gripper()
move((tx,ty,release_z + 0.12),180)
settle_state = get_robot_state()
for tick in range(30):
    step(RobotAction(arms={"primary": ArmCommand("joint_position", settle_state.joint_positions["primary"], gripper_position=1.0)}))
result = report


