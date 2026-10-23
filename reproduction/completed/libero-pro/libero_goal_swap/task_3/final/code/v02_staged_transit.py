import math

def q(values, fraction):
    values = sorted(float(v) for v in values)
    return values[int((len(values) - 1) * fraction)]

def center(points):
    return tuple((q((p[a] for p in points), 0.05) + q((p[a] for p in points), 0.95)) / 2 for a in range(3))

def locate(prompts):
    for prompt in prompts:
        found = localize_object(prompt, camera_name="agentview", target_frame=frame)
        if found.ok and len(found.point_cloud.points) >= 100:
            return found
    raise ValueError("localization failed")

def handles(cabinet_bottom, cabinet_top):
    found = segment_text("agentview", "drawer handle")
    candidates = []
    if found.ok:
        for mask in found.segmentations:
            if float(mask.score) < 0.35:
                continue
            cloud = mask_to_point_cloud(mask, "agentview", target_frame=frame)
            pts = cloud.points
            if len(pts) < 50:
                continue
            z = q((p[2] for p in pts), 0.85)
            bar = [p for p in pts if abs(float(p[2]) - z) < 0.012]
            if len(bar) < 30:
                continue
            c = center(bar)
            if c[2] > cabinet_bottom and c[2] < cabinet_top + 0.02:
                candidates.append((c, bar))
    if len(candidates) < 2:
        raise ValueError("fewer than two plausible handles")
    candidates = sorted(candidates, key=lambda item: item[0][2])
    return candidates

def quat_columns(x, y, z):
    # Quaternion from a right-handed rotation matrix.
    trace = x[0] + y[1] + z[2]
    if trace > 0:
        s = math.sqrt(trace + 1) * 2
        return (0.25*s, (y[2]-z[1])/s, (z[0]-x[2])/s, (x[1]-y[0])/s)
    if x[0] > y[1] and x[0] > z[2]:
        s = math.sqrt(1+x[0]-y[1]-z[2])*2
        return ((y[2]-z[1])/s, 0.25*s, (y[0]+x[1])/s, (z[0]+x[2])/s)
    if y[1] > z[2]:
        s = math.sqrt(1+y[1]-x[0]-z[2])*2
        return ((z[0]-x[2])/s, (y[0]+x[1])/s, 0.25*s, (z[1]+y[2])/s)
    s = math.sqrt(1+z[2]-x[0]-y[1])*2
    return ((x[1]-y[0])/s, (z[0]+x[2])/s, (z[1]+y[2])/s, 0.25*s)

def move(name, xyz, orientation, cap=160):
    pose = Pose(tuple(xyz), tuple(orientation), frame)
    outcome = move_to_pose(pose, tolerance=0.018, max_steps=cap)
    report["motions"].append({"stage":name, "ok":outcome.ok, "status":outcome.status, "steps":outcome.steps_executed})
    if not outcome.ok:
        raise ValueError(name + " motion failed")
    return get_robot_state().end_effector_poses["primary"]

def shifted(c, n, amount, dz=0):
    return (c[0]+n[0]*amount, c[1]+n[1]*amount, c[2]+dz)

