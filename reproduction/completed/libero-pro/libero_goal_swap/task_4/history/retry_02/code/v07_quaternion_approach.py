import math


def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def locate(queries, frame):
    for query in queries:
        found = localize_object(query, camera_name="agentview", target_frame=frame)
        if found.ok and len(found.point_cloud.points) >= 20:
            return found
    return None


def rotate(q, vector):
    w, x, y, z = (float(value) for value in q)
    vx, vy, vz = vector
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


state = get_robot_state()
frame = state.base_frame
context = get_task_context()
bowl = locate(("grey bowl", "silver bowl", "bowl"), frame)
cabinet = locate(("top of the black drawer", "black drawer", "top of the black cabinet", "black cabinet", "drawer cabinet"), frame)
if bowl is None or cabinet is None:
    raise ValueError("could not localize bowl and cabinet")

bowl_points = bowl.point_cloud.points
cabinet_points = cabinet.point_cloud.points
bowl_bottom = quantile((point[2] for point in bowl_points), 0.05)
bowl_top = quantile((point[2] for point in bowl_points), 0.95)
surface_z = quantile((point[2] for point in cabinet_points), 0.90)
top_points = [point for point in cabinet_points if abs(float(point[2]) - surface_z) < 0.02]
if len(top_points) < 20:
    top_points = cabinet_points
target_x = quantile((point[0] for point in top_points), 0.5)
target_y = quantile((point[1] for point in top_points), 0.5)

downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
grasps = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet")
selected = None
selected_pre = None
selected_score = None
if grasps.ok:
    for candidate in grasps.grasps:
        z = float(candidate.pose.position[2])
        if z < bowl_bottom - 0.08 or z > bowl_top + 0.08:
            continue
        # Public CGN approach axis is the local +Z axis. Stand off opposite
        # that axis, so side grasps are approached from their own direction.
        axis = rotate(candidate.pose.quaternion_wxyz, (0.0, 0.0, 1.0))
        pre = Pose(
            (candidate.pose.position[0] - 0.12 * axis[0], candidate.pose.position[1] - 0.12 * axis[1], candidate.pose.position[2] - 0.12 * axis[2]),
            candidate.pose.quaternion_wxyz,
            frame,
        )
        if not plan_motion(pre).ok or not plan_motion(candidate.pose).ok:
            continue
        score = float(candidate.score)
        if selected is None or score > selected_score:
            selected = candidate.pose
            selected_pre = pre
            selected_score = score

if selected is None:
    xs = [float(point[0]) for point in bowl_points]
    ys = [float(point[1]) for point in bowl_points]
    x = quantile(xs, 0.5) + 0.30 * (max(xs) - min(xs))
    y = quantile(ys, 0.5)
    selected = Pose((x, y, bowl_top + 0.02), downward, frame)
    selected_pre = Pose((x, y, bowl_top + 0.14), downward, frame)

open_gripper()
if not move_to_pose(selected_pre, tolerance=0.025, max_steps=260).ok:
    raise ValueError("directional pre-grasp failed")
if not move_to_pose(selected, tolerance=0.025, max_steps=220).ok:
    raise ValueError("directional grasp approach failed")
if not close_gripper().ok:
    raise ValueError("close failed")

clearance = float(selected.position[2]) - bowl_bottom
transit_z = max(float(selected.position[2]) + 0.28, surface_z + clearance + 0.16)
if not move_to_pose(Pose((selected.position[0], selected.position[1], transit_z), selected.quaternion_wxyz, frame), tolerance=0.025, max_steps=240).ok:
    raise ValueError("lift failed")
if not move_to_pose(Pose((target_x, target_y, transit_z), selected.quaternion_wxyz, frame), tolerance=0.025, max_steps=300).ok:
    raise ValueError("transport failed")
if not move_to_pose(Pose((target_x, target_y, surface_z + clearance + 0.02), selected.quaternion_wxyz, frame), tolerance=0.025, max_steps=240).ok:
    raise ValueError("lower failed")
if not open_gripper().ok:
    raise ValueError("release failed")

result = {"task_language": context.language, "bowl_points": len(bowl_points), "cabinet_points": len(cabinet_points), "top_points": len(top_points), "directional_cgn": selected_pre is not None, "released": True}
