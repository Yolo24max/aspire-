def q(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def quat_mul(a, b):
    aw, ax, ay, az = (float(v) for v in a)
    bw, bx, by, bz = (float(v) for v in b)
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)

def locate(prompts, frame):
    for prompt in prompts:
        found = localize_object(prompt, camera_name="agentview", target_frame=frame)
        if found.ok and len(found.point_cloud.points) >= 20:
            return found
    return None

context = get_task_context()
state = get_robot_state()
frame = state.base_frame
bowl = locate(("grey bowl", "metal bowl", "bowl"), frame)
cabinet = locate(("black cabinet", "drawer cabinet", "cabinet"), frame)
if bowl is None or cabinet is None:
    raise ValueError("object localization failed")

points = bowl.point_cloud.points
bowl_bottom = q((point[2] for point in points), 0.05)
bowl_top = q((point[2] for point in points), 0.95)
center_x = q((point[0] for point in points), 0.5)
center_y = q((point[1] for point in points), 0.5)
current = state.end_effector_poses["primary"].position
dx = center_x - float(current[0])
dy = center_y - float(current[1])
distance = (dx * dx + dy * dy) ** 0.5
if distance < 0.02:
    raise ValueError("side approach direction unavailable")
ux = dx / distance
uy = dy / distance
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
half_turn_x = (0.7071067811865476, 0.7071067811865476, 0.0, 0.0)
side_quaternion = quat_mul(downward, half_turn_x)
grasp_z = bowl_bottom + 0.62 * (bowl_top - bowl_bottom)
pre = Pose((center_x - 0.12 * ux, center_y - 0.12 * uy, grasp_z), side_quaternion, frame)
grasp_pose = Pose((center_x, center_y, grasp_z), side_quaternion, frame)
open_gripper()
if not move_to_pose(pre, tolerance=0.025, max_steps=260).ok:
    raise ValueError("side pre-grasp failed")
if not move_to_pose(grasp_pose, tolerance=0.02, max_steps=220).ok:
    raise ValueError("side grasp approach failed")
if not close_gripper().ok:
    raise ValueError("side grasp close failed")

lift_z = grasp_z + 0.18
if not move_to_pose(Pose((center_x, center_y, lift_z), side_quaternion, frame), tolerance=0.025, max_steps=260).ok:
    raise ValueError("lift failed")
after = locate(("grey bowl", "metal bowl", "bowl"), frame)
after_z = q((point[2] for point in after.point_cloud.points), 0.5) if after is not None else bowl_bottom
if after is None or after_z - bowl_bottom <= 0.02:
    raise ValueError("post-lift grasp verification failed")

cabinet_points = cabinet.point_cloud.points
surface_z = q((point[2] for point in cabinet_points), 0.92)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.015]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = q((point[0] for point in top_points), 0.5)
target_y = q((point[1] for point in top_points), 0.5)
held_clearance = grasp_z - bowl_bottom
transit_z = max(lift_z + 0.14, surface_z + held_clearance + 0.16)
for stage, pose in (
    ("transit", Pose((center_x, center_y, transit_z), side_quaternion, frame)),
    ("carry", Pose((target_x, target_y, transit_z), side_quaternion, frame)),
    ("place", Pose((target_x, target_y, surface_z + held_clearance + 0.012), side_quaternion, frame)),
):
    if not move_to_pose(pose, tolerance=0.025, max_steps=260).ok:
        raise ValueError(stage + " failed")
if not open_gripper().ok:
    raise ValueError("release failed")
result = {"task_language": context.language, "grasp_verified": True, "stages": ["localized", "side_contact", "grasp_verified", "transported", "released"], "grasp_z": grasp_z, "surface_z": surface_z}
