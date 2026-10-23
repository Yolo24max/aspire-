import hashlib,json,shutil
from collections import Counter
from pathlib import Path

base=Path(__file__).resolve().parent
selection=json.loads((base/'selected_candidate.json').read_text())
dev=json.loads((base/'v08_dev_summary.json').read_text())
unseen=json.loads((base/'unseen_summary.json').read_text())
analysis=(base/'unseen_failure_analysis.md').read_text(encoding='utf-8-sig')
source=Path(selection['program_local']); source_bytes=source.read_bytes()
sha=hashlib.sha256(source_bytes).hexdigest()
assert sha==selection['source_sha256']=='6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226'
assert dev['seeds']==list(range(51,66)) and dev['total']==15
assert unseen['seeds']==list(range(66,81)) and unseen['total']==15
assert dev['source_hash']==unseen['source_hash']==sha
assert json.loads((base/'api_audit_v08.json').read_text())['automated_audit_pass']
req=json.loads((base/'requested_runs.json').read_text())
assert req==json.loads((base/'unseen_request_once.json').read_text())
assert req['seeds']==list(range(66,81)) and req['program']==selection['program_server']
for row in dev['rows']+unseen['rows']:
    recorded=(Path(row['run_dir'])/'source'/'program.py').read_text()
    assert recorded.replace('\r\n','\n').strip()==source.read_text(encoding='utf-8-sig').replace('\r\n','\n').strip()

server='/mnt/aspire-work/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_1'
policies=[]; lookup={}
for p in sorted((base/'code').glob('v*.py')):
    normalized=hashlib.sha256(p.read_text(encoding='utf-8-sig').replace('\r\n','\n').strip().encode()).hexdigest()
    record={'program':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'normalized_sha256':normalized,'runs':[]}
    policies.append(record); lookup[normalized]=record
videos=[]
for outcome in sorted((base/'debug').rglob('outcome.json')):
    run=outcome.parent; seed=int(run.parent.name); assert seed>=51
    o=json.loads(outcome.read_text()); program=run/'source'/'program.py'
    normalized=hashlib.sha256(program.read_text(encoding='utf-8-sig').replace('\r\n','\n').strip().encode()).hexdigest()
    status='infrastructure-invalid' if ('v00_seed51' in str(run) or ('v01_seed51' in str(run) and 'repaired' not in str(run))) else 'measured'
    row={'seed':seed,'run_dir':str(run),'classification':status,'program_ok':o['program_ok'],'task_success':o['task_success'],'steps':o['steps_executed'],'recorded_source_sha256':hashlib.sha256(program.read_bytes()).hexdigest()}
    if normalized in lookup: lookup[normalized]['runs'].append(row)
    for video in sorted((run/'media'/'videos').glob('*.mp4')):
        relative=video.relative_to(base).as_posix()
        videos.append({'seed':seed,'run_dir':str(run),'local_video':str(video),'server_original_video':server+'/'+relative,'video_index':str(run/'media'/'video-index.json'),'program_ok':o['program_ok'],'task_success':o['task_success']})
coverage={'schema_version':1,'selected_source_sha256':sha,'selected_source_development_seeds':dev['seeds'],'selected_source_unseen_seeds':unseen['seeds'],'selected_source_development_successes':dev['successes'],'selected_source_unseen_successes':unseen['successes'],'selected_source_development_program_ok':dev['program_ok'],'selected_source_unseen_program_ok':unseen['program_ok'],'unseen_worker_request_count':1,'later_worker_policy_requests':0,'heldout_requested_by_worker':False,'valid_policy_versions':8,'infrastructure_invalid_notes':'v00 CGN OOM and firstv01 SAM3 OOM excluded; exactv01 repaired retry is valid. Root journal audit is separate.','policies':policies}
(base/'coverage_inventory.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
(base/'video_index.json').write_text(json.dumps({'schema_version':1,'videos':videos},indent=2),encoding='utf-8')

skill=json.loads((base/'skill_report_draft.json').read_text(encoding='utf-8-sig'))
(base/'skill_report.json').write_text(json.dumps(skill,indent=2),encoding='utf-8')
counts=Counter(e['verdict'] for e in skill['consulted'])
skill_lines='\n'.join('- '+e['skill']+' # '+e['section']+': '+e['verdict']+' — '+e['evidence'] for e in skill['consulted'])
findings=f'''# Findings: libero-pro/libero_goal_swap/task_1

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
(base/'findings.md').write_text(findings,encoding='utf-8')
shutil.copyfile(source,base/'fix_code.py')
assert hashlib.sha256((base/'fix_code.py').read_bytes()).hexdigest()==sha
with (base/'code'/'CHANGELOG.md').open('a',encoding='utf-8') as f:
    f.write(f'\nFrozenv08 unseen exactly once:{unseen["successes"]}/15task,{unseen["program_ok"]}/15program. No tuning afterward. Full coverage and non-privileged auditPASS; fix_code.py copied byte-identically from frozenv08. Known rejected settling limitation preserved.\n')
print(json.dumps({'development':dev['successes'],'unseen':unseen['successes'],'program_ok_dev':dev['program_ok'],'program_ok_unseen':unseen['program_ok'],'sha':sha,'skill_counts':dict(counts),'proposals_new':len(skill['proposed_new']),'proposals_edit':len(skill['proposed_edits']),'video_count':len(videos)},indent=2))


