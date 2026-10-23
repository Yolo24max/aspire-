import json
from pathlib import Path

task=Path(__file__).resolve().parent
status=json.loads((task/'coordinator_status.json').read_text(encoding='utf-8-sig'))
if status['phase']!='artifacts_ready':
    print(json.dumps({'phase':status['phase'],'program':status.get('program')}))
else:
    root=Path(status['output_root'])
    rows=[]
    for file in sorted(root.rglob('outcome.json')):
        outcome=json.loads(file.read_text())
        run=file.parent
        result=json.loads((run/'source'/'program-result.json').read_text())
        row={'seed':int(run.parent.name),'program_ok':outcome['program_ok'],'task_success':outcome['task_success'],'steps':outcome['steps_executed'],'reason':outcome['termination_reason'],'error':outcome.get('error'),'result':result.get('result'),'run_dir':str(run),'videos':[str(p) for p in sorted((run/'media'/'videos').glob('*.mp4'))]}
        rows.append(row)
    summary={'program':status['program'],'source_hash':status['source_hash'],'seeds':[r['seed'] for r in rows],'successes':sum(r['task_success'] for r in rows),'program_ok':sum(r['program_ok'] for r in rows),'total':len(rows),'rows':rows}
    (task/'latest_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('program',summary['program'],'score',summary['successes'],'/',len(rows),'program_ok',summary['program_ok'])
    for row in rows:
        print(row['seed'],row['program_ok'],row['task_success'],row['steps'],row['reason'],str(row['error']))
        if not row['task_success']:
            print('result',json.dumps(row['result']),'run',row['run_dir'])
