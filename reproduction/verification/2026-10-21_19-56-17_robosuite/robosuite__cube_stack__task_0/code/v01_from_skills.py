import math

def quantile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int((len(ordered) - 1) * fraction)]

def locate(prompt):
    found = localize_object(prompt, camera_name="agentview", target_frame=frame)
    if not found.ok or len(found.point_cloud.points) < 20:
        raise ValueError("localization failed: " + prompt)
    return found

def move(position, cap=220):
    for attempt in range(3):
        motion = move_to_pose(Pose(position, downward, frame), tolerance=0.015, max_steps=cap)
        report["motions"].append(motion)
        if motion.ok:
            return
        if motion.status != "timeout":
            break
    raise ValueError("motion failed after bounded convergence retries")

state = get_robot_state()
frame = state.base_frame
report = {"task": get_task_context().language, "motions": []}
picked = locate("red cube")
target = locate("green cube")
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
# Estimate cube yaw from the smallest horizontal top-cloud bounding square.
top_points = [p for p in points if float(p[2]) > top - 0.006]
best_area = None
yaw = 0.0
for angle_index in range(90):
    angle = angle_index * math.pi / 180.0
    cs = math.cos(angle)
    sn = math.sin(angle)
    us = [cs * float(p[0]) + sn * float(p[1]) for p in top_points]
    vs = [-sn * float(p[0]) + cs * float(p[1]) for p in top_points]
    area = (quantile(us, 0.98) - quantile(us, 0.02)) * (quantile(vs, 0.98) - quantile(vs, 0.02))
    if best_area is None or area < best_area:
        best_area = area
        yaw = angle
downward = (0.0, math.cos(yaw / 2.0), math.sin(yaw / 2.0), 0.0)
report["yaw"] = yaw
report["grasp"] = [x, y, grasp_z]
report["width"] = observed_width
open_gripper()
move((x, y, grasp_z + 0.15), cap=250)
move((x, y, grasp_z), cap=220)
if not close_gripper().ok:
    raise ValueError("close failed")
move((x, y, grasp_z + 0.18), cap=250)
after = locate("red cube")
report["grasp_verified"] = quantile((p[2] for p in after.point_cloud.points), 0.5) - quantile((p[2] for p in points), 0.5) > 0.02
if not report["grasp_verified"]:
    raise ValueError("cube not lifted")
tpoints = target.point_cloud.points
tsurface = quantile((p[2] for p in tpoints), 0.9)
top_plane = [p for p in tpoints if float(p[2]) > tsurface - 0.008]
tx = quantile((p[0] for p in top_plane), 0.5)
ty = quantile((p[1] for p in top_plane), 0.5)
clearance = grasp_z - (top - observed_width)
transit_z = max(grasp_z + 0.18, tsurface + clearance + 0.12)
move((tx, ty, transit_z), cap=260)
move((tx, ty, tsurface + clearance + 0.008), cap=220)
open_gripper()
move((tx, ty, transit_z), cap=220)
state = get_robot_state()
for tick in range(20):
    step(RobotAction(arms={"primary": ArmCommand("joint_position", state.joint_positions["primary"], gripper_position=1.0)}))
result = report
