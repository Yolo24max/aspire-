def quantile(values, fraction):
    ordered = sorted(float(v) for v in values)
    return ordered[int((len(ordered)-1)*fraction)]

def locate(prompt):
    found = localize_object(prompt, camera_name="agentview", target_frame=frame)
    if not found.ok or len(found.point_cloud.points)<20:
        raise ValueError("cube not localized: " + prompt)
    pts = found.point_cloud.points
    x = quantile((p[0] for p in pts),0.5)
    y = quantile((p[1] for p in pts),0.5)
    top = quantile((p[2] for p in pts),0.9)
    width = min(quantile((p[0] for p in pts),0.9)-quantile((p[0] for p in pts),0.1),quantile((p[1] for p in pts),0.9)-quantile((p[1] for p in pts),0.1))
    if width <= 0:
        raise ValueError("invalid cube width")
    return {"prompt":prompt,"x":x,"y":y,"top":top,"bottom":quantile((p[2] for p in pts),0.05),"width":width}

def move(pos, stage, cap=160):
    motion=move_to_pose(Pose(pos,downward,frame),tolerance=0.015,max_steps=cap)
    report["motions"].append({"stage":stage,"motion":motion})
    if not motion.ok:
        raise ValueError(stage + " failed")

def transfer(cube, tx, ty, surface):
    x,y,w=cube["x"],cube["y"],cube["width"]
    gz=cube["top"]-0.65*w
    if not open_gripper().ok:
        raise ValueError("open failed")
    move((x,y,gz+0.15),"pregrasp",220)
    move((x,y,gz),"grasp",180)
    if not close_gripper().ok:
        raise ValueError("close failed")
    liftz=max(gz+0.15,surface+w+0.12)
    move((x,y,liftz),"lift",180)
    after=locate(cube["prompt"])
    report["grasp_checks"].append(after["top"]-cube["top"])
    if after["top"]-cube["top"]<0.02:
        raise ValueError("lift not verified")
    held_pose=get_robot_state().end_effector_poses["primary"].position
    clearance=float(held_pose[2])-after["bottom"]
    dx=float(held_pose[0])-after["x"]
    dy=float(held_pose[1])-after["y"]
    tx,ty=tx+dx,ty+dy
    report["held_clearances"].append(clearance)
    move((tx,ty,liftz),"transport",180)
    move((tx,ty,surface+clearance+0.012),"lower",180)
    if not open_gripper().ok:
        raise ValueError("release failed")
    move((tx,ty,liftz),"retreat",160)

state=get_robot_state()
frame=state.base_frame
downward=tuple(state.end_effector_poses["primary"].quaternion_wxyz)
report={"task":get_task_context().language,"motions":[],"grasp_checks":[],"held_clearances":[]}
result=report
red=locate("red cube")
green=locate("green cube")
upper,lower=(red,green) if red["top"]>green["top"] else (green,red)
report["initial"]=[upper,lower]
table=localize_object("table",camera_name="agentview",target_frame=frame)
if not table.ok:
    raise ValueError("table unavailable")
surface=quantile((p[2] for p in table.point_cloud.points),0.95)
# Adjacent table location, derived from the stack and measured cube span.
tx=lower["x"]
ty=lower["y"]-3.0*max(upper["width"],lower["width"])
transfer(upper,tx,ty,surface)
upper_now=locate(upper["prompt"])
lower_now=locate(lower["prompt"])
transfer(lower_now,upper_now["x"],upper_now["y"],upper_now["top"])
state=get_robot_state()
for tick in range(12):
    step(RobotAction(arms={"primary":ArmCommand("joint_position",state.joint_positions["primary"],gripper_position=1.0)}))
report["completed"]=True

