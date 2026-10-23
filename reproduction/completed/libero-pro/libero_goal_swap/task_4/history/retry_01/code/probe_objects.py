PROMPTS = (
    "grey bowl",
    "silver bowl",
    "bowl",
    "black cabinet",
    "drawer cabinet",
    "cabinet",
    "drawer",
)

context = get_task_context()
state = get_robot_state()
observation = get_observation()
report = {
    "task_language": context.language,
    "base_frame": state.base_frame,
    "prompts": [],
}

for prompt in PROMPTS:
    entry = {"prompt": prompt, "ok": False, "num_masks": 0, "scores": [], "boxes": []}
    segmented = segment_text("agentview", prompt)
    if segmented.ok:
        entry["ok"] = True
        entry["num_masks"] = len(segmented.segmentations)
        for candidate in segmented.segmentations[:5]:
            entry["scores"].append(float(candidate.score))
            if candidate.box_xyxy is not None:
                entry["boxes"].append([float(value) for value in candidate.box_xyxy])
    report["prompts"].append(entry)

open_gripper()
result = report
