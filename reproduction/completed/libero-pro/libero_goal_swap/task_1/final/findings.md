# Findings: libero-pro/libero_goal_swap/task_1

## Root causes observed

- Infrastructure failures before movement: v00 Contact-GraspNet OOM and the first v01 SAM3 OOM, both on seed 51. These were excluded from the eight valid policy versions; the coordinator repaired services.
- Joint execution on seed 51: direct descent and Cartesian staging stopped before convergence. Large wrist rotation also stalled. Bounded public joint increments completed the approach in v05 onward.
- Grasp and transport near the rack on seed 51: the side rim approach stopped near the rack. A front rim grasp with staged yaw lifted the bowl. An earlier release left the bowl on the rack; higher transit and measured held-object geometry solved this scene in v07. Their individual contributions were not isolated.
- Generated-grasp path failures cost development seeds 54, 57 and 60 in v07. Seeds 54/60 closed and lifted empty; 57 stalled on approach. All three selected generated grasps failed, while the eleven successes used the geometry rim fallback.
- Placement recovery is a heuristic: after any exception in the lower move, release is allowed only when measured XY error is <=25 mm. It does not check vertical error or sense physical contact. The separate +25 mm is the release target Z offset. The lower_contact_blocked flag is a report label, not a contact witness.
- Development seed 65 repeats a support-border placement in v07/v08: motion guards pass and the bowl is visibly near the stove front/side edge with partial overhang, yet task_success=false. Exact causal roles of support contact, tilt or settling are unproven; no hidden predicate was inspected.
- Own adaptation defect: I omitted ArmCommand.embodiment=state.embodiment from the intended settling calls. The complete transport.md recipe correctly includes it and warns about the robosuite default. All 225 intended dedicated settling calls in selected development runs returned invalid_request and advanced zero ticks. Accepted motions, including retraction, still advanced physics. Program_ok does not prove these step calls succeeded. The defect was audited after source freeze; frozen bytes remain unchanged.

## What fixed them

- v01 through v06 are seed 51 gate/debug trials, not full development rates. v07 was the first clean seed 51 success at 698 ticks, then measured 11/15 task successes and 12/15 program_ok on the full development sweep.
- v08 changes only grasp choice: it removes generated grasps and always uses the already-tested runtime rim path. It flips 54/57/60 with no regressions, measuring 14/15 task successes and 15/15 program_ok. Placement was unchanged in this ablation.
- v00 has no valid full-development baseline: its only trial was an infrastructure-invalid, zero-tick seed 51 episode. It must not be reported as 0/15.

## Development vs unseen

14/15 development successes and 13/15 unseen successes, with 15/15 and 15/15 program_ok respectively. Selected v08 was frozen before one unseen request covering seeds 66–80 and was never tuned afterward. Heldout seeds 1–50 were not accessed; they remain coordinator-owned.

## Unseen residual regime

The exact-once frozen measurement scored 13/15 task success and 15/15 program_ok, close to the development result of 14/15. Residual failures are support-border placements on seeds 66 and 69, matching the observed development seed 65 regime. All six reported pose stages passed; final images show the bowl near the stove front/side edge with partial overhang, while the benchmark task result remains false. No new grasp or approach failure was observed.

Neither failed unseen run used the catch-all lower fallback: their lower stage passed its measured guard, and no lower_contact_blocked flag was reported. The flag is only a heuristic after any lower exception and is not evidence of physical contact.

The dedicated settling calls were rejected by the public API and advanced zero ticks; accepted retraction motions still advanced physics. It is unproven whether support contact, tilt or additional settling would change these outcomes. No hidden predicate was inspected, and no source change, new policy request or rerun followed the unseen measurement. These results support a remaining placement-border regime rather than a predicted heldout success rate.


## Generalizable patterns

none submitted as a new standalone control recipe. The skill report proposes a measured qualification of the library's unqualified backend preference, without introducing an untested selector or controller.

## Skill report

Canonical library hash at consultation: 4f6964b8ab59e95a. Consulted 24 sections: 9 useful, 1 misleading, 0 wrong and 14 not-applicable. The settling recipe was incompletely applied by my adaptation; the library recipe itself is not blamed.

