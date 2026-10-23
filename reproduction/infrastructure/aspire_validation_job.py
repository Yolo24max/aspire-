"""Coordinator-only heldout job, queued behind the machine equivalence check."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import tarfile
import time
from aspire_attempt_layout import attempt_layout

def run_owned_evaluation(argv, cwd, env, timeout):
    process=subprocess.Popen(argv,cwd=cwd,env=env,start_new_session=True)
    try:
        return subprocess.CompletedProcess(argv,process.wait(timeout=timeout))
    except subprocess.TimeoutExpired:
        # Only this newly created evaluation process group; persistent providers
        # and unrelated user workloads have different groups and are untouched.
        if process.poll() is None:
            assert os.getpgid(process.pid)==process.pid
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        raise

parser = argparse.ArgumentParser()
parser.add_argument('--task-id', type=int, required=True)
parser.add_argument('--incremental-artifacts', action='store_true')
parser.add_argument('--attempt-name')
args = parser.parse_args()
w = Path('/mnt/aspire-work')
repo = w/'ASPIRE'
root = Path((w/'run-root.txt').read_text().strip())
task, attempt_suffix, validation_runs = attempt_layout(root/f'libero-pro/libero_goal_swap/task_{args.task_id}', args.attempt_name)
audit = json.loads((task/'coordinator_handoff_audit.json').read_text())
review = json.loads((task/'coordinator_provenance_review.json').read_text())
program = task/'fix_code.py'
expected = audit['source_sha256']
assert audit['gate'] == 'PASS' and review['status'] == 'PASS'
assert review['source_sha256'] == expected
assert hashlib.sha256(program.read_bytes()).hexdigest() == expected
status_path = w/f'validation-state-task{args.task_id}{attempt_suffix}.json'
deadline = time.monotonic()+2400
while time.monotonic()<deadline:
    p=w/'batch-equivalence-state.json'
    if p.exists():
        equivalence=json.loads(p.read_text())
        if equivalence['phase']=='finished':
            break
    time.sleep(2)
else:
    raise TimeoutError('Equivalence diagnostic has no final verdict; evaluation not started')
verdict=equivalence['verdict']
assert verdict and verdict['conclusive'], 'Missing diagnostic episodes: no evaluation launched'
workers=4 if verdict['equivalent'] else 1
lock=(w/'episode.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX)
status={'phase':'running','job':'heldout_evaluation','task_id':args.task_id,'gpu':0,
        'attempt_name':args.attempt_name,
        'source_sha256':expected,'workers':workers,'started':time.time(),
        'artifact_transport':'incremental_ssh_tar_stream' if args.incremental_artifacts else 'remote_tar_archive'}
status_path.write_text(json.dumps(status,indent=2))
(root/'gpu-ledger.json').write_text(json.dumps({**status,'episode_running':True},indent=2))
env={**os.environ,**json.loads((w/'runtime-env.json').read_text())}
cap_harness=w/'guarded-cap-harness' if args.incremental_artifacts else repo/'.venv-libero/bin/cap-harness'
assert cap_harness.is_file()
argv=['python3','.claude/skills/iterative-debugging/scripts/run_validation.py',
      '--benchmark','libero-pro','--suite','libero_goal_swap','--task-id',str(args.task_id),
      '--gpu','0','--run-root',str(root),'--program',str(program),
      '--cap-harness',str(cap_harness),'--init-mode','seeded',
      '--max-steps','1000','--seeds',*[str(s) for s in range(1,51)],'--resume','--workers',str(workers)]
if args.attempt_name:
    argv.extend(['--output-root', str(task/'validation')])
try:
    result=run_owned_evaluation(argv,cwd=repo,env=env,timeout=6000)
    assert hashlib.sha256(program.read_bytes()).hexdigest()==expected
    manifests=[]
    for p in validation_runs.glob('*/manifest.json'):
        record=json.loads(p.read_text())
        if record['identity']['code_sha256']==expected:
            manifests.append((p,record))
    assert len(manifests)==1, 'Expected one coherent frozen-policy validation manifest'
    manifest_path,manifest=manifests[0]
    status.update(phase='finished',exit_code=result.returncode,finished=time.time(),
                  manifest=str(manifest_path),trials=manifest['trials'],passes=manifest['passes'],
                  pass_rate=manifest['pass_rate'],manifest_status=manifest['status'])
    status_path.write_text(json.dumps(status,indent=2))
    (root/'gpu-ledger.json').write_text(json.dumps({**status,'episode_running':False},indent=2))
    fcntl.flock(lock,fcntl.LOCK_UN)
    if not args.incremental_artifacts:
        archive_path=w/f'task{args.task_id}{attempt_suffix}-validation-artifacts.tar.gz'
        with tarfile.open(archive_path,'w:gz') as archive:
            archive.add(task/'validation',arcname='validation')
        status.update(phase='artifacts_ready',archive=str(archive_path),archive_bytes=archive_path.stat().st_size)
except BaseException as exc:
    status.update(phase='runner_error',error=repr(exc),finished=time.time())
    raise
finally:
    status_path.write_text(json.dumps(status,indent=2))
    ledger_path=root/'gpu-ledger.json'
    current_ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    if current_ledger.get('job')=='heldout_evaluation' and current_ledger.get('started')==status['started']:
        ledger_path.write_text(json.dumps({**status,'episode_running':False},indent=2))
    print(json.dumps(status),flush=True)
