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
grasps = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet")
if not grasps.ok:
    raise ValueError("grasp provider failed")
grasp = select_grasp(grasps, strategy="highest_score")
if grasp is None:
    raise ValueError("no grasp candidate")
grasp_pose = grasp.pose
open_gripper()
if not move_to_pose(grasp_pose, tolerance=0.025, max_steps=260).ok:
    raise ValueError("direct CGN grasp approach failed")
if not close_gripper().ok:
    raise ValueError("CGN grasp close failed")

cabinet_points = cabinet.point_cloud.points
surface_z = q((point[2] for point in cabinet_points), 0.92)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.015]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = q((point[0] for point in top_points), 0.5)
target_y = q((point[1] for point in top_points), 0.5)
held_clearance = grasp_pose.position[2] - bowl_bottom
lift_z = grasp_pose.position[2] + 0.18
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
result = {"task_language": context.language, "stages": ["localized", "cgn_direct_grasped", "lifted", "transported", "released"], "grasp_z": grasp_pose.position[2], "surface_z": surface_z}