- task-exploration.md # Initial Scene Analysis: useful — Used mirrored public seed51 task language and scene. v07 clean success on51; scene hypotheses were revised from recorded evidence, not copied as executable coordinates.
- task-exploration.md # Triage from disk, not from a run: log line: useful — Read finalized outcome/source/trace/image files for every completed51 trial; distinguished provider OOM from manipulation failures.
- task-exploration.md # Wrap every run in timeout: not-applicable — Root-owned remote queue executes episodes; worker never launches simulator processes.
- task-exploration.md # Sandbox constraints when writing probes: useful — All valid51 policies use math only and documented builtins; no sandbox AST rejection occurred.
- localize.md # Standard Localization Helper: useful — Prompt fallback plus minimum-point guards correctly localized bowl and stove on51. v07 clean success; no isolated helper ablation.
- localize.md # Prompt Registry: not-applicable — The registry has no bowl/stove entry. Prompts came from current language and public scene evidence.
- localize.md # Disambiguation: Two Similar Objects in Scene: not-applicable — The inspected scene has one requested bowl; no multi-object candidate selector was used.
- localize.md # Key Signals: useful — Typed provider failures identified CGN and SAM3 OOM-only51 runs. Candidate ordering in typed JSON corrected an initial misreading of multi-box overlays.
- localize.md # Prompting Strategy: useful — Read authoritative runtime language and localized stove before grasp. grey bowl and stove selected correct masks on51; selected v07 succeeded.
- localize.md # Placement Z Notes: useful — Observed clouds represent visible surfaces. v07 measured held bowl relation rather than assuming initial center offset;51 succeeded, causal contributions not isolated.
- grasp.md # Standard Pick-and-Place Template: misleading — The unqualified preference for Contact-GraspNet on irregular objects sent this open bowl to generated top_down candidates. v07 selected them on54/57/60 and all3failed (empty grasp54/60, approach57). One-variable ablation v08 uses the already-tested runtime rim grasp and flips all3, improving11/15 to14/15 with no regressions; remaining65placement is unchanged.
- grasp.md # Cylindrical Side Grasp (bottles, cans): not-applicable — Requested object is an open bowl; used a rim grasp rather than cylindrical side grasp.
- grasp.md # Key Conventions: useful — close_gripper contact-stall completion preserved closed command during51 lift/transport. Public motion diagnostics were checked; no home call while holding.
- grasp.md # Object Geometry Utilities: useful — Computed bowl/target clearance and held geometry from public point-cloud quantiles. v07 passed51 and provenance audit.
- transport.md # Waypoint Sequences: not-applicable — The section is a structural placeholder; authored Cartesian and joint staging from measured execution failures.
- transport.md # Pre-Probe IK Conditioning: not-applicable — Observed IK solved requested poses; failures were execution/contact, so no before-grasp placement previsit was justified.
- transport.md # Safe Transit (Lateral Escape Before Lift): not-applicable — The section has no executable recipe, and the selected approach lifts vertically before lateral transport.
- transport.md # Placement Approach: not-applicable — No filled placement approach recipe exists in the section. Measured rack interception motivated runtime held offset and higher clearance.
- transport.md # Physics Settling After Release: not-applicable — Incomplete application, own adaptation defect: omitted embodiment=state.embodiment even though this section correctly includes it and warns default robosuite. All225 intended step calls in selected development runs returned invalid_request and advanced0ticks. The full recipe was not applied; no negative skill-efficacy attribution is justified.
- transport.md # Basket / Container Placement: not-applicable — Goal is a stove surface, not a container. Did not apply generic container release-height rule.
- manipulation.md # Knob / Switch Turning: not-applicable — Task language requests bowl placement; no knob/switch operation needed.
- manipulation.md # Hinged Door Opening / Closing: not-applicable — No requested articulated door action.
- manipulation.md # Pushing / Sliding: not-applicable — Selected policy grasps and transports the bowl; no push technique used.
- manipulation.md # General Notes: not-applicable — Articulated manipulation notes do not determine this bowl pick/place strategy.

## Blocked modes

- Development seed 65 support-border placement; exact cause remains unproven.
- Rejected dedicated settling calls: own adaptation defect, zero executed loop ticks. Retraction still advances time. A repair belongs in a later independently authorized attempt with a valid evaluation protocol.
- Unseen residual regimes are documented above for reporting only; they did not drive tuning.

## Non-privileged API audit

PASS for access/provenance compliance. Math is the only policy import. All task geometry comes from documented public observations, perception and robot state. No native assets, simulator state, reward/evaluator access, other-task directories or heldout seeds were used. All fifteen selected-source development and fifteen unseen artifact programs match the frozen source after newline normalization. fix_code.py is a byte-identical copy of the tested frozen source, SHA256: 6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226.

This audit does not imply every public command was accepted: the settling limitation remains explicit. Evidence includes api_audit_v08.json, constant_audit_v08.md, settling_audit.json, selected_candidate.json, coverage_inventory.json and the absolute video_index.json. The worker promoted no proposals.
