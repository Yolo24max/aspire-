from pathlib import Path
p=Path(__file__).resolve().parent/'finalize_reports.py'
s=p.read_text(encoding='utf-8-sig')
a=s.index("findings=f'''")
b=s.index("(base/'findings.md').write_text",a)
replacement="""findings=f'''# Findings: libero-pro/libero_goal_swap/task_1

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

{dev['successes']}/15 development successes and {unseen['successes']}/15 unseen successes, with {dev['program_ok']}/15 and {unseen['program_ok']}/15 program_ok respectively. Selected v08 was frozen before one unseen request covering seeds 66–80 and was never tuned afterward. Heldout seeds 1–50 were not accessed; they remain coordinator-owned.

{analysis}

## Generalizable patterns

none submitted as a new standalone control recipe. The skill report proposes a measured qualification of the library's unqualified backend preference, without introducing an untested selector or controller.

## Skill report

Canonical library hash at consultation: 4f6964b8ab59e95a. Consulted 24 sections: {counts['useful']} useful, {counts['misleading']} misleading, {counts['wrong']} wrong and {counts['not-applicable']} not-applicable. The settling recipe was incompletely applied by my adaptation; the library recipe itself is not blamed.

{skill_lines}

## Blocked modes

- Development seed 65 support-border placement; exact cause remains unproven.
- Rejected dedicated settling calls: own adaptation defect, zero executed loop ticks. Retraction still advances time. A repair belongs in a later independently authorized attempt with a valid evaluation protocol.
- Unseen residual regimes are documented above for reporting only; they did not drive tuning.

## Non-privileged API audit

PASS for access/provenance compliance. Math is the only policy import. All task geometry comes from documented public observations, perception and robot state. No native assets, simulator state, reward/evaluator access, other-task directories or heldout seeds were used. All fifteen selected-source development and fifteen unseen artifact programs match the frozen source after newline normalization. fix_code.py is a byte-identical copy of the tested frozen source, SHA256: {sha}.

This audit does not imply every public command was accepted: the settling limitation remains explicit. Evidence includes api_audit_v08.json, constant_audit_v08.md, settling_audit.json, selected_candidate.json, coverage_inventory.json and the absolute video_index.json. The worker promoted no proposals.
'''
"""
p.write_text(s[:a]+replacement+s[b:],encoding='utf-8')
print('Final findings template polished; policy unchanged')
