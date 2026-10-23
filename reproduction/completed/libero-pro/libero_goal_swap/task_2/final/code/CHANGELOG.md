Probe: `probe_geometry.py` — observation-only SAM3 prompt and public depth inspection on seed51.
v00 — initial side-grasp pick and cabinet-top placement from seed51 public geometry.
v00 pilot51: 0/1; grasp generation returned one candidate off bottle body. No motion executed.
v01 — replace failed generated grasp with geometry-derived side grasp; stage above its approach point.
v01 pilot51: 0/1; horizontal tool reorientation timed out after 159 ticks before contact.
v02 — preserve observed downward tool orientation; reach bottle body vertically from above.
v02 pilot51: 0/1; pre-grasp converged in 57 ticks, bottle-body descent stalled near bottle neck at z≈0.11 m.
v03 — close around upper bottle neck (observed 80% height), avoiding forced descent through the body.
v03 pilot51: task_success=true at release (345 ticks), but program_ok=false because open_gripper returned `terminated` and the source raised afterward.
v04 — treat public terminal flag during release as graceful completion and skip further settle commands.
v04 development 51–65: 15/15 task_success, 15/15 program_ok, 335–355 ticks; non-privileged provenance audit PASS.
SELECTED: v04 — 15/15 development seeds. fix_code.py is a byte-identical copy; frozen before unseen 66–80.
v04 exact-once unseen 66–80: 15/15 task_success, 15/15 program_ok; no code change or second unseen request.
