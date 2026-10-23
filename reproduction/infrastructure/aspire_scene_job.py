"""Root-only initial public scene for a newly allocated campaign task."""
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
args=parser.parse_args();w=Path('/mnt/aspire-work');repo=w/'ASPIRE'
root=Path((w/'run-root.txt').read_text().strip())
task=root/f'libero-pro/libero_goal_swap/task_{args.task_id}'
lock=(w/'episode.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
(task/'code').mkdir(parents=True,exist_ok=True);(task/'debug/logs').mkdir(parents=True,exist_ok=True)
program=task/'code/probe_scene.py'
shutil.copyfile(repo/'.claude/skills/iterative-debugging/scripts/scene_snapshot.py',program)
state_path=w/f'initial-scene-state-task{args.task_id}.json'
status={'phase':'running','job':'initial_public_scene','task_id':args.task_id,'gpu':0,'started':time.time()}
state_path.write_text(json.dumps(status,indent=2))
(root/'gpu-ledger.json').write_text(json.dumps({**status,'episode_running':True},indent=2))
env={**os.environ,**json.loads((w/'runtime-env.json').read_text())}
try:
    with (task/'debug/logs/scene_snapshot.log').open('w') as log:
        result=subprocess.run(['timeout','600',str(repo/'.venv-libero/bin/cap-harness'),
            'run','--benchmark','libero-pro','--suite','libero_goal_swap','--task-id',str(args.task_id),
            '--seed','51','--program',str(program),'--output-root',str(task/'debug/explore'),
            '--flat-run-dir','--no-videos','--init-mode','seeded','--max-steps','1000'],
            cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
    outcomes=list((task/'debug/explore').rglob('outcome.json'))
    assert len(outcomes)==1
    outcome=json.loads(outcomes[0].read_text());assert outcome['program_ok']
    status.update(exit_code=result.returncode,finished=time.time())
    archive_path=w/f'task{args.task_id}-initial.tar.gz'
    with tarfile.open(archive_path,'w:gz') as archive:
        for relative in ['code/probe_scene.py','debug/explore','debug/logs/scene_snapshot.log']:
            archive.add(task/relative,arcname=relative)
    status.update(phase='artifacts_ready',archive=str(archive_path),archive_bytes=archive_path.stat().st_size)
except BaseException as exc:
    status.update(phase='runner_error',error=repr(exc));raise
finally:
    state_path.write_text(json.dumps(status,indent=2))
    (root/'gpu-ledger.json').write_text(json.dumps({**status,'episode_running':False},indent=2))
    print(json.dumps(status),flush=True)
