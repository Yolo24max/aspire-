def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def move_checked(stage, pose, cap):
    answer = move_to_pose(pose, tolerance=0.025, max_steps=cap)
    if not answer.ok:
        raise ValueError(stage + " failed")
    return answer.steps_executed


task_language = get_task_context().language
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

grasp_state = get_robot_state()
grasp_pose = grasp_state.end_effector_poses["primary"]
gx = float(grasp_pose.position[0])
gy = float(grasp_pose.position[1])
gz = float(grasp_pose.position[2])
bottle_bottom = low

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
lift_steps = move_checked("lift", Pose((gx, gy, transit_z), grasp_pose.quaternion_wxyz, frame), 200)
transport_steps = move_checked("transport", Pose((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame), 260)
release_z = surface_z + grasp_clearance + 0.012
lower_steps = move_checked("lower", Pose((target_x, target_y, release_z), grasp_pose.quaternion_wxyz, frame), 200)
open_answer = open_gripper()

result = {
    "task_language": task_language,
    "bottle_points": len(points),
    "cabinet_points": len(cabinet_points),
    "top_points": len(top_points),
    "bottle_bottom": bottle_bottom,
    "bottle_top": high,
    "grasp_target": (x, y, z),
    "grasp_measured": (gx, gy, gz),
    "surface_z": surface_z,
    "target_xy": (target_x, target_y),
    "transit_z": transit_z,
    "release_z": release_z,
    "stage_steps": (lift_steps, transport_steps, lower_steps),
    "release_ok": open_answer.ok,
    "release_steps": open_answer.steps_executed,
}
