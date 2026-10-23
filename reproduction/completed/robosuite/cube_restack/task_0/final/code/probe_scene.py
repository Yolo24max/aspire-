context = get_task_context()
obs = get_observation()
state = get_robot_state()
probes = {}
for prompt in ("red cube", "green cube", "blue cube", "cube", "table"):
    found = localize_object(prompt, camera_name="agentview", target_frame=state.base_frame)
    probes[prompt] = found
result = {"task_language": context.language, "context": context, "cameras": list(obs.cameras), "state": state, "probes": probes}
