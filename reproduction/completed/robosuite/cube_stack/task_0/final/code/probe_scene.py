state = get_robot_state()
observation = get_observation()
report = {"language": get_task_context().language, "cameras": list(observation.cameras), "state": state, "metadata": robosuite.get_task_metadata(), "controller": robosuite.get_controller_metadata(), "objects": {}}
for prompt in ("red cube", "green cube", "blue cube", "cube"):
    found = localize_object(prompt, camera_name="agentview", target_frame=state.base_frame)
    report["objects"][prompt] = found
result = report
