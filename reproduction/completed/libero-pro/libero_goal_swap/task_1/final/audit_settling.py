import json
from pathlib import Path
base=Path(__file__).resolve().parent
summary=json.loads((base/'v08_dev_summary.json').read_text())
rows=[]
for r in summary['rows']:
    run=Path(r['run_dir']); p=json.loads((run/'source'/'program-result.json').read_text())
    steps=[c for c in p['calls'] if c['tool']=='step']
    events=[json.loads(line) for line in (run/'trace'/'events.jsonl').read_text().splitlines()]
    times=[e['simulator_time_s'] for e in events if e.get('name')=='step']
    rows.append({'seed':r['seed'],'requested_step_calls':len(steps),'ok_step_calls':sum(c['ok'] for c in steps),'invalid_request_calls':sum(c.get('failure_code')=='invalid_request' for c in steps),'step_span_simulator_times':sorted(set(times)),'run_dir':str(run)})
report={'policy':'v08','source_sha256':'6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226','source_unchanged_after_freeze':True,'attribution':'Own adaptation omitted embodiment=state.embodiment from transport.md Physics Settling recipe, which correctly includes it and warns default robosuite. The abbreviated docs/api-reference.md constructor table was followed during adaptation; the complete skill recipe was not applied. No bad skill/example snippet was copied.','requested_step_calls':sum(r['requested_step_calls'] for r in rows),'ok_step_calls':sum(r['ok_step_calls'] for r in rows),'invalid_request_calls':sum(r['invalid_request_calls'] for r in rows),'actual_settling_ticks':0,'rows':rows}
assert report['requested_step_calls']==225 and report['invalid_request_calls']==225 and report['ok_step_calls']==0
assert all(len(r['step_span_simulator_times'])==1 for r in rows)
(base/'settling_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for name in ('constant_audit_v07.md','constant_audit_v08.md'):
    path=base/name
    text=path.read_text(encoding='utf-8-sig').replace('15 settling ticks','15 intended settling calls (typed invalid_request;0 executed settling ticks due own omitted embodiment)')
    path.write_text(text,encoding='utf-8')
draft=json.loads((base/'skill_report_draft.json').read_text(encoding='utf-8-sig'))
for entry in draft['consulted']:
    if entry['skill']=='transport.md' and entry['section']=='Physics Settling After Release':
        entry['verdict']='not-applicable'
        entry['evidence']='Incomplete application, own adaptation defect: omitted embodiment=state.embodiment even though this section correctly includes it and warns default robosuite. All225 intended step calls in selected development runs returned invalid_request and advanced0ticks. The full recipe was not applied; no negative skill-efficacy attribution is justified.'
    if entry['skill']=='grasp.md' and entry['section']=='Standard Pick-and-Place Template':
        entry['verdict']='misleading'
        entry['evidence']='The unqualified preference for Contact-GraspNet on irregular objects sent this open bowl to generated top_down candidates. v07 selected them on54/57/60 and all3failed (empty grasp54/60, approach57). One-variable ablation v08 uses the already-tested runtime rim grasp and flips all3, improving11/15 to14/15 with no regressions; remaining65placement is unchanged.'
draft['proposed_edits']=[{'skill':'grasp.md','section':'Standard Pick-and-Place Template','change':'Replace the unqualified preferred-for-irregular-objects backend comment with a conditional choice and a measured application record: returned top_down candidates remain contact hypotheses and require observed object-lift verification; public-geometry alternatives can outperform them on open bowls. Record task1 v07 generated-grasp0/3 versus v08 geometry-rim14/15 as task-specific evidence, without a universal backend ranking or an untested selection threshold.','why':'All3 generated-grasp selections in v07 failed54/57/60; forcing the existing manual rim path in v08 flipped those3 and preserved the other outcomes,11/15 to14/15. This edit qualifies guidance; it does not propose a new untested controller or geometry rule.'}]
(base/'skill_report_draft.json').write_text(json.dumps(draft,indent=2),encoding='utf-8')
with (base/'code'/'CHANGELOG.md').open('a',encoding='utf-8') as f:
    f.write('\nPost-freeze operational audit:225/225 intended settling step calls acrossv08dev returned invalid_request, because my adaptation omitted ArmCommand.embodiment=state.embodiment. They advanced0ticks; the complete transport skill recipe correctly includes this field and was not applied. Frozen source/unseen request unchanged. Residual65shows support-border placement; settling as a cause is unproven.\n')
print('Settling audit:',report['invalid_request_calls'],'rejected calls,0ticks; reports corrected; policy unchanged')
