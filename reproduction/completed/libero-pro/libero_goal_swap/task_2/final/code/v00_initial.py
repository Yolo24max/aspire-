def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def axis_z(quaternion):
    w, x, y, z = (float(value) for value in quaternion)
    return (2.0 * (x * z + w * y), 2.0 * (y * z - w * x), 1.0 - 2.0 * (x * x + y * y))

def pose_at(position, quaternion, frame):
    return Pose(tuple(position), tuple(quaternion), frame)

def move_checked(stage, target, max_steps):
    response = move_to_pose(target, tolerance=0.025, max_steps=max_steps)
    report["motions"].append({"stage": stage, "ok": bool(response.ok), "status": str(response.status), "steps": int(response.steps_executed), "target": list(target.position)})
    if not response.ok:
        raise ValueError(stage + " failed: " + str(response.status))

context = get_task_context()
state = get_robot_state()
frame = state.base_frame
report = {"language": context.language, "motions": [], "grasp_candidates": []}
result = report

if "wine bottle" not in context.language.lower() or "drawer" not in context.language.lower():
    raise ValueError("unexpected task language")

bottle = localize_object("wine bottle", camera_name="agentview", target_frame=frame)
if not bottle.ok or len(bottle.point_cloud.points) < 100:
    raise ValueError("wine bottle not localized")
cabinet = localize_object("black cabinet", camera_name="agentview", target_frame=frame)
if not cabinet.ok or len(cabinet.point_cloud.points) < 500:
    raise ValueError("drawer cabinet not localized")

bottle_points = bottle.point_cloud.points
cabinet_points = cabinet.point_cloud.points
bottle_x = quantile((point[0] for point in bottle_points), 0.5)
bottle_y = quantile((point[1] for point in bottle_points), 0.5)
bottle_bottom = quantile((point[2] for point in bottle_points), 0.05)
bottle_top = quantile((point[2] for point in bottle_points), 0.95)
surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.012]
if len(top_points) < 100:
    raise ValueError("cabinet top plane not found")
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)
report["observed"] = {"bottle_center": [bottle_x, bottle_y], "bottle_z": [bottle_bottom, bottle_top], "target": [target_x, target_y, surface_z], "top_points": len(top_points)}

generated = generate_grasps("agentview", bottle.segmentation, backend="contact-graspnet", max_candidates=10)
if not generated.ok:
    raise ValueError("grasp generation failed")

best = None
best_pre = None
best_rank = None
grasp_mid_z = bottle_bottom + 0.50 * (bottle_top - bottle_bottom)
for candidate in generated.grasps:
    grasp_pose = candidate.pose
    gx, gy, gz = (float(value) for value in grasp_pose.position)
    direction = axis_z(grasp_pose.quaternion_wxyz)
    report["grasp_candidates"].append({"position": [gx, gy, gz], "score": float(candidate.score), "axis_z": list(direction)})
    if abs(gx - bottle_x) > 0.065 or abs(gy - bottle_y) > 0.065:
        continue
    if gz < bottle_bottom + 0.025 or gz > bottle_top - 0.020:
        continue
    if abs(direction[2]) > 0.70:
        continue
    pre_position = (gx - 0.11 * direction[0], gy - 0.11 * direction[1], gz - 0.11 * direction[2])
    pre_pose = pose_at(pre_position, grasp_pose.quaternion_wxyz, frame)
    rank = float(candidate.score) - 2.0 * abs(gz - grasp_mid_z)
    if best_rank is None or rank > best_rank:
        best = candidate
        best_pre = pre_pose
        best_rank = rank
if best is None:
    raise ValueError("no side grasp candidate near bottle body")

grasp_pose = best.pose
gx, gy, gz = (float(value) for value in grasp_pose.position)
report["chosen_grasp"] = {"position": [gx, gy, gz], "quaternion": list(grasp_pose.quaternion_wxyz), "pre_position": list(best_pre.position)}
open_gripper()
move_checked("pre_grasp", best_pre, 250)
move_checked("grasp", grasp_pose, 180)
closed = close_gripper()
report["close"] = {"ok": bool(closed.ok), "status": str(closed.status), "steps": int(closed.steps_executed)}
if not closed.ok:
    raise ValueError("close failed")

grasp_clearance = gz - bottle_bottom
transit_z = max(gz + 0.30, surface_z + grasp_clearance + 0.15)
lift_pose = pose_at((gx, gy, transit_z), grasp_pose.quaternion_wxyz, frame)
move_checked("lift", lift_pose, 200)
above_target = pose_at((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame)
move_checked("transport", above_target, 260)
release_z = surface_z + grasp_clearance + 0.012
release_pose = pose_at((target_x, target_y, release_z), grasp_pose.quaternion_wxyz, frame)
move_checked("lower", release_pose, 200)
released = open_gripper()
report["release"] = {"ok": bool(released.ok), "status": str(released.status), "steps": int(released.steps_executed)}
if not released.ok:
    raise ValueError("release failed")

settle_state = get_robot_state()
for tick in range(8):
    step(RobotAction({"primary": ArmCommand("joint_position", settle_state.joint_positions["primary"], gripper_position=1.0, embodiment=settle_state.embodiment)}))
report["complete"] = True
result = report
