def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def center(points):
    return (quantile((p[0] for p in points), 0.5),
            quantile((p[1] for p in points), 0.5),
            quantile((p[2] for p in points), 0.5))


def locate(prompts, frame, min_points=20):
    for prompt in prompts:
        item = localize_object(prompt, camera_name="agentview", target_frame=frame)
        if item.ok and len(item.point_cloud.points) >= min_points:
            return item, prompt
    return None, None


def move(name, position, orientation, frame, cap=180):
    motion = move_to_pose(Pose(position, orientation, frame),
                          tolerance=0.025, max_steps=cap)
    if name == "outside_high" and not motion.ok:
        actual = get_robot_state().end_effector_poses["primary"].position
        residual = ((float(actual[0]) - position[0]) ** 2 +
                    (float(actual[1]) - position[1]) ** 2 +
                    (float(actual[2]) - position[2]) ** 2) ** 0.5
        if residual < 0.02:
            result["motions"].append((name + "_first", False, str(motion.status),
                                      int(motion.steps_executed)))
            motion = move_to_pose(Pose(position, orientation, frame),
                                  tolerance=0.025, max_steps=cap)
    near_contact = False
    if name == "handle_contact" and not motion.ok:
        actual = get_robot_state().end_effector_poses["primary"].position
        residual = ((float(actual[0]) - position[0]) ** 2 +
                    (float(actual[1]) - position[1]) ** 2 +
                    (float(actual[2]) - position[2]) ** 2) ** 0.5
        result["handle_residual_m"] = residual
        near_contact = residual < 0.04 and int(motion.steps_executed) > 0
    result["motions"].append((name, bool(motion.ok), str(motion.status),
                              int(motion.steps_executed)))
    return bool(motion.ok) or near_contact


state = get_robot_state()
frame = state.base_frame
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
# A partial side turn keeps the arm clear while moving the fingertips behind the rail.
cos_half = 0.9238795325112867
sin_half = -0.3826834323650898
handle_orientation = (cos_half * downward[0] - sin_half * downward[1],
                      cos_half * downward[1] + sin_half * downward[0],
                      cos_half * downward[2] - sin_half * downward[3],
                      cos_half * downward[3] + sin_half * downward[2])
result = {"task": get_task_context().language, "motions": [], "stage": "localize"}
cabinet, cabinet_prompt = locate(("black drawer cabinet", "black cabinet", "drawer cabinet"), frame, 100)
bowl, bowl_prompt = locate(("gray bowl", "silver bowl", "bowl"), frame, 30)
result["cabinet_prompt"] = cabinet_prompt
result["bowl_prompt"] = bowl_prompt
active = cabinet is not None and bowl is not None
if active:
    cc = center(cabinet.point_cloud.points)
    bc = center(bowl.point_cloud.points)
    result["cabinet_center"] = cc
    result["bowl_center"] = bc
    selected_center = None
    selected_segmentation = None
    selected_points = None
    result["handle_candidates"] = []
    for prompt in ("drawer handle", "silver drawer handle", "handle"):
        found = segment_text("agentview", prompt)
        if not found.ok:
            continue
        for candidate in found.segmentations[:10]:
            cloud = mask_to_point_cloud(candidate, "agentview", target_frame=frame)
            if len(cloud.points) < 20:
                continue
            hc = center(cloud.points)
            distance = ((hc[0] - cc[0]) ** 2 + (hc[1] - cc[1]) ** 2) ** 0.5
            result["handle_candidates"].append((prompt, hc, len(cloud.points), distance))
            if distance <= 0.35 and cc[2] - 0.08 <= hc[2] <= cc[2] + 0.30:
                if selected_center is None or hc[2] > selected_center[2]:
                    selected_center = hc
                    selected_segmentation = candidate
                    selected_points = cloud.points
                    result["handle_prompt"] = prompt
        if selected_center is not None:
            break
    if selected_center is None:
        active = False
        result["stage"] = "handle_missing"
if active:
    grasp_set = generate_grasps("agentview", selected_segmentation, backend="contact-graspnet")
    handle_grasp = select_grasp(grasp_set, strategy="top_down") if grasp_set.ok else None
    result["handle_grasp_found"] = handle_grasp is not None
    if handle_grasp is not None:
        result["handle_grasp_pose"] = (
            tuple(handle_grasp.pose.position),
            tuple(handle_grasp.pose.quaternion_wxyz),
        )
