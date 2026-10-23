context = get_task_context()
observation = get_observation()
state = get_robot_state()
picked = localize_object("red cube", camera_name="agentview", target_frame=state.base_frame)
result = {"task_language": context.language, "base_frame": state.base_frame, "initial_pose": state.end_effector_poses["primary"], "localization_ok": picked.ok, "point_count": len(picked.point_cloud.points) if picked.ok else 0}
