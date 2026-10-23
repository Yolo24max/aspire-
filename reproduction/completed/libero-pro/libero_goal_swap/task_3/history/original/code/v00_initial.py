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
    result["motions"].append((name, bool(motion.ok), str(motion.status),
                              int(motion.steps_executed)))
    return bool(motion.ok)


state = get_robot_state()
frame = state.base_frame
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
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
    selected = None
    selected_center = None
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
            if distance > 0.35 or hc[2] < cc[2] - 0.08 or hc[2] > cc[2] + 0.30:
                continue
            if selected_center is None or hc[2] > selected_center[2]:
                selected = candidate
                selected_center = hc
                result["handle_prompt"] = prompt
        if selected is not None:
            break
    if selected is None:
        active = False
        result["stage"] = "handle_missing"
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
        result["handle_center"] = selected_center
        result["pull_axis"] = (dx, dy)
if active:
    result["stage"] = "open_drawer"
    open_gripper()
    active = move("handle_above", (hx, hy, hz + 0.11), downward, frame)
    if active:
        active = move("handle_contact", (hx, hy, hz), downward, frame, 120)
    if active:
        close = close_gripper()
        result["close_handle"] = (bool(close.ok), str(close.status), int(close.steps_executed))
        active = bool(close.ok)
    if active:
        active = move("drawer_pull", (hx + dx * 0.22, hy + dy * 0.22, hz), downward, frame, 180)
    if active:
        open_gripper()
        active = move("clear_handle", (hx + dx * 0.22, hy + dy * 0.22, hz + 0.14), downward, frame)
if active:
    result["stage"] = "bowl_grasp"
    grasp_set = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet")
    grasp = select_grasp(grasp_set, strategy="top_down") if grasp_set.ok else None
    result["grasp_found"] = grasp is not None
    if grasp is None:
        gx, gy, gz = bc[0], bc[1], quantile((p[2] for p in bowl.point_cloud.points), 0.9)
        grip_orientation = downward
    else:
        gx, gy, gz = grasp.pose.position
        grip_orientation = tuple(grasp.pose.quaternion_wxyz)
    result["grasp_xyz"] = (gx, gy, gz)
    active = move("bowl_above", (gx, gy, gz + 0.12), grip_orientation, frame)
    if active:
        active = move("bowl_contact", (gx, gy, gz), grip_orientation, frame, 120)
    if active:
        close = close_gripper()
        result["close_bowl"] = (bool(close.ok), str(close.status), int(close.steps_executed))
        active = bool(close.ok)
    if active:
        active = move("bowl_lift", (gx, gy, gz + 0.18), grip_orientation, frame)
if active:
    result["stage"] = "place"
    target_x = hx + dx * 0.09
    target_y = hy + dy * 0.09
    target_z = hz + 0.08
    active = move("transport", (target_x, target_y, max(gz + 0.18, target_z + 0.14)), grip_orientation, frame, 220)
    if active:
        active = move("lower", (target_x, target_y, target_z), grip_orientation, frame, 160)
    if active:
        release = open_gripper()
        result["release"] = (bool(release.ok), int(release.steps_executed))
        result["stage"] = "done"
