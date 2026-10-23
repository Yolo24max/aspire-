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
cabinet = locate(("top of the black drawer", "black drawer", "top of the black cabinet", "black cabinet", "drawer cabinet"), frame)
if bowl is None or cabinet is None:
    raise ValueError("could not localize bowl and cabinet")

bowl_points = bowl.point_cloud.points
cabinet_points = cabinet.point_cloud.points
bowl_x = quantile((point[0] for point in bowl_points), 0.5)
bowl_y = quantile((point[1] for point in bowl_points), 0.5)
bowl_bottom = quantile((point[2] for point in bowl_points), 0.05)
bowl_top = quantile((point[2] for point in bowl_points), 0.95)
low_x = quantile((point[0] for point in bowl_points), 0.10)
high_x = quantile((point[0] for point in bowl_points), 0.90)
low_y = quantile((point[1] for point in bowl_points), 0.10)
high_y = quantile((point[1] for point in bowl_points), 0.90)
if high_x - low_x >= high_y - low_y:
    grasp_x = bowl_x + 0.30 * (high_x - low_x)
    grasp_y = bowl_y
else:
    grasp_x = bowl_x
    grasp_y = bowl_y + 0.30 * (high_y - low_y)

surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.02]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)

downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
grasp_z = bowl_top + 0.02
grasp_pose = Pose((grasp_x, grasp_y, grasp_z), downward, frame)
pre_grasp = Pose((grasp_x, grasp_y, grasp_z + 0.12), downward, frame)

open_gripper()
if not move_to_pose(pre_grasp, tolerance=0.025, max_steps=240).ok:
    raise ValueError("pre-grasp failed")
if not move_to_pose(grasp_pose, tolerance=0.025, max_steps=200).ok:
    raise ValueError("grasp approach failed")
if not close_gripper().ok:
    raise ValueError("close failed")
contact_pose = Pose((grasp_x, grasp_y, bowl_top - 0.01), downward, frame)
if not move_to_pose(contact_pose, tolerance=0.025, max_steps=160).ok:
    raise ValueError("contact settle failed")

clearance = grasp_z - bowl_bottom
transit_z = max(grasp_z + 0.28, surface_z + clearance + 0.16)
if not move_to_pose(Pose((grasp_x, grasp_y, transit_z), downward, frame), tolerance=0.025, max_steps=240).ok:
    raise ValueError("lift failed")
if not move_to_pose(Pose((target_x, target_y, transit_z), downward, frame), tolerance=0.025, max_steps=300).ok:
    raise ValueError("transport failed")
if not move_to_pose(Pose((target_x, target_y, surface_z + clearance + 0.02), downward, frame), tolerance=0.025, max_steps=240).ok:
    raise ValueError("lower failed")
if not open_gripper().ok:
    raise ValueError("release failed")

result = {"task_language": context.language, "bowl_points": len(bowl_points), "cabinet_points": len(cabinet_points), "top_points": len(top_points), "edge_grasp": True, "released": True}
