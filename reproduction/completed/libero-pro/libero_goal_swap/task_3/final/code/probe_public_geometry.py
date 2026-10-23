def q(values, f):
    values = sorted(float(v) for v in values)
    return values[int((len(values)-1)*f)]
def describe(points):
    return [[q((p[axis] for p in points), f) for f in (0.02,0.1,0.5,0.9,0.98)] for axis in range(3)]
report = {"task": get_task_context().language, "objects": []}
frame = get_robot_state().base_frame
for prompt in ("drawer handle", "top drawer handle", "black cabinet", "grey bowl", "bowl"):
    seg = segment_text("agentview", prompt)
    entry = {"prompt":prompt, "ok":seg.ok, "candidates":[]}
    if seg.ok:
        for mask in seg.segmentations[:5]:
            cloud = mask_to_point_cloud(mask, "agentview", target_frame=frame)
            if len(cloud.points) >= 20:
                geom = estimate_geometry(cloud)
                entry["candidates"].append({"score":mask.score, "box":mask.box_xyxy, "quantiles":describe(cloud.points), "geometry":geom})
    report["objects"].append(entry)
result = report
