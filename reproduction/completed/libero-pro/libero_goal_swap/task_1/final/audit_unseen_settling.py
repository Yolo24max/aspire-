import json
from pathlib import Path
base=Path(__file__).resolve().parent
s=json.loads((base/'unseen_summary.json').read_text())
rows=[]
for r in s['rows']:
    run=Path(r['run_dir']); p=json.loads((run/'source'/'program-result.json').read_text()); calls=[c for c in p['calls'] if c['tool']=='step']
    events=[json.loads(l) for l in (run/'trace'/'events.jsonl').read_text().splitlines()]
    times=sorted({e['simulator_time_s'] for e in events if e.get('name')=='step'})
    rows.append({'seed':r['seed'],'calls':len(calls),'ok':sum(c['ok'] for c in calls),'invalid_request':sum(c.get('failure_code')=='invalid_request' for c in calls),'step_span_times':times})
assert sum(r['calls'] for r in rows)==225 and sum(r['invalid_request'] for r in rows)==225 and all(len(r['step_span_times'])==1 for r in rows)
(base/'settling_audit_unseen.json').write_text(json.dumps({'policy':'frozen v08','requested_calls':225,'accepted_calls':0,'invalid_request_calls':225,'dedicated_settling_ticks':0,'source_change_after_unseen':False,'rows':rows},indent=2),encoding='utf-8')
print('Unseen225 intended settling calls rejected;0dedicated ticks; source unchanged')
