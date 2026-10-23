import math

result = {"task": get_task_context().language, "phase": "localize", "motions": [], "candidates": []}
base_frame = get_robot_state().base_frame

def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def center_of(points):
    return tuple(quantile([p[axis] for p in points], 0.5) for axis in range(3))

def motion_ok(motion):
    if motion.terminated or motion.truncated:
        result["phase"] = "environment_ended"
        result["environment_terminated"] = bool(motion.terminated)
        result["environment_truncated"] = bool(motion.truncated)
        return False
    return bool(motion.ok)

def move(position, quaternion, label, tries=2):
    for attempt in range(tries):
        motion = move_to_pose(Pose(tuple(position), quaternion, base_frame), tolerance=0.012, max_steps=120)
        state = get_robot_state()
        achieved = state.end_effector_poses["primary"].position
        result["motions"].append({"label": label, "attempt": attempt + 1, "commanded": list(position), "achieved": [float(v) for v in achieved], "ok": bool(motion.ok), "status": str(motion.status), "steps": int(motion.steps_executed)})
        if motion.terminated or motion.truncated:
            result["phase"] = "environment_ended"
            result["environment_terminated"] = bool(motion.terminated)
            result["environment_truncated"] = bool(motion.truncated)
            return False
        if motion.ok:
            return True
    result["phase"] = label + "_failed"
    return False

def main():
    handles = []
    for prompt in ("drawer handle", "black drawer handle", "cabinet handle"):
        found = segment_text("agentview", prompt)
        if not found.ok:
            continue
        for candidate in found.segmentations[:10]:
            cloud = mask_to_point_cloud(candidate, "agentview", target_frame=base_frame)
            if len(cloud.points) < 20:
                continue
            geometry = estimate_geometry(cloud)
            points = cloud.points
            center = center_of(points)
            duplicate = False
            for entry in handles:
                if sum((center[k] - entry["center"][k]) ** 2 for k in range(3)) < 0.0004:
                    duplicate = True
            result["candidates"].append({"prompt": prompt, "score": float(candidate.score), "center": list(center), "extents": [float(v) for v in geometry.extents], "points": len(points), "duplicate": duplicate})
            if not duplicate:
                handles.append({"center": center, "points": points, "score": float(candidate.score)})
        if len(handles) >= 3:
            break
    if len(handles) < 3:
        result["phase"] = "insufficient_handles"
        return
    handles = sorted(handles, key=lambda entry: entry["center"][2])
    target = handles[len(handles) // 2]
    center = target["center"]
    points = target["points"]
    result["selection"] = {"relation": "middle_by_own_height", "own_height_column": [entry["center"][2] for entry in handles], "proximity_column": [math.sqrt(entry["center"][0] ** 2 + entry["center"][1] ** 2) for entry in handles], "support_gap_column": None, "support_gap_reason": "articulated handles; support gap does not define drawer identity", "target": list(center)}
    dx = [float(p[0]) - center[0] for p in points]
    dy = [float(p[1]) - center[1] for p in points]
    xx = sum(v * v for v in dx) / len(dx)
    yy = sum(v * v for v in dy) / len(dy)
    xy = sum(dx[k] * dy[k] for k in range(len(dx))) / len(dx)
    angle = 0.5 * math.atan2(2.0 * xy, xx - yy)
    axis = (math.cos(angle), math.sin(angle))
    normal = (-axis[1], axis[0])
    if normal[0] * center[0] + normal[1] * center[1] > 0.0:
        normal = (-normal[0], -normal[1])
    quaternion = (0.0, math.cos(angle / 2.0), math.sin(angle / 2.0), 0.0)
    handle_length = quantile([p[0] * axis[0] + p[1] * axis[1] for p in points], 0.95) - quantile([p[0] * axis[0] + p[1] * axis[1] for p in points], 0.05)
    result["geometry"] = {"axis": list(axis), "normal": list(normal), "handle_length": handle_length, "quaternion": list(quaternion)}
    grasp = (center[0], center[1], center[2])
    above = (grasp[0] + normal[0] * 0.015, grasp[1] + normal[1] * 0.015, grasp[2] + 0.10)
    if not motion_ok(open_gripper()):
        return
    result["phase"] = "approach"
    if not move(above, quaternion, "first_approach", tries=3):
        if result["phase"] == "environment_ended":
            return
        current = get_robot_state().end_effector_poses["primary"].position
        stage = (float(current[0]), float(current[1]), max(float(current[2]), above[2]) + 0.08)
        if not move(stage, quaternion, "stage_after_three_failures"):
            return
        if not move(above, quaternion, "approach_after_stage"):
            return
    if not move(grasp, quaternion, "descend"):
        return
    if not motion_ok(close_gripper()):
        return
    result["jaw_at_close"] = float(get_robot_state().gripper_positions["primary"])
    result["phase"] = "pull"
    pull_distance = max(0.16, min(0.24, handle_length * 2.0))
    for pull_index in range(1, 9):
        distance = pull_distance * pull_index / 8.0
        pulled = (grasp[0] + normal[0] * distance, grasp[1] + normal[1] * distance, grasp[2])
        if not move(pulled, quaternion, "pull_" + str(pull_index)):
            return
    result["jaw_after_pull"] = float(get_robot_state().gripper_positions["primary"])
    result["phase"] = "pull_completed"

main()
