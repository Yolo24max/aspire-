import math

result = {"task": get_task_context().language, "phase": "perception", "motions": []}
frame = get_robot_state().base_frame
camera = "agentview"

def quantile(values, fraction):
    values = sorted(float(value) for value in values)
    return values[int((len(values) - 1) * fraction)]

def center(points):
    return [quantile([p[k] for p in points], 0.5) for k in range(3)]

def quaternion_from_columns(x, y, z):
    m = [[x[r], y[r], z[r]] for r in range(3)]
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = [s / 4, (m[2][1]-m[1][2])/s, (m[0][2]-m[2][0])/s, (m[1][0]-m[0][1])/s]
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0]-m[1][1]-m[2][2]) * 2.0
        q = [(m[2][1]-m[1][2])/s, s/4, (m[0][1]+m[1][0])/s, (m[0][2]+m[2][0])/s]
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1]-m[0][0]-m[2][2]) * 2.0
        q = [(m[0][2]-m[2][0])/s, (m[0][1]+m[1][0])/s, s/4, (m[1][2]+m[2][1])/s]
    else:
        s = math.sqrt(1.0 + m[2][2]-m[0][0]-m[1][1]) * 2.0
        q = [(m[1][0]-m[0][1])/s, (m[0][2]+m[2][0])/s, (m[1][2]+m[2][1])/s, s/4]
    length = math.sqrt(sum(v*v for v in q))
    return [v/length for v in q]

cabinet = None
for prompt in ("cabinet", "drawer cabinet", "black cabinet"):
    observed = localize_object(prompt, camera_name=camera, target_frame=frame)
    if observed.ok and len(observed.point_cloud.points) >= 100:
        cabinet = observed
        result["cabinet_prompt"] = prompt
        break
if cabinet is None:
    raise ValueError("cabinet localization unavailable; no motion attempted")
cabinet_points = cabinet.point_cloud.points
cabinet_center = center(cabinet_points)
cabinet_low = quantile([p[2] for p in cabinet_points], 0.02)
cabinet_high = quantile([p[2] for p in cabinet_points], 0.98)
cabinet_height = cabinet_high - cabinet_low

handles = []
result["handle_probes"] = []
for prompt in ("drawer handle", "black drawer handle", "cabinet handle"):
    masks = segment_text(camera, prompt)
    candidates = []
    if masks.ok:
        for mask in masks.segmentations:
            cloud = mask_to_point_cloud(mask, camera, target_frame=frame)
            points = cloud.points
            if len(points) < 20:
                continue
            c = center(points)
            zspan = quantile([p[2] for p in points], 0.95) - quantile([p[2] for p in points], 0.05)
            if c[2] < cabinet_low - 0.02 or c[2] > cabinet_high + 0.02:
                continue
            # An all-handles mask is split only when three separated Z bands are observed.
            if zspan > 0.45 * cabinet_height:
                heights = [quantile([p[2] for p in points], q) for q in (0.15, 0.5, 0.85)]
                clusters = []
                for iteration in range(8):
                    clusters = [[], [], []]
                    for p in points:
                        distances = [abs(float(p[2]) - h) for h in heights]
                        index = distances.index(min(distances))
                        clusters[index].append(p)
                    if any(len(group) < 10 for group in clusters):
                        break
                    heights = [quantile([p[2] for p in group], 0.5) for group in clusters]
                if all(len(group) >= 10 for group in clusters):
                    spans = [quantile([p[2] for p in group], 0.9) - quantile([p[2] for p in group], 0.1) for group in clusters]
                    spacing = min(heights[1]-heights[0], heights[2]-heights[1])
                    if spacing > 1.3 * max(spans):
                        for group in clusters:
                            candidates.append({"center": center(group), "points": group, "score": float(mask.score)})
            else:
                candidates.append({"center": c, "points": points, "score": float(mask.score)})
    unique = []
    for candidate in sorted(candidates, key=lambda item: -item["score"]):
        if not any(abs(candidate["center"][2]-other["center"][2]) < 0.08*cabinet_height for other in unique):
            unique.append(candidate)
    result["handle_probes"].append({"prompt": prompt, "candidates": [{"center": h["center"], "score": h["score"], "points": len(h["points"])} for h in unique]})
    if len(unique) == 3:
        handles = sorted(unique, key=lambda item: item["center"][2])
        result["handle_prompt"] = prompt
        break
if len(handles) != 3:
    raise ValueError("need three distinct observed handle heights to identify middle drawer")
handle = handles[1]
points = handle["points"]
c = handle["center"]
mx = sum(float(p[0]) for p in points)/len(points)
my = sum(float(p[1]) for p in points)/len(points)
xx = sum((float(p[0])-mx)**2 for p in points)
yy = sum((float(p[1])-my)**2 for p in points)
xy = sum((float(p[0])-mx)*(float(p[1])-my) for p in points)
angle = 0.5 * math.atan2(2*xy, xx-yy)
normal = [-math.sin(angle), math.cos(angle), 0.0]
if sum(normal[k]*(c[k]-cabinet_center[k]) for k in range(2)) < 0:
    normal = [-v for v in normal]
orientation = quaternion_from_columns([0.0, 0.0, 1.0], [-normal[1], normal[0], 0.0], [-normal[0], -normal[1], 0.0])
depths = [float(p[0])*normal[0] + float(p[1])*normal[1] for p in cabinet_points]
stroke = max(0.12, min(0.24, 0.75*(quantile(depths, 0.95)-quantile(depths, 0.05))))
result["handle_center"] = c
result["outward_normal"] = normal
result["stroke"] = stroke
result["orientation"] = orientation
result["phase"] = "approach"

def move(label, position, budget):
    strategy = MotionStrategy(pose_planner="curobo-integrated") if label == "raised_standoff" else MotionStrategy()
    motion = None
    for attempt in range(3):
        motion = move_to_pose(Pose(position, orientation, frame), tolerance=0.012, max_steps=budget, strategy=strategy)
        result["motions"].append({"phase": label, "attempt": attempt, "ok": bool(motion.ok), "status": str(motion.status), "steps": motion.steps_executed})
        if motion.ok or "TIMEOUT" not in str(motion.status).upper():
            break
    if not motion.ok:
        print(result)
        raise ValueError("motion failed: " + label)

open_gripper()
move("raised_standoff", [c[0]+0.10*normal[0], c[1]+0.10*normal[1], c[2]+0.10], 140)
move("handle_standoff", [c[0]+0.10*normal[0], c[1]+0.10*normal[1], c[2]], 140)
move("contact", [c[0]-0.004*normal[0], c[1]-0.004*normal[1], c[2]], 140)
grip = close_gripper()
result["grip"] = {"ok": bool(grip.ok), "status": str(grip.status), "steps": grip.steps_executed}
if not grip.ok:
    raise ValueError("handle closing failed")
result["phase"] = "pull"
for part in range(1, 5):
    distance = stroke*part/4.0 - 0.004
    move("pull_" + str(part), [c[0]+distance*normal[0], c[1]+distance*normal[1], c[2]], 100)
open_gripper()
result["phase"] = "complete_unverified"


