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

bowl_points = bowl.point_cloud.points
bowl_bottom = q((point[2] for point in bowl_points), 0.05)
bowl_top = q((point[2] for point in bowl_points), 0.95)
bowl_x = q((point[0] for point in bowl_points), 0.5)
bowl_y = q((point[1] for point in bowl_points), 0.5)
grasps = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet")
grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
if grasp is not None:
    grasp_pose = grasp.pose
else:
    downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
    grasp_pose = Pose((bowl_x, bowl_y, bowl_top + 0.02), downward, frame)

open_gripper()
pre = Pose((grasp_pose.position[0], grasp_pose.position[1], grasp_pose.position[2] + 0.12), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(pre, tolerance=0.025, max_steps=220).ok:
    raise ValueError("pre-grasp failed")
if not move_to_pose(grasp_pose, tolerance=0.02, max_steps=220).ok:
    raise ValueError("grasp approach failed")
if not close_gripper().ok:
    raise ValueError("grasp close failed")

cabinet_points = cabinet.point_cloud.points
surface_z = q((point[2] for point in cabinet_points), 0.92)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.015]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = q((point[0] for point in top_points), 0.5)
target_y = q((point[1] for point in top_points), 0.5)
held_clearance = grasp_pose.position[2] - bowl_bottom
lift_z = max(grasp_pose.position[2] + 0.16, bowl_top + 0.10)
transit_z = max(lift_z + 0.14, surface_z + held_clearance + 0.16)
for stage, pose in (
    ("lift", Pose((grasp_pose.position[0], grasp_pose.position[1], lift_z), grasp_pose.quaternion_wxyz, frame)),
    ("transit", Pose((grasp_pose.position[0], grasp_pose.position[1], transit_z), grasp_pose.quaternion_wxyz, frame)),
    ("carry", Pose((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame)),
    ("place", Pose((target_x, target_y, surface_z + held_clearance + 0.012), grasp_pose.quaternion_wxyz, frame)),
):
    if not move_to_pose(pose, tolerance=0.025, max_steps=260).ok:
        raise ValueError(stage + " failed")
if not open_gripper().ok:
    raise ValueError("release failed")
result = {"task_language": context.language, "stages": ["localized", "grasped", "lifted", "transported", "released"], "grasp_z": grasp_pose.position[2], "surface_z": surface_z}
