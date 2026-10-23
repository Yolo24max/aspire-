def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def locate(queries, frame):
    for query in queries:
        found = localize_object(query, camera_name="agentview", target_frame=frame)
        if found.ok and len(found.point_cloud.points) >= 20:
            return found
    return None


state = get_robot_state()
frame = state.base_frame
context = get_task_context()
bowl = locate(("grey bowl", "silver bowl", "bowl"), frame)
cabinet = locate(("black cabinet", "drawer cabinet", "cabinet"), frame)
if bowl is None or cabinet is None:
    raise ValueError("could not localize bowl and cabinet")

bowl_points = bowl.point_cloud.points
cabinet_points = cabinet.point_cloud.points
bowl_x = quantile((point[0] for point in bowl_points), 0.5)
bowl_y = quantile((point[1] for point in bowl_points), 0.5)
bowl_bottom = quantile((point[2] for point in bowl_points), 0.05)
bowl_top = quantile((point[2] for point in bowl_points), 0.95)

surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.02]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)

grasps = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet")
grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
if grasp is None and grasps.ok:
    # The backend returned candidates but its top_down selector rejected both.
    # Keep only reachable candidates near the observed bowl height, then score them.
    selected = None
    selected_score = None
    for candidate in grasps.grasps:
        candidate_z = float(candidate.pose.position[2])
        if candidate_z < bowl_bottom - 0.08 or candidate_z > bowl_top + 0.08:
            continue
        candidate_score = float(candidate.score)
        if selected is None or candidate_score > selected_score:
            selected = candidate
            selected_score = candidate_score
    if selected is not None:
        grasp = selected
if grasp is not None:
    grasp_pose = grasp.pose
else:
    downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
    grasp_pose = Pose((bowl_x, bowl_y, bowl_top + 0.005), downward, frame)

open_gripper()
pre_grasp = Pose(
    (grasp_pose.position[0], grasp_pose.position[1], grasp_pose.position[2] + 0.12),
    grasp_pose.quaternion_wxyz,
    frame,
)
if not move_to_pose(pre_grasp, tolerance=0.025, max_steps=200).ok:
    raise ValueError("pre-grasp failed")
if not move_to_pose(grasp_pose, tolerance=0.02, max_steps=180).ok:
    raise ValueError("grasp approach failed")
if not close_gripper().ok:
    raise ValueError("close failed")

clearance = grasp_pose.position[2] - bowl_bottom
transit_z = max(grasp_pose.position[2] + 0.18, surface_z + clearance + 0.14)
lift = Pose((grasp_pose.position[0], grasp_pose.position[1], transit_z), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(lift, tolerance=0.025, max_steps=220).ok:
    raise ValueError("lift failed")
above_target = Pose((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(above_target, tolerance=0.025, max_steps=280).ok:
    raise ValueError("transport failed")
release = Pose((target_x, target_y, surface_z + clearance + 0.015), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(release, tolerance=0.025, max_steps=220).ok:
    raise ValueError("lower failed")
if not open_gripper().ok:
    raise ValueError("release failed")

result = {
    "task_language": context.language,
    "bowl_points": len(bowl_points),
    "cabinet_points": len(cabinet_points),
    "top_points": len(top_points),
    "selected_backend_grasp": grasp is not None,
    "released": True,
}
