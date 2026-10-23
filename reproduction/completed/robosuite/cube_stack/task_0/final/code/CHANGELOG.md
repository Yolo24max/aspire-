v00 — initial program from scene analysis; mode: stable stacking placement

v00 scored 22/25 development; 23/25 program_ok. Modes: adjacent-cube interference 103,108 (grasp descent blocked at ~0.031m error); target displacement suspected113 (final red and green separated). Public keyframes show an open finger contacting the green neighbor during red approach.
v01 -- adjacent-cube interference: rotate observed tool about base Z to put jaw-opening direction perpendicular to runtime red-to-green vector. No fixed poses, dimensions, pixels, seed branches or privileged data.

v01 scored15/25 development,15/25 program_ok; regressions109,110,114,118,119,123,124. Modes: initial rotated pregrasp execution timeout103,108,109,110,113,114,118,119,123,124. Public103 trace shows first pregrasp timeout146 ticks,0.247m error; keyframe shows partial wrist rotation with empty jaws still above scene. Not a perception/provider failure.
v02 -- adjacent-cube interference (third and final source for this mode, conservatively counting v00): preserve perception-derived rotation but bound repeated pose replanning/servo at3 calls after typed timeout. No retry for planner errors, no simulator harness retries. Full policy stays1000 ticks maximum.

v02 scored25/25 development,25/25 program_ok,409-533 ticks. Flipped original failures103,108,113 and all v01 regressions; no development regression. Conservative adjacent-interference allocation consumed3/3 including v00; mode resolved.
SELECTED: v02 --25/25 development. API provenance audit PASS; freeze_manifest.json records SHA and library SHA before unseen. fix_code.py is an exact byte copy. No unseen evidence used in selection.

UNSEEN: frozen v02 passed5/5 task and5/5 program on126-130 exactly once;419-634 ticks. No code changes after freeze. Stage1 complete; Stage2/heldout/verifier/promotion remain root-owned.