def execute():
    cabinet = locate(("black cabinet",))
    cp = cabinet.point_cloud.points
    cabinet_bottom = q((p[2] for p in cp), 0.02)
    cabinet_top = q((p[2] for p in cp), 0.90)
    bowl = locate(("grey bowl", "bowl"))
    initial_bowl = center(bowl.point_cloud.points)
    hs = handles(cabinet_bottom, cabinet_top)
    h, bar = hs[-1]
    lower_h = hs[-2][0]
    layer_height = h[2] - lower_h[2]
    mx = sum(float(p[0]) for p in bar)/len(bar)
    my = sum(float(p[1]) for p in bar)/len(bar)
    xx = sum((float(p[0])-mx)**2 for p in bar)
    yy = sum((float(p[1])-my)**2 for p in bar)
    xy = sum((float(p[0])-mx)*(float(p[1])-my) for p in bar)
    angle = 0.5*math.atan2(2*xy, xx-yy)
    axis = (math.cos(angle), math.sin(angle), 0.0)
    normal = (-axis[1], axis[0], 0.0)
    cc = center(cp)
    if (h[0]-cc[0])*normal[0] + (h[1]-cc[1])*normal[1] < 0:
        normal = (-normal[0], -normal[1], 0.0)
        axis = (-axis[0], -axis[1], 0.0)
    depth = q((p[0]*normal[0]+p[1]*normal[1] for p in cp), 0.98)-q((p[0]*normal[0]+p[1]*normal[1] for p in cp), 0.02)
    pull = depth*1.10
    horizontal = quat_columns(axis, (0,0,1), (-normal[0],-normal[1],0))
    report["geometry"] = {"handle":h,"axis":axis,"normal":normal,"cabinet_depth":depth,"layer_height":layer_height,"pull":pull}
    open_gripper()
    move("high approach", shifted(h, normal, 0.18, 0.24), downward, 200)
    move("high wrist rotation", shifted(h, normal, 0.18, 0.24), horizontal, 180)
    move("handle standoff", shifted(h, normal, 0.12, 0.04), horizontal)
    move("handle alignment", shifted(h, normal, 0.055), horizontal)
    move("handle contact", shifted(h, normal, -0.008), horizontal)
    close_gripper()
    for fraction in (0.33, 0.66, 1.0):
        move("drawer pull", shifted(h, normal, pull*fraction), horizontal, 110)
    open_gripper()
    move("handle retreat", shifted(h, normal, pull+0.09, 0.07), horizontal)
    move("clear cabinet", shifted(h, normal, pull+0.10, 0.16), downward)
    new_h = handles(cabinet_bottom, cabinet_top)[-1][0]
    opening = (new_h[0]-h[0])*normal[0] + (new_h[1]-h[1])*normal[1]
    report["opening"] = opening
    if opening < depth*0.55:
        raise ValueError("drawer opening not verified")
    bowl = locate(("grey bowl", "bowl"))
    points = bowl.point_cloud.points
    bc = center(points)
    bottom = q((p[2] for p in points), 0.05)
    grasps = generate_grasps("agentview", bowl.segmentation, backend="contact-graspnet", max_candidates=5)
    grasp = select_grasp(grasps, strategy="top_down") if grasps.ok else None
    if grasp is None:
        raise ValueError("no bowl grasp")
    gp = grasp.pose
    report["grasp"] = gp
    move("bowl pregrasp", (gp.position[0],gp.position[1],gp.position[2]+0.12), gp.quaternion_wxyz)
    move("bowl contact", gp.position, gp.quaternion_wxyz)
    close_gripper()
    lift_z = max(cabinet_top+0.15, gp.position[2]+0.20)
    move("bowl lift", (gp.position[0],gp.position[1],lift_z), gp.quaternion_wxyz)
    held = locate(("grey bowl", "bowl"))
    held_bottom = q((p[2] for p in held.point_cloud.points), 0.05)
    held_center = center(held.point_cloud.points)
    report["lift_delta"] = held_center[2]-initial_bowl[2]
    if held_center[2]-initial_bowl[2] < 0.04:
        raise ValueError("bowl lift not verified")
    eef = get_robot_state().end_effector_poses["primary"]
    offset = tuple(float(eef.position[a])-held_center[a] for a in range(3))
    bottom_offset = float(eef.position[2])-held_bottom
    target = shifted(h, normal, opening*0.50)
    target_floor = h[2]-layer_height*0.40
    target_eef = (target[0]+offset[0], target[1]+offset[1], target_floor+bottom_offset+0.012)
    report["placement"] = {"target":target,"floor":target_floor,"eef":target_eef,"held_offset":offset}
    move("bowl transit", (target_eef[0],target_eef[1],lift_z), gp.quaternion_wxyz, 200)
    move("bowl lower", target_eef, gp.quaternion_wxyz, 180)
    open_gripper()
    move("release retreat", (target_eef[0],target_eef[1],lift_z), gp.quaternion_wxyz, 160)
    state = get_robot_state()
    for tick in range(20):
        step(RobotAction(arms={"primary":ArmCommand("joint_position",state.joint_positions["primary"],gripper_position=1.0)}))
    report["completed"] = True

state = get_robot_state()
frame = state.base_frame
downward = tuple(state.end_effector_poses["primary"].quaternion_wxyz)
report = {"task":get_task_context().language,"motions":[],"completed":False}
try:
    execute()
except Exception as error:
    report["error"] = str(error)
result = report


