def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("empty point cloud")
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


def locate(queries, camera_name, frame):
    for query in queries:
        candidate = localize_object(query, camera_name=camera_name, target_frame=frame)
        if candidate.ok and len(candidate.point_cloud.points) >= 20:
            return candidate
    return None


context = get_task_context()
state = get_robot_state()
frame = state.base_frame
camera = "agentview"
report = {"task_language": context.language, "stages": [], "grasp_verified": False}

# Observe both objects while the arm is still out of the camera's way.
bowl = locate(("grey bowl", "metal bowl", "bowl"), camera, frame)
cabinet = locate(("black cabinet", "drawer cabinet", "cabinet"), camera, frame)
if bowl is None or cabinet is None:
    raise ValueError("pick or support object not localized")

bowl_points = bowl.point_cloud.points
bowl_x = quantile((point[0] for point in bowl_points), 0.5)
bowl_y = quantile((point[1] for point in bowl_points), 0.5)
bowl_bottom = quantile((point[2] for point in bowl_points), 0.05)
bowl_top = quantile((point[2] for point in bowl_points), 0.95)

# Prefer the configured grasp provider; retain a geometry-derived top-down fallback.
grasps = generate_grasps(camera, bowl.segmentation, backend="contact-graspnet")
grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
if grasp is not None:
    grasp_pose = grasp.pose
else:
    downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
    grasp_z = bowl_bottom + 0.72 * (bowl_top - bowl_bottom)
    grasp_pose = Pose((bowl_x, bowl_y, grasp_z), downward, frame)

open_gripper()
pre_grasp = Pose(
    (grasp_pose.position[0], grasp_pose.position[1], grasp_pose.position[2] + 0.12),
    grasp_pose.quaternion_wxyz,
    frame,
)
if not move_to_pose(pre_grasp, tolerance=0.025, max_steps=220).ok:
    raise ValueError("pre-grasp failed")
if not move_to_pose(grasp_pose, tolerance=0.02, max_steps=220).ok:
    raise ValueError("grasp approach failed")
if not close_gripper().ok:
    raise ValueError("gripper close failed")

lift_z = max(grasp_pose.position[2] + 0.16, bowl_top + 0.10)
lift_pose = Pose(
    (grasp_pose.position[0], grasp_pose.position[1], lift_z),
    grasp_pose.quaternion_wxyz,
    frame,
)
if not move_to_pose(lift_pose, tolerance=0.025, max_steps=220).ok:
    raise ValueError("lift failed")

# The arm remains closed while the bowl is carried. Derive the support plane and
# the bowl's held clearance from the two public clouds captured before grasping.
cabinet_points = cabinet.point_cloud.points
surface_z = quantile((point[2] for point in cabinet_points), 0.92)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.015]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)
held_clearance = grasp_pose.position[2] - bowl_bottom
transit_z = max(lift_z + 0.14, surface_z + held_clearance + 0.16)

transit_pose = Pose((grasp_pose.position[0], grasp_pose.position[1], transit_z), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(transit_pose, tolerance=0.025, max_steps=220).ok:
    raise ValueError("transit lift failed")
above_target = Pose((target_x, target_y, transit_z), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(above_target, tolerance=0.025, max_steps=260).ok:
    raise ValueError("transport failed")

release_z = surface_z + held_clearance + 0.012
release_pose = Pose((target_x, target_y, release_z), grasp_pose.quaternion_wxyz, frame)
if not move_to_pose(release_pose, tolerance=0.025, max_steps=220).ok:
    raise ValueError("placement descent failed")
if not open_gripper().ok:
    raise ValueError("release failed")

report["stages"] = ["localized", "grasped", "lifted", "transported", "released"]
report["held_clearance"] = held_clearance
report["surface_z_observed"] = surface_z
result = report
