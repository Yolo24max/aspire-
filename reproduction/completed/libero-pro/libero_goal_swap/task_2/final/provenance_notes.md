# Task 2 provenance and version record

- Benchmark: `libero-pro/libero_goal_swap/task_2`, `seeded`, max 1000 steps, GPU0 serial through the coordinator. Videos requested at 800×512. The worker launched no simulator or SSH process.
- Stage 0 source: this task's seed51 scene snapshot, public RGB keyframe, public SAM3/point-cloud probe, the documented generated-program API, and the shared canonical skill library. Runtime language was `Put the wine bottle on the top of the drawer`; the different task name was not used as authority.
- Prohibited sources were not read: no real-robot files/instructions, native simulation assets, task2 public examples, reference-prep-task2, sibling task-specific sources, or held-out seeds 1–50.
- `v00_initial.py`: seed51 pilot 0/1; Contact-GraspNet candidate missed the bottle. Invalidated for selection; preserved.
- `v01_manual_side.py`: seed51 pilot 0/1; horizontal tool reorientation timed out at 159 ticks. Invalidated for selection; preserved.
- `v02_vertical_tool.py`: seed51 pilot 0/1; approach succeeded, bottle-midpoint descent stalled after contact. Invalidated for selection; preserved.
- `v03_neck_grasp.py`: seed51 `task_success=true`, `program_ok=false`; release returned public `terminated` after task success and the source raised. Invalidated for selection; preserved.
- `v04_terminal_release.py`: seed51 pilot `task_success=true`, `program_ok=true`; development 51–65 scored 15/15 on both fields. Selected and frozen as byte-identical `fix_code.py` before unseen.
- Source SHA256: `3629cae5274b16d6dbc704540d35c014084e29decb8fcc9eb5410fb5d190e78f`. Coordinator reported this same source hash for development and exact-once unseen 66–80. Unseen scored 15/15 success and 15/15 program OK. The first unseen request pointed outside `code/` and was rejected before launching any episode; the corrected request ran the frozen `code/v04_terminal_release.py` once.
- Public program-source audit: no imports, filesystem/network, reward, native environment, simulator state, seed branching, fixed world object poses, or copied task2 program. Position and height values derive from runtime localization/point-cloud quantiles. Relative margins and motion caps are generic tunable parameters. The observed initial end-effector orientation supplies the grasp orientation.
- There were no policy edits or further episode requests after unseen. Held-out seeds 1–50 remain exclusively with the coordinator.
