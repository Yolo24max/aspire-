prompts = (
    "wine bottle",
    "black wine bottle",
    "bottle",
    "drawer cabinet",
    "black cabinet",
    "drawer",
    "top of the drawer",
    "wooden rack",
)

def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

state = get_robot_state()
report = {
    "language": get_task_context().language,
    "frame": state.base_frame,
    "eef_position": list(state.end_effector_poses["primary"].position),
    "eef_quaternion": list(state.end_effector_poses["primary"].quaternion_wxyz),
    "objects": [],
}
for prompt in prompts:
    found = segment_text("agentview", prompt)
    item = {"prompt": prompt, "ok": bool(found.ok), "candidates": []}
    if found.ok:
        for candidate in found.segmentations[:3]:
            entry = {"score": float(candidate.score), "box": list(candidate.box_xyxy) if candidate.box_xyxy is not None else None}
            cloud = mask_to_point_cloud(candidate, "agentview", target_frame=state.base_frame)
            points = cloud.points
            entry["point_count"] = len(points)
            if len(points) >= 20:
                entry["xyz_quantiles"] = [[quantile((point[axis] for point in points), fraction) for fraction in (0.05, 0.5, 0.95)] for axis in range(3)]
                geometry = estimate_geometry(cloud)
                entry["geometry_center"] = list(geometry.pose.position)
                entry["geometry_extents"] = list(geometry.extents)
            item["candidates"].append(entry)
    report["objects"].append(item)

open_gripper()
result = report
