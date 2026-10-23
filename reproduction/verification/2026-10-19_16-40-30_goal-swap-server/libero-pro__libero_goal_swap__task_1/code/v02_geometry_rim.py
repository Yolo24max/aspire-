def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def move_retry(pose, tolerance, tries, label):
    attempts = []
    for attempt in range(tries):
        motion = move_to_pose(pose, tolerance=tolerance, max_steps=250)
        actual = get_robot_state().end_effector_poses["primary"].position
        short = [float(pose.position[axis] - actual[axis]) for axis in range(3)]
        attempts.append({"ok": motion.ok, "status": motion.status, "steps": motion.steps_executed,
                         "commanded_z": float(pose.position[2]), "achieved_z": float(actual[2]),
                         "short_xyz": short})
        if motion.ok:
            report[label] = attempts
            return True
    report[label] = attempts
    return False

base_frame = get_robot_state().base_frame
report = {"task": get_task_context().language, "grasp_backend": "observed_geometry_rim"}

picked = localize_object("grey bowl", camera_name="agentview", target_frame=base_frame)
if not picked.ok or len(picked.point_cloud.points) < 20:
    raise ValueError("bowl localization failed")

stove = localize_object("stove burner", camera_name="agentview", target_frame=base_frame)
if not stove.ok or len(stove.point_cloud.points) < 20:
    stove = localize_object("stove", camera_name="agentview", target_frame=base_frame)
if not stove.ok or len(stove.point_cloud.points) < 20:
    raise ValueError("stove localization failed")

all_z = [float(point[2]) for point in picked.point_cloud.points]
low_z = quantile(all_z, 0.05)
bowl_points = [point for point in picked.point_cloud.points if float(point[2]) < low_z + 0.08]
if len(bowl_points) < 20:
    raise ValueError("bowl geometry too sparse")

bowl_x = quantile((point[0] for point in bowl_points), 0.5)
bowl_y = quantile((point[1] for point in bowl_points), 0.5)
rim_y = quantile((point[1] for point in bowl_points), 0.1) + 0.009
rim_z = quantile((point[2] for point in bowl_points), 0.95)
bowl_bottom_z = quantile((point[2] for point in bowl_points), 0.05)
stove_x = quantile((point[0] for point in stove.point_cloud.points), 0.5)
stove_y = quantile((point[1] for point in stove.point_cloud.points), 0.5)
stove_z = quantile((point[2] for point in stove.point_cloud.points), 0.9)
report["geometry"] = {"bowl_xy": [bowl_x, bowl_y], "rim_y": rim_y,
                      "rim_z": rim_z, "bowl_bottom_z": bowl_bottom_z,
                      "stove_xyz": [stove_x, stove_y, stove_z]}

downward = get_robot_state().end_effector_poses["primary"].quaternion_wxyz
grasp_z = rim_z + 0.035
grasp_pose = Pose((bowl_x, rim_y, grasp_z), downward, base_frame)
pre_grasp = Pose((bowl_x, rim_y, grasp_z + 0.13), downward, base_frame)
open_gripper()
if not move_retry(pre_grasp, 0.02, 3, "pre_grasp"):
    raise ValueError("pre-grasp approach failed")
if not move_retry(grasp_pose, 0.018, 2, "grasp_approach"):
    raise ValueError("rim grasp approach failed")
close_gripper()
report["jaw_close"] = float(get_robot_state().gripper_positions["primary"])

lift_z = grasp_z + 0.17
lift_pose = Pose((bowl_x, rim_y, lift_z), downward, base_frame)
if not move_retry(lift_pose, 0.025, 2, "lift"):
    raise ValueError("lift failed")
report["jaw_after_lift"] = float(get_robot_state().gripper_positions["primary"])

after = localize_object("grey bowl", camera_name="agentview", target_frame=base_frame)
grasp_verified = (
    after.ok and len(after.point_cloud.points) >= 20
    and quantile((point[2] for point in after.point_cloud.points), 0.5)
        - quantile((point[2] for point in bowl_points), 0.5) > 0.035
)
report["grasp_verified"] = grasp_verified
if not grasp_verified:
    raise ValueError("object did not visibly lift")

transit_z = max(lift_z, stove_z + 0.30)
if transit_z > lift_z + 0.01:
    raised = Pose((bowl_x, rim_y, transit_z), downward, base_frame)
    if not move_retry(raised, 0.03, 2, "raise_for_transit"):
        raise ValueError("transit raise failed")
above_stove = Pose((stove_x, stove_y, transit_z), downward, base_frame)
if not move_retry(above_stove, 0.03, 2, "transit"):
    raise ValueError("transit failed")

release_z = stove_z + (grasp_z - bowl_bottom_z) + 0.025
release_pose = Pose((stove_x, stove_y, release_z), downward, base_frame)
if not move_retry(release_pose, 0.025, 2, "release_approach"):
    raise ValueError("release approach failed")
report["jaw_before_place"] = float(get_robot_state().gripper_positions["primary"])
open_gripper()
retreat = Pose((stove_x, stove_y, release_z + 0.10), downward, base_frame)
move_retry(retreat, 0.03, 2, "retreat")

landed = localize_object("grey bowl", camera_name="agentview", target_frame=base_frame)
if landed.ok and len(landed.point_cloud.points) >= 20:
    report["landed_bowl_xyz"] = [quantile((point[axis] for point in landed.point_cloud.points), 0.5)
                                 for axis in range(3)]
result = report
