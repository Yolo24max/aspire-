def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def run():
    context = get_task_context()
    state = get_robot_state()
    frame = state.base_frame
    observation = get_observation()
    camera = "agentview"
    if camera not in observation.cameras:
        raise ValueError("agentview camera unavailable")
    picked = None
    for prompt in ("red cube", "red block", "cube"):
        candidate = localize_object(prompt, camera_name=camera, target_frame=frame)
        if candidate.ok and len(candidate.point_cloud.points) >= 20:
            picked = candidate
            break
    if picked is None:
        raise ValueError("cube not localized")
    points = picked.point_cloud.points
    x = quantile((p[0] for p in points), 0.5)
    y = quantile((p[1] for p in points), 0.5)
    top = quantile((p[2] for p in points), 0.9)
    width_x = quantile((p[0] for p in points), 0.9) - quantile((p[0] for p in points), 0.1)
    width_y = quantile((p[1] for p in points), 0.9) - quantile((p[1] for p in points), 0.1)
    observed_width = min(width_x, width_y)
    if observed_width <= 0.0:
        raise ValueError("cube cloud has no horizontal span")
    grasp_z = top - 0.4 * observed_width
    downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
    report = {"task": context.language, "camera": camera, "initial_top": top,
              "observed_width": observed_width, "grasp_position": [x, y, grasp_z]}
    opened = open_gripper()
    if opened.terminated or opened.truncated:
        report["phase"] = "open_terminal"
        return report
    if not opened.ok:
        raise ValueError("open failed")
    for phase, z, cap in (("pregrasp", grasp_z + 0.15, 250),
                          ("contact", grasp_z, 220)):
        moved = move_to_pose(Pose((x, y, z), downward, frame), tolerance=0.015, max_steps=cap)
        if moved.terminated or moved.truncated:
            report["phase"] = phase + "_terminal"
            report["motion_status"] = moved.status
            return report
        if not moved.ok:
            raise ValueError(phase + " failed: " + str(moved.status))
    closed = close_gripper()
    if closed.terminated or closed.truncated:
        report["phase"] = "close_terminal"
        return report
    if not closed.ok:
        raise ValueError("close failed")
    lifted = move_to_pose(Pose((x, y, grasp_z + 0.18), downward, frame), tolerance=0.015, max_steps=250)
    report["phase"] = "lift"
    report["motion_status"] = lifted.status
    report["terminal"] = lifted.terminated
    if lifted.terminated or lifted.truncated:
        return report
    if not lifted.ok:
        raise ValueError("lift failed: " + str(lifted.status))
    after = localize_object("red cube", camera_name=camera, target_frame=frame)
    report["grasp_verified"] = bool(after.ok and len(after.point_cloud.points) >= 20 and
        quantile((p[2] for p in after.point_cloud.points), 0.9) - top > 0.03)
    return report


result = run()
