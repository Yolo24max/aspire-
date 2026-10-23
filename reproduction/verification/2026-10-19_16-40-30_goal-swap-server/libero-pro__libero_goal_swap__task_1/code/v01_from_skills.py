def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def cloud_quantiles(points, x_fraction=0.5, y_fraction=0.5, z_fraction=0.5):
    return (
        quantile((point[0] for point in points), x_fraction),
        quantile((point[1] for point in points), y_fraction),
        quantile((point[2] for point in points), z_fraction),
    )

base_frame = get_robot_state().base_frame
report = {"task": get_task_context().language}

# --- Localize pick object ---
picked = localize_object("grey bowl", camera_name="agentview", target_frame=base_frame)
if not picked.ok or len(picked.point_cloud.points) < 20:
    raise ValueError("localization failed for pick object")
object_center = cloud_quantiles(picked.point_cloud.points)

# --- Grasp via grasp backend (a contact hypothesis for an open bowl) ---
grasps = generate_grasps("agentview", picked.segmentation, backend="contact-graspnet")
grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
if grasp is not None:
    grasp_pose = grasp.pose
else:
    # --- OR: top-down grasp from observed geometry ---
    downward = get_robot_state().end_effector_poses["primary"].quaternion_wxyz
    grasp_pose = Pose(
        (object_center[0], object_center[1], object_center[2] + 0.01),
        downward,
        base_frame,
    )

# --- Staged approach: pre-grasp above, descend, close ---
open_gripper()
pre_grasp = Pose(
    (grasp_pose.position[0], grasp_pose.position[1], grasp_pose.position[2] + 0.12),
    grasp_pose.quaternion_wxyz,
    grasp_pose.frame,
)
if not move_to_pose(pre_grasp, tolerance=0.02, max_steps=250).ok:
    raise ValueError("pre-grasp approach failed")
if not move_to_pose(grasp_pose, tolerance=0.015, max_steps=250).ok:
    raise ValueError("grasp approach failed")
close_gripper()

# --- Lift, then VERIFY the object actually moved with the gripper ---
before_z = quantile((point[2] for point in picked.point_cloud.points), 0.5)
lift = Pose(
    (grasp_pose.position[0], grasp_pose.position[1], grasp_pose.position[2] + 0.15),
    grasp_pose.quaternion_wxyz,
    grasp_pose.frame,
)
move_to_pose(lift, tolerance=0.02, max_steps=250)

after = localize_object("grey bowl", camera_name="agentview", target_frame=base_frame)
grasp_verified = (
    after.ok
    and len(after.point_cloud.points) >= 20
    and quantile((point[2] for point in after.point_cloud.points), 0.5) - before_z > 0.02
)
report["grasp_verified"] = grasp_verified

# --- Re-observe for placement target ---
target = localize_object("stove", camera_name="agentview", target_frame=base_frame)
if not target.ok:
    raise ValueError("localization failed for placement target")
target_center = cloud_quantiles(target.point_cloud.points)
surface_z = quantile((point[2] for point in target.point_cloud.points), 0.9)

# --- Transport ---
above_target = Pose(
    (target_center[0], target_center[1], lift.position[2]),
    grasp_pose.quaternion_wxyz,
    base_frame,
)
move_to_pose(above_target, tolerance=0.02, max_steps=300)

# --- Place ---
release = Pose(
    (target_center[0], target_center[1], surface_z + 0.03),
    grasp_pose.quaternion_wxyz,
    base_frame,
)
move_to_pose(release, tolerance=0.02, max_steps=250)
open_gripper()

result = report
