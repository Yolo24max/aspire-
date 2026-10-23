def q(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

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
bowl_x = q((point[0] for point in points), 0.5)
bowl_y = q((point[1] for point in points), 0.5)
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
grasp_z = bowl_top + 0.005
grasp_pose = Pose((bowl_x, bowl_y, grasp_z), downward, frame)
open_gripper()
pre = Pose((bowl_x, bowl_y, grasp_z + 0.12), downward, frame)
if not move_to_pose(pre, tolerance=0.025, max_steps=220).ok:
    raise ValueError("pre-grasp failed")
approach = move_to_pose(grasp_pose, tolerance=0.02, max_steps=240)
closed = close_gripper()
if not closed.ok:
    raise ValueError("grasp close failed")

cabinet_points = cabinet.point_cloud.points
surface_z = q((point[2] for point in cabinet_points), 0.92)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.015]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = q((point[0] for point in top_points), 0.5)
target_y = q((point[1] for point in top_points), 0.5)
held_clearance = grasp_z - bowl_bottom
lift_z = grasp_z + 0.18
transit_z = max(lift_z + 0.14, surface_z + held_clearance + 0.16)
for stage, pose in (
    ("lift", Pose((bowl_x, bowl_y, lift_z), downward, frame)),
    ("transit", Pose((bowl_x, bowl_y, transit_z), downward, frame)),
    ("carry", Pose((target_x, target_y, transit_z), downward, frame)),
    ("place", Pose((target_x, target_y, surface_z + held_clearance + 0.012), downward, frame)),
):
    if not move_to_pose(pose, tolerance=0.025, max_steps=260).ok:
        raise ValueError(stage + " failed")
if not open_gripper().ok:
    raise ValueError("release failed")
result = {"task_language": context.language, "approach_ok": approach.ok, "stages": ["localized", "rim_contact", "grasped", "lifted", "transported", "released"], "grasp_z": grasp_z, "surface_z": surface_z}
