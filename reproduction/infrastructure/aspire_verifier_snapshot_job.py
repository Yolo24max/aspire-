"""Root-owned fresh public verifier scene, queued after its full evaluation."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import shutil
import subprocess
import tarfile
import time

parser=argparse.ArgumentParser();parser.add_argument('--task-id',type=int,required=True)
args=parser.parse_args()
w=Path('/mnt/aspire-work');repo=w/'ASPIRE'
root=Path((w/'run-root.txt').read_text().strip())
verify=root/f'verification/libero-pro__libero_goal_swap__task_{args.task_id}'
assert not (verify/'debug/explore').exists(), 'Never replace an existing verifier scene'
state_path=w/f'verifier-snapshot-state-task{args.task_id}.json'
state={'phase':'queued','job':'verifier_snapshot','task_id':args.task_id}
state_path.write_text(json.dumps(state,indent=2))
while True:
    p=w/f'validation-state-task{args.task_id}.json'
    if p.exists():
        prior=json.loads(p.read_text())
        if prior['phase']=='runner_error':
            raise RuntimeError('Heldout runner error; verifier not started')
        if prior['phase'] in ('finished','artifacts_ready'):
            assert prior['trials']==50 and prior['manifest_status']=='complete'
            break
    time.sleep(2)
lock=(w/'episode.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
(verify/'code').mkdir(parents=True,exist_ok=True)
(verify/'debug/logs').mkdir(parents=True,exist_ok=True)
program=verify/'code/probe_scene.py'
shutil.copyfile(repo/'.claude/skills/iterative-debugging/scripts/scene_snapshot.py',program)
env={**os.environ,**json.loads((w/'runtime-env.json').read_text())}
state.update(phase='running',started=time.time(),gpu=0)
state_path.write_text(json.dumps(state,indent=2))
(root/'gpu-ledger.json').write_text(json.dumps({**state,'episode_running':True},indent=2))
try:
    with (verify/'debug/logs/scene_snapshot.log').open('w') as log:
        result=subprocess.run(['timeout','600',str(repo/'.venv-libero/bin/cap-harness'),
            'run','--benchmark','libero-pro','--suite','libero_goal_swap','--task-id',str(args.task_id),
            '--seed','51','--program',str(program),'--output-root',str(verify/'debug/explore'),
            '--flat-run-dir','--no-videos','--init-mode','seeded','--max-steps','1000'],
            cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
    outcomes=list((verify/'debug/explore').rglob('outcome.json'))
    assert len(outcomes)==1 and json.loads(outcomes[0].read_text())['program_ok']
    state.update(phase='finished',exit_code=result.returncode,finished=time.time())
    archive_path=w/f'verifier{args.task_id}-initial.tar.gz'
    with tarfile.open(archive_path,'w:gz') as archive:
        for relative in ['code/probe_scene.py','debug/explore','debug/logs/scene_snapshot.log']:
            archive.add(verify/relative,arcname=relative)
    state.update(phase='artifacts_ready',archive=str(archive_path),archive_bytes=archive_path.stat().st_size)
except BaseException as exc:
    state.update(phase='runner_error',error=repr(exc));raise
finally:
    state_path.write_text(json.dumps(state,indent=2))
    (root/'gpu-ledger.json').write_text(json.dumps({**state,'episode_running':False},indent=2))
    print(json.dumps(state),flush=True)
