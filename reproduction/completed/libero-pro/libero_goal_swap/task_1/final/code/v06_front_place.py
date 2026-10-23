import math

def q(values, fraction):
    ordered = sorted(float(v) for v in values)
    return ordered[int((len(ordered)-1)*fraction)]

def locate(prompts):
    for prompt in prompts:
        found = localize_object(prompt, camera_name="agentview", target_frame=frame)
        if found.ok and len(found.point_cloud.points) >= 20:
            return found
    raise ValueError("localization failed")

def quant(points, axis, fraction):
    return q([p[axis] for p in points], fraction)

def move(position, rotation, label, cap=160):
    start = get_robot_state().end_effector_poses["primary"].position
    distance = math.sqrt(sum((float(position[a])-float(start[a]))**2 for a in range(3)))
    count = max(1,int(math.ceil(distance/0.035)))
    for segment in range(1,count+1):
        waypoint = tuple(float(start[a])+(float(position[a])-float(start[a]))*segment/count for a in range(3))
        ik = solve_ik(Pose(waypoint, rotation, frame))
        if not ik.ok:
            raise ValueError("IK failed: " + label)
        reached = False
        previous_error = None
        stalled = 0
        for joint_stage in range(24):
            state = get_robot_state()
            delta = [float(ik.joint_positions[a])-float(state.joint_positions["primary"][a]) for a in range(len(ik.joint_positions))]
            biggest = max(abs(v) for v in delta)
            fraction = min(1.0,0.14/max(biggest,0.00001))
            command = [float(state.joint_positions["primary"][a])+fraction*delta[a] for a in range(len(delta))]
            moved = move_to_joints(command,tolerance=0.025,max_steps=18)
            state = get_robot_state()
            measured = state.end_effector_poses["primary"].position
            error = math.sqrt(sum((float(measured[a])-float(waypoint[a]))**2 for a in range(3)))
            remaining = max(abs(float(ik.joint_positions[a])-float(state.joint_positions["primary"][a])) for a in range(len(delta)))
            if error <= 0.018 and remaining <= 0.05:
                reached = True
                break
            if previous_error is not None and previous_error-remaining < 0.001:
                stalled += 1
            else:
                stalled = 0
            previous_error = remaining
            if stalled >= 3:
                break
        if not reached:
            raise ValueError("bounded joint staging failed: " + label)
    report["moves"].append({"label":label,"ok":reached,"position_error":error})

context = get_task_context()
frame = get_robot_state().base_frame
report = {"task":context.language, "moves":[]}
result = report
picked = locate(("grey bowl", "bowl"))
target = locate(("stove", "hot plate"))
p = picked.point_cloud.points
t = target.point_cloud.points
cx, cy = float(picked.geometry.pose.position[0]), float(picked.geometry.pose.position[1])
low, high = quant(p,2,0.05), quant(p,2,0.95)
tx, ty, tz = quant(t,0,0.5), quant(t,1,0.5), quant(t,2,0.9)
bowl_radius_x = (quant(p,0,0.95)-quant(p,0,0.05))/2.0
tx = max(tx,quant(t,0,0.95)-bowl_radius_x-0.01)
grasps = generate_grasps("agentview", picked.segmentation, backend="contact-graspnet", max_candidates=10)
grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
if grasp is None:
    home_rotation = get_robot_state().end_effector_poses["primary"].quaternion_wxyz
    yaw = math.pi/2.0
    c,s = math.cos(yaw/2.0),math.sin(yaw/2.0)
    rotated = (c*home_rotation[0]-s*home_rotation[3], c*home_rotation[1]-s*home_rotation[2], c*home_rotation[2]+s*home_rotation[1], c*home_rotation[3]+s*home_rotation[0])
    grasp_pose = Pose((quant(p,0,0.85), picked.geometry.pose.position[1], high-0.012), rotated, frame)
if grasp is not None:
    grasp_pose = grasp.pose
gp = grasp_pose.position
rot = grasp_pose.quaternion_wxyz
report["object"] = {"center":[cx,cy], "low":low, "high":high}
report["target"] = [tx,ty,tz]
report["grasp"] = [float(v) for v in gp]
clearance = max(high,tz) + 0.18
open_gripper()
move((gp[0],gp[1],max(gp[2]+0.12,clearance)),rot,"pregrasp")
move(gp,rot,"grasp")
close_gripper()
move((gp[0],gp[1],clearance),rot,"lift")
after = localize_object("bowl",camera_name="agentview",target_frame=frame)
report["lift_observed"] = after.ok and len(after.point_cloud.points)>=20 and quant(after.point_cloud.points,2,0.5)>quant(p,2,0.5)+0.025
place_x,place_y = tx+gp[0]-cx,ty+gp[1]-cy
move((place_x,place_y,clearance),rot,"transport")
try:
    move((place_x,place_y,tz+gp[2]-low+0.018),rot,"lower")
except Exception:
    measured=get_robot_state().end_effector_poses["primary"].position
    if math.sqrt((float(measured[0])-place_x)**2+(float(measured[1])-place_y)**2)>0.025:
        raise ValueError("placement XY blocked")
    report["lower_contact_blocked"]=True
open_gripper()
move((place_x,place_y,clearance),rot,"retract")
state=get_robot_state()
for tick in range(15):
    step(RobotAction(arms={"primary":ArmCommand("joint_position",state.joint_positions["primary"],gripper_position=1.0)}))
landed=localize_object("bowl",camera_name="agentview",target_frame=frame)
if landed.ok:
    report["landed_center"]=[quant(landed.point_cloud.points,a,0.5) for a in range(3)]
result=report






