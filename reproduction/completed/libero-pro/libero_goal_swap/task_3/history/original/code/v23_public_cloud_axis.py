import math


def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]


def center(points):
    return tuple(quantile((p[i] for p in points), 0.5) for i in range(3))


def handles(cabinet_center, frame):
    found = segment_text("agentview", "drawer handle")
    candidates = []
    if found.ok:
        for mask in found.segmentations:
            cloud = mask_to_point_cloud(mask, "agentview", target_frame=frame)
            if len(cloud.points) < 30:
                continue
            c = center(cloud.points)
            distance = math.hypot(c[0] - cabinet_center[0], c[1] - cabinet_center[1])
            if distance < 0.35 and abs(c[2] - cabinet_center[2]) < 0.25:
                candidates.append((c, cloud.points))
    return candidates


def move(name, xyz, quaternion, cap=160):
    motion = move_to_pose(Pose(xyz, quaternion, frame), tolerance=0.025, max_steps=cap)
    actual = get_robot_state().end_effector_poses["primary"]
    error = math.sqrt(sum((float(actual.position[i]) - xyz[i]) ** 2 for i in range(3)))
    result["motions"].append({"name": name, "ok": bool(motion.ok),
                              "status": str(motion.status), "steps": int(motion.steps_executed),
                              "actual": tuple(actual.position), "error": error})
    return bool(motion.ok)


state = get_robot_state()
frame = state.base_frame
down = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
result = {"task": get_task_context().language, "stage": "localize", "motions": [],
          "provenance": "public point clouds and pre-v16 public top-down branch; no baseline constants"}
cabinet = localize_object("black drawer cabinet", camera_name="agentview", target_frame=frame)
active = cabinet.ok and len(cabinet.point_cloud.points) > 100
if active:
    cc = center(cabinet.point_cloud.points)
    candidates = handles(cc, frame)
    result["candidates_before"] = [item[0] for item in candidates]
    active = len(candidates) >= 3
if active:
    hc, points = max(candidates, key=lambda item: item[0][2])
    mean_x = sum(float(p[0]) for p in points) / len(points)
    mean_y = sum(float(p[1]) for p in points) / len(points)
    xx = sum((float(p[0]) - mean_x) ** 2 for p in points)
    yy = sum((float(p[1]) - mean_y) ** 2 for p in points)
    xy = sum((float(p[0]) - mean_x) * (float(p[1]) - mean_y) for p in points)
    yaw = 0.5 * math.atan2(2.0 * xy, xx - yy)
    tx, ty = math.cos(yaw), math.sin(yaw)
    nx, ny = -ty, tx
    if nx * (hc[0] - cc[0]) + ny * (hc[1] - cc[1]) < 0:
        nx, ny = -nx, -ny
    # Align tool X to the observed rod; the jaw axis then spans its short dimension.
    c, s = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    grasp_q = (c * down[0] - s * down[3], c * down[1] - s * down[2],
               c * down[2] + s * down[1], c * down[3] + s * down[0])
    gx, gy = hc[0] + nx * 0.005, hc[1] + ny * 0.005
    gz = hc[2] - 0.012
    result["handle_center"] = hc
    result["rod_axis"] = (tx, ty)
    result["outward_normal"] = (nx, ny)
    result["grasp_pose"] = ((gx, gy, gz), grasp_q)
    result["stage"] = "approach"
    open_gripper()
    top = quantile((p[2] for p in cabinet.point_cloud.points), 0.95)
    high = max(top + 0.12, gz + 0.18)
    active = move("outside_high", (gx + nx * 0.14, gy + ny * 0.14, high), grasp_q, 220)
    if active:
        active = move("outside_low", (gx + nx * 0.14, gy + ny * 0.14, gz), grasp_q)
    if active:
        active = move("contact", (gx, gy, gz), grasp_q)
    if active:
        result["stage"] = "grasp"
        close = close_gripper()
        result["gripper_after_close"] = float(get_robot_state().gripper_positions["primary"])
        active = bool(close.ok)
    if active:
        result["stage"] = "pull"
        active = move("pull", (gx + nx * 0.22, gy + ny * 0.22, gz), grasp_q, 200)
    open_gripper()
    current = get_robot_state().end_effector_poses["primary"].position
    move("clear", (float(current[0]), float(current[1]), high), grasp_q)
    after = handles(cc, frame)
    result["candidates_after"] = [item[0] for item in after]
    same_height = [item[0] for item in after if abs(item[0][2] - hc[2]) < 0.035]
    result["handle_motion_verified"] = False
    if same_height:
        observed = min(same_height, key=lambda c: abs(c[2] - hc[2]))
        displacement = (observed[0] - hc[0]) * nx + (observed[1] - hc[1]) * ny
        result["handle_displacement_m"] = displacement
        result["handle_motion_verified"] = displacement > 0.06
    result["stage"] = "drawer_probe_complete"
