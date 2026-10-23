"""Root-only reconnecting Robosuite100 snapshots; this file never launches jobs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import time

from aspire_network_recovery import SSHRecovery, acquire_local_lock, atomic_json
from aspire_robosuite_validation_job import SUITES, SEEDS, digest, identity, run_id


def parse_args(description=__doc__):
    p = argparse.ArgumentParser(description=description)
    p.add_argument('--local-run-root', '--run-root', dest='local_run_root', type=Path, required=True)
    p.add_argument('--remote-run-root', type=PurePosixPath, required=True)
    p.add_argument('--suite', choices=sorted(SUITES), required=True)
    p.add_argument('--task-id', type=int, default=0)
    p.add_argument('--source-sha256')
    p.add_argument('--once', action='store_true')
    p.add_argument('--poll-seconds', type=float, default=10)
    p.add_argument('--max-network-failures', type=int)
    args = p.parse_args()
    if args.task_id != 0 or not args.remote_run_root.is_absolute() or '..' in args.remote_run_root.parts or args.poll_seconds < 1:
        p.error('Absolute remote campaign root, task_id0 and poll-seconds>=1 are required')
    args.remote_run_root.relative_to('/mnt/aspire-work/ASPIRE/outputs/runs')
    args.local_task = args.local_run_root.resolve() / 'robosuite' / args.suite / f'task_{args.task_id}'
    args.remote_task = args.remote_run_root / 'robosuite' / args.suite / f'task_{args.task_id}'
    sha = digest(args.local_task / 'fix_code.py')
    if args.source_sha256 and args.source_sha256 != sha:
        p.error('Local frozen fix_code.py differs from expected SHA256')
    args.source_sha256 = sha
    args.expected = identity(args.suite, args.task_id, sha)
    args.run_id = run_id(args.expected)
    args.network_root = args.local_run_root.resolve() / 'network-monitoring'
    args.network_root.mkdir(parents=True, exist_ok=True)
    return args


def snapshot_source(remote_task, expected, rid):
    return f'''from pathlib import Path
import fcntl,json,hashlib
task=Path({str(remote_task)!r}).resolve();owned=task/'.heldout'/{rid!r}
expected={expected!r};claim_path=owned/'launch_claim.json';state_path=owned/'state.json'
state=json.loads(state_path.read_text()) if state_path.exists() else {{}}
claim=json.loads(claim_path.read_text()) if claim_path.exists() else {{}}
if not claim:
 print(json.dumps({{'phase':'not_launched','run_id':{rid!r},'identity':expected,'trials':0,'passes':0,'results':{{}},'canonical_task':str(task)}}))
 raise SystemExit(0)
assert claim['run_id']=={rid!r} and claim['identity']==expected
if state:assert state['run_id']=={rid!r} and state['identity']==expected
process=state.get('process_identity') or claim['process_identity'];proc=Path('/proc')/str(process['pid'])
alive=False
if proc.exists():
 stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
 cmd=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
 alive=stat[19]==process['start_ticks'] and process['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and cmd==process['command'] and '--guarded-cap' not in cmd
locked=False
with Path('/mnt/aspire-work/episode.lock').open('a+') as lock:
 lock.seek(0)
 try:owner=json.loads(lock.read() or '{{}}')
 except json.JSONDecodeError:owner={{}}
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 except BlockingIOError:locked=owner.get('run_id')=={rid!r} and owner.get('pid')==process['pid'] and owner.get('start_ticks')==process['start_ticks']
manifest_path=task/'validation/runs'/{rid!r}/'manifest.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {{}}
if manifest:
 assert manifest['identity']==expected and manifest['run_id']=={rid!r}
 assert set(map(int,manifest['results']))<=set(range(1,101))
 assert len(manifest['results'])==manifest['trials']
 assert all(str(row['seed'])==key for key,row in manifest['results'].items())
 results={{key:{{k:row.get(k) for k in ('seed','program_ok','task_success','run_dir')}} for key,row in manifest['results'].items()}}
else:results={{}}
value={{'phase':state.get('phase','launch_ambiguous'),'run_id':{rid!r},'identity':expected,'process_identity':process,
 'process_identity_verified':alive,'group_lock_verified':locked,'canonical_task':str(task),
 'trials':manifest.get('trials',0),'passes':manifest.get('passes',0),'pass_rate':manifest.get('pass_rate',0),
 'manifest_status':manifest.get('status'),'results':results,'error_type':state.get('error_type'),
 'source_sha256':expected['code_sha256'],'manifest_relative':str(manifest_path.relative_to(task))}}
print(json.dumps(value))
'''


def read_snapshot(network, args):
    source = snapshot_source(args.remote_task, args.expected, args.run_id)
    return network.run(lambda: json.loads(network.python(source)), 'read_robosuite100_validation_identity',
                       max_failures=args.max_network_failures)


def validate_snapshot(snapshot, previous, expected, rid):
    if snapshot['run_id'] != rid or snapshot['identity'] != expected:
        raise ValueError('Frozen evaluation identity changed')
    if previous and (previous['run_id'] != rid or snapshot['trials'] < previous['trials']):
        raise ValueError('Evaluation seed coverage regressed; preserve prior snapshot')
    if snapshot.get('phase') == 'running' and (not snapshot.get('process_identity_verified') or
                                                not snapshot.get('group_lock_verified')):
        raise ValueError('Running evaluation process/group-lock identity cannot be verified')
    if snapshot.get('manifest_status') == 'complete' and set(map(int, snapshot['results'])) != set(SEEDS):
        raise ValueError('Complete manifest does not contain exactly100 distinct seeds')


def main():
    args = parse_args()
    prefix = f'{args.suite}-task{args.task_id}-validation'
    lease = acquire_local_lock(args.network_root / f'{prefix}-monitor.lock')
    progress = args.network_root / f'{prefix}-progress.json'
    previous = json.loads(progress.read_text()) if progress.exists() else None
    network = SSHRecovery.interactive(args.network_root / f'{prefix}-monitor-network.json',
        dict(role='validation_monitor', run_root=str(args.remote_run_root), run_id=args.run_id,
             suite=args.suite, task_id=args.task_id, source_sha256=args.source_sha256))
    try:
        while True:
            value = read_snapshot(network, args)
            validate_snapshot(value, previous, args.expected, args.run_id)
            atomic_json(progress, value)
            if value != previous:
                print(json.dumps({k: v for k, v in value.items() if k not in ('results', 'identity')}), flush=True)
                previous = value
            if args.once or value['phase'] in ('finished', 'partial', 'runner_error', 'gpu_lock_unavailable'):
                return
            time.sleep(args.poll_seconds)
    finally:
        network.close(); lease.close()


if __name__ == '__main__':
    main()
