import hashlib,json,sys
from pathlib import Path
base=Path(__file__).resolve().parent
root=(base/sys.argv[1]).resolve()
assert root.is_relative_to(base/'debug')
policy=base/'code'/sys.argv[2]
rows=[]
for file in sorted(root.rglob('outcome.json')):
    o=json.loads(file.read_text()); run=file.parent
    p=json.loads((run/'source'/'program-result.json').read_text())
    rows.append({'seed':int(run.parent.name),'program_ok':o['program_ok'],'task_success':o['task_success'],'steps':o['steps_executed'],'reason':o['termination_reason'],'error':o.get('error'),'result':p.get('result'),'run_dir':str(run),'videos':[str(v) for v in sorted((run/'media'/'videos').glob('*.mp4'))]})
summary={'program':str(policy),'source_hash':hashlib.sha256(policy.read_bytes()).hexdigest(),'output_root':str(root),'seeds':[r['seed'] for r in rows],'successes':sum(r['task_success'] for r in rows),'program_ok':sum(r['program_ok'] for r in rows),'total':len(rows),'rows':rows}
(base/sys.argv[3]).write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('score',summary['successes'],'/',summary['total'],'program_ok',summary['program_ok'],'source',summary['source_hash'])
for r in rows:
    print(r['seed'],r['program_ok'],r['task_success'],r['steps'],r['reason'],str(r['error']))
    if not r['task_success']: print('result',json.dumps(r['result']),'run',r['run_dir'])
