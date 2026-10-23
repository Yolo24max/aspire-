# retry_03 changelog
v00_geometry_rim: independent public-API geometry-derived rim pinch, bounded joint staging, held-bowl verification, and drawer-top placement. Seed 51 only. No private APIs, fixed snapshot poses, unseen or heldout seeds.
v01_terminal_release: one-variable repair; stop after the release action because v00 reached task_success before its retract motion, which caused program_ok=false. No post-success motion or new API.
