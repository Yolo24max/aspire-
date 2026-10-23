def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

state = get_robot_state()
picked = localize_object("red cube", camera_name="agentview", target_frame=state.base_frame)
if not picked.ok or len(picked.point_cloud.points) < 20:
    raise ValueError("red cube localization failed")
points = picked.point_cloud.points
x = quantile((p[0] for p in points), 0.5)
y = quantile((p[1] for p in points), 0.5)
top = quantile((p[2] for p in points), 0.9)
width_x = quantile((p[0] for p in points), 0.9) - quantile((p[0] for p in points), 0.1)
width_y = quantile((p[1] for p in points), 0.9) - quantile((p[1] for p in points), 0.1)
observed_width = min(width_x, width_y)
if observed_width <= 0.0:
    raise ValueError("cube cloud has no horizontal span")
grasp_z = top - 0.65 * observed_width
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
before_z = quantile((p[2] for p in points), 0.5)
if not open_gripper().ok:
    raise ValueError("open failed")
if not move_to_pose(Pose((x, y, grasp_z + 0.15), downward, state.base_frame), tolerance=0.015, max_steps=250).ok:
    raise ValueError("approach failed")
if not move_to_pose(Pose((x, y, grasp_z), downward, state.base_frame), tolerance=0.015, max_steps=220).ok:
    raise ValueError("descent failed")
if not close_gripper().ok:
    raise ValueError("close failed")
lift = move_to_pose(Pose((x, y, grasp_z + 0.18), downward, state.base_frame), tolerance=0.015, max_steps=250)
after = localize_object("red cube", camera_name="agentview", target_frame=state.base_frame)
grasp_verified = after.ok and len(after.point_cloud.points) >= 20 and quantile((p[2] for p in after.point_cloud.points), 0.5) - before_z > 0.02
result = {"task": get_task_context().language, "lift_ok": lift.ok, "grasp_verified": grasp_verified, "observed_width": observed_width, "grasp_z": grasp_z}
