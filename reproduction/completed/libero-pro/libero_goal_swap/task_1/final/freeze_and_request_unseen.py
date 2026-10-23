import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
base=Path(__file__).resolve().parent
v7=json.loads((base/'v07_dev_summary.json').read_text())
v8=json.loads((base/'v08_dev_summary.json').read_text())
assert v8['seeds']==list(range(51,66)) and v8['total']==15 and v8['successes']==14 and v8['program_ok']==15
source=base/'code'/'v08_geometry_rim_only.py'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert sha=='6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226'
assert json.loads((base/'api_audit_v08.json').read_text())['automated_audit_pass']
for row in v8['rows']:
    exact=(Path(row['run_dir'])/'source'/'program.py').read_text()
    assert exact.replace('\r\n','\n').strip()==source.read_text(encoding='utf-8-sig').replace('\r\n','\n').strip()
server='/mnt/aspire-work/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_1'
selection={'schema_version':1,'frozen_utc':datetime.now(timezone.utc).isoformat(),'selected_version':'v08','program_local':str(source),'program_server':server+'/code/v08_geometry_rim_only.py','source_sha256':sha,'development_seeds':list(range(51,66)),'development_successes':14,'development_program_ok':15,'development_summary':str(base/'v08_dev_summary.json'),'selection_rule':'Highest full-development task success (v08 14/15 vs v07 11/15), then program_ok; no assembled untested program.','api_audit':'PASS','audit_paths':[str(base/'api_audit_v08.json'),str(base/'constant_audit_v08.md')],'unseen_seeds':list(range(66,81)),'unseen_protocol':'Exactly one measurement after this freeze; no tuning or later worker policy requests.','skill_library_sha':'4f6964b8ab59e95a'}
(base/'selected_candidate.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
program=selection['program_server']; out=server+'/debug/holdout/v08_unseen'; log=server+'/debug/logs/v08_unseen'
command=f'CUDA_VISIBLE_DEVICES=0 MUJOCO_EGL_DEVICE_ID=0 .venv-libero/bin/cap-harness run-batch --benchmark libero-pro --suite libero_goal_swap --task-id 1 --seeds 66-80 --program {program} --output-root {out} --flat-run-dir --init-mode seeded --workers 1 --max-steps 1000 --log-dir {log} --results-jsonl {out}/results.jsonl'
req={'schema_version':1,'benchmark':'libero-pro','suite':'libero_goal_swap','task_id':1,'seeds':list(range(66,81)),'init_mode':'seeded','gpu':0,'max_steps':1000,'workers':1,'program':program,'output_root':out,'purpose':'EXACTLY ONCE UNSEEN66-80 measurement of frozenv08 SHA6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226; no tuning afterward','command':command}
(base/'unseen_request_once.json').write_text(json.dumps(req,indent=2),encoding='utf-8')
tmp=base/'requested_runs.tmp.json'; tmp.write_text(json.dumps(req,indent=2),encoding='utf-8'); tmp.replace(base/'requested_runs.json')
with (base/'code'/'CHANGELOG.md').open('a',encoding='utf-8') as f:
    f.write('\nv08 full development14/15 task,15/15 program. Flipped54/57/60, no regressions;65 repeats support-border failure. SELECTED/FROZENv08 SHA'+sha+' before exactly-once unseen66-80. No further tuning or worker policy requests. fix_code absent pending unseen coverage.\n')
print('Frozen',sha,'dev14/15, program15/15; exactly-once unseen66-80 atomically published')
