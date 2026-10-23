# Findings: robosuite/cube_restack/task_0

## Root causes observed
- v00 failed all25 development seeds101–125 at the first placement lower. Horizontal cube span was insufficient to estimate retained-cube bottom clearance. Public lower results timed out; seed101 showed the retained red cube contacting the table before the EEF reached its requested target.
- The initial full25 request met an infrastructure gate conflict. Root repaired the clean-pilot-only gate and reused the exact failed101 episode; no scientific replay, source change, reset or budget exception occurred.

## What fixed them
v01 measures post-lift EEF position minus held cube cloud bottom, and the held XY relation, then derives each release target from the current support surface. It changed full development from0/25 to25/25 with25/25 program success. All episodes used728–792ticks. The own101 final keyframe visibly shows green on red with the tool withdrawn. No component ablation was performed.

## Development vs unseen
25/25 development101–125 and5/5 exact-once unseen126–130, all program_ok. The selected source was frozen before unseen and was never changed afterwards. Evidence supports generalization across these assigned scenes; no broader transfer claim is made.

## Generalizable patterns
No new library entry proposed. The existing segmented-fixture placement pattern already describes deriving clearance from measured held geometry; this task transfers that principle to reversing a two-cube stack. The cube-width grasp-depth skill supplied successful initial grasp/lift, but does not claim a width-based placement formula. Both source histories remain available.

## Skill report
- localize.md §Standard Localization Helper: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- localize.md §Prompt Registry: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- localize.md §Disambiguation: Two Similar Objects in Scene: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- localize.md §Key Signals: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- localize.md §Prompting Strategy: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- localize.md §Placement Z Notes: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- transport.md §Waypoint Sequences: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- transport.md §Bounded public pose convergence after a rotated pregrasp timeout: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- transport.md §Pre-Probe IK Conditioning: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- transport.md §Safe Transit (Lateral Escape Before Lift): not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- transport.md §Placement Approach: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- transport.md §Segmented Fixture Top Placement: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- transport.md §Physics Settling After Release: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- transport.md §Basket / Container Placement: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- README.md §How an entry gets here: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- grasp.md §Standard Pick-and-Place Template: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- grasp.md §Cylindrical Side Grasp (bottles, cans): not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- grasp.md §Downward Bottle Neck Grasp: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- grasp.md §Key Conventions: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- grasp.md §Visible cube width-relative grasp depth: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- grasp.md §Object Geometry Utilities: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- manipulation.md §Knob / Switch Turning: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- manipulation.md §Hinged Door Opening / Closing: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- manipulation.md §Pushing / Sliding: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- manipulation.md §General Notes: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- task-exploration.md §Triage from disk, not from a `run:` log line: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- task-exploration.md §Wrap every run in `timeout` — orphans starve the GPU: not-applicable — Read before initial scene; skipped because this task is two simple cubes and this section does not supply its needed operation.
- task-exploration.md §Sandbox constraints when writing probes: useful — Applied public perception, staged control, or artifact triage to own cube_restack v00/v01. v00 full development0/25 failed placement; v01 full development101-125 passed25/25 at728-792ticks. Whole-policy evidence only, no isolated ablation.
- task-exploration.md §Initial Scene Analysis: useful — Own single no-motion scene101 supplied authoritative reversal language and red/green overlays; runtime role ordering uses public heights. Scene count1 preserved.
- README.md §Shared Robot Skills: useful — Only curated library used as cross-task knowledge; no other task or verifier workspace read. Library SHA139b0f21899063b4 confirmed by official campaign command.

## Blocked modes
None.

## Non-privileged API audit
PASS. Exact selected source/fix_code SHA256:eac7ad8656fe85fafc83b286026c537eab1a6b4c2db856d1ebdc815842619742. Public robot state and runtime point-cloud quantiles determine every task-dependent pose, dimension, role and placement relation. No simulator internals, assets, raw success predicates, cached coordinates, seed branches, cross-task evidence, external baseline, paid APIs or model switch used. Root owns simulation infrastructure and heldout1–100. All writes remained inside this task directory.