if active:
    hx, hy, hz = selected_center
    dx = hx - cc[0]
    dy = hy - cc[1]
    norm = (dx * dx + dy * dy) ** 0.5
    if norm < 0.02:
        active = False
        result["stage"] = "pull_axis_missing"
    else:
        dx = dx / norm
        dy = dy / norm
        contact_x = quantile((p[0] for p in selected_points), 0.10)
        contact_y = hy - 0.035
        result["handle_center"] = selected_center
        result["pull_axis"] = (dx, dy)
        result["inset_contact"] = (contact_x, contact_y, hz + 0.01)
if active:
    result["stage"] = "open_drawer"
    open_gripper()
    cabinet_top = quantile((p[2] for p in cabinet.point_cloud.points), 0.95)
    staging_z = max(hz + 0.18, cabinet_top + 0.10)
    outside_x = contact_x
    outside_y = hy + 0.22
    active = move("outside_high", (outside_x, outside_y, staging_z), downward, frame, 220)
    if active:
        rotate = move_to_pose(Pose((outside_x, outside_y, staging_z), handle_orientation, frame),
                              tolerance=0.04, max_steps=400)
        result["motions"].append(("rotate_side", bool(rotate.ok), str(rotate.status), int(rotate.steps_executed)))
        active = bool(rotate.ok)
    if active:
        active = move("outside_low", (outside_x, outside_y, hz + 0.025), handle_orientation, frame, 160)
    if active:
        active = move("lateral_align", (contact_x, outside_y, hz + 0.025), handle_orientation, frame, 160)
    if active:
        active = move("handle_contact", (contact_x, contact_y, hz + 0.025), handle_orientation, frame, 160)
    if active:
        close = close_gripper()
        result["close_handle"] = (bool(close.ok), str(close.status), int(close.steps_executed))
        result["handle_pose_after_contact"] = tuple(get_robot_state().end_effector_poses["primary"].position)
        result["handle_gripper_width"] = float(get_robot_state().gripper_positions["primary"])
        active = bool(close.ok)
    if active:
        held = get_robot_state().end_effector_poses["primary"]
        for offset in (0.04, 0.08, 0.12, 0.16, 0.20, 0.24):
            if active:
                active = move("drawer_pull_" + str(offset),
                              (held.position[0], held.position[1] + offset, held.position[2]),
                              tuple(held.quaternion_wxyz), held.frame, 220)
    if active:
        opened, opened_prompt = locate(("inside of the open top drawer", "open top drawer", "top drawer interior"), frame, 20)
        result["open_top_drawer_found"] = opened is not None
        if opened is not None:
            opened_center = center(opened.point_cloud.points)
            result["open_top_drawer_center"] = opened_center
            result["open_top_drawer_prompt"] = opened_prompt
            planar_shift = ((opened_center[0] - cc[0]) ** 2 + (opened_center[1] - cc[1]) ** 2) ** 0.5
            result["open_top_drawer_planar_shift"] = planar_shift
            if planar_shift > 0.10:
                result["placement_center"] = opened_center
        open_gripper()
        active = move("clear_handle", (contact_x, contact_y + 0.29, hz + 0.15), handle_orientation, frame, 180)
if active:
    result["stage"] = "bowl_grasp"
    gx = bc[0]
    gy = quantile((p[1] for p in bowl.point_cloud.points), 0.1) + 0.01
    gz = quantile((p[2] for p in bowl.point_cloud.points), 0.9) - 0.005
    active = move("bowl_above", (gx, gy, gz + 0.12), downward, frame, 180)
    if active:
        active = move("bowl_contact", (gx, gy, gz), downward, frame, 140)
    if active:
        close = close_gripper()
        result["close_bowl"] = (bool(close.ok), str(close.status), int(close.steps_executed))
        result["bowl_gripper_width"] = float(get_robot_state().gripper_positions["primary"])
        active = bool(close.ok)
    if active:
        active = move("bowl_lift", (gx, gy, gz + 0.18), downward, frame, 180)
    if active:
        after_bowl, after_prompt = locate(("gray bowl", "silver bowl", "bowl"), frame, 30)
        result["bowl_after_prompt"] = after_prompt
        if after_bowl is not None:
            result["bowl_after_center"] = center(after_bowl.point_cloud.points)
if active:
    result["stage"] = "place"
    if "placement_center" in result:
        target_x, target_y, target_z = result["placement_center"]
        target_z += 0.04
    else:
        target_x = hx + dx * 0.09
        target_y = hy + dy * 0.09
        target_z = hz + 0.08
    active = move("transport", (target_x, target_y, max(gz + 0.18, target_z + 0.14)), downward, frame, 220)
    if active:
        active = move("lower", (target_x, target_y, target_z), downward, frame, 160)
    if active:
        release = open_gripper()
        result["release"] = (bool(release.ok), int(release.steps_executed))
        result["stage"] = "done"
