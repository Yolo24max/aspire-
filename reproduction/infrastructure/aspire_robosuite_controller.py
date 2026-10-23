"""Root-owned single-GPU Robosuite request queue with durable transport recovery.

Default execution waits for execution-ready.json, verified both locally and remotely.
--prepare-only is entirely offline. Worker requests never execute shell command text.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shlex
import tarfile
import time

from aspire_network_recovery import SSHRecovery, acquire_local_lock, atomic_json
from aspire_policy_budget import is_observation_only
from aspire_robosuite_job import (SUITES, canonical, digest, enforce_history,
                                  validate_settings)


def emit(**fields):
    print(json.dumps({'time': time.time(), **fields}), flush=True)


def remote_json(recovery, source, label, timeout=30):
    return recovery.run(lambda: json.loads(recovery.python(source, timeout=timeout)), label)


def history_records(task):
    records = []
    for path in sorted((task / '.requests').glob('*/reservation.json')):
        row = json.loads(path.read_text())
        original = task / row['program']
        if digest(original) != row['source_sha256'] or digest(path.with_name('program.py')) != row['source_sha256']:
            raise ValueError('Prior numbered source or immutable snapshot changed')
        status = path.with_name('result.json')
        if status.exists():
            row.update(json.loads(status.read_text()))
        records.append(row)
    return records


def build_request(raw, task, remote_task, suite, task_id, history):
    validate_settings(raw, suite, task_id)
    program = PurePosixPath(raw['program'])
    if program.is_absolute():
        program = program.relative_to(remote_task)
    if len(program.parts) != 2 or program.parts[0] != 'code' or program.suffix != '.py' or '..' in program.parts:
        raise ValueError('Program must be immutable code/<version>.py')
    local = (task / str(program)).resolve()
    if local.is_symlink() or not local.is_relative_to((task / 'code').resolve()):
        raise ValueError('Source path is outside task code')
    source_hash = digest(local)
    source = local.read_text(encoding='utf-8')
    observation = is_observation_only(source)
    req = {k: raw[k] for k in ('benchmark', 'suite', 'task_id', 'init_mode',
           'max_steps', 'camera_width', 'camera_height', 'workers', 'gpu', 'seeds', 'failure_mode')}
    req.update(program=program.as_posix(), source_sha256=source_hash,
               observation_only=observation, execution_mode='fresh_per_seed',
               run_root=str(remote_task.parents[2]))
    req['stage'] = enforce_history(req, history, source_hash, observation)
    output = PurePosixPath(raw['output_root'])
    relative = output.relative_to(remote_task) if output.is_absolute() else output
    allowed = {PurePosixPath('debug/explore'), PurePosixPath('debug/initial'),
               PurePosixPath('debug/holdout')}
    numbered = len(relative.parts) == 3 and relative.parts[:2] == ('debug', 'attempts') and \
        len(relative.name) == 3 and relative.name[0] == 'v' and relative.name[1:].isdigit()
    if relative not in allowed and not numbered:
        raise ValueError('Use exact official debug/explore, initial, attempts/vNN, or holdout root')
    if '..' in relative.parts:
        raise ValueError('Output path traversal')
    if req['stage'] == 'observe' and relative != PurePosixPath('debug/explore'):
        raise ValueError('Observation must use debug/explore')
    if req['stage'] == 'unseen' and relative != PurePosixPath('debug/holdout'):
        raise ValueError('Unseen must use debug/holdout')
    if req['stage'] in ('pilot', 'development') and relative in {PurePosixPath('debug/explore'), PurePosixPath('debug/holdout')}:
        raise ValueError('Policy development must use initial or attempts/vNN')
    req['output_root'] = str(remote_task / relative)
    if req['stage'] == 'development':
        pilots = [h for h in history if h.get('stage') == 'pilot' and
                  h['source_sha256'] == source_hash and h.get('phase') == 'artifacts_ready']
        pilot = pilots[-1]
        if pilot['output_root'] != req['output_root']:
            raise ValueError('Development must reuse pilot101 output root for this version')
        req['reuse_pilot101'] = dict(pilot['outcomes'][0], from_request_id=pilot['request_id'])
    # Repeated identical requests deduplicate even when worker rewrites JSON whitespace.
    identity = hashlib.sha256(canonical(req)).hexdigest()
    return req, identity, local


def local_gate(path, remote_root, suite, task_id):
    if not path.exists():
        return False
    gate = json.loads(path.read_text())
    expected = dict(owner='robosuite', benchmark='robosuite', launch_enabled=True,
                    gpu=0, run_root=str(remote_root))
    return all(type(gate.get(k)) is type(v) and gate.get(k) == v for k, v in expected.items()) and \
        gate.get('suite', suite) == suite and gate.get('task_id', task_id) == task_id


def put_immutable(recovery, remote, content):
    """Idempotent immutable installation; never overwrite previously submitted data."""
    code = f'''from pathlib import Path
import hashlib,json,os
p=Path({str(remote)!r});data=bytes.fromhex({content.hex()!r})
p.parent.mkdir(parents=True,exist_ok=True)
try:
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
except FileExistsError:
 assert p.read_bytes()==data,'Immutable file changed'
print(json.dumps({{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}))
'''
    result = remote_json(recovery, code, 'install_immutable_file')
    if result['sha256'] != hashlib.sha256(content).hexdigest():
        raise ValueError('Immutable upload SHA mismatch')


def launch_once(recovery, root, task, request_id, job_script, gate):
    """Safe to retry after a lost response: claim persists before Popen."""
    code = f'''import fcntl,json,os,subprocess,time
from pathlib import Path
root=Path({str(root)!r});task=Path({str(task)!r});job=task/'.requests'/{request_id!r}
g=json.loads(Path({str(gate)!r}).read_text())
assert g['owner']=='robosuite' and g['benchmark']=='robosuite' and g['launch_enabled'] is True
assert g['gpu']==0 and g['run_root']==str(root)
with (job/'launch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 claim=job/'launch_claim.json'
 if not claim.exists():
  with claim.open('x') as f:json.dump({{'claimed_at':time.time(),'request_id':{request_id!r},'status':'launch_claimed'}},f);f.flush();os.fsync(f.fileno())
  req=json.loads((job/'request.json').read_text())
  with (job/'job.log').open('a') as log:
   child=subprocess.Popen(['python3','-u',{str(job_script)!r},'--run-root',str(root),'--suite',req['suite'],'--task-id',str(req['task_id']),'--request-dir',str(job),'--gate',{str(gate)!r}],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()
  value={{'request_id':{request_id!r},'pid':child.pid,'start_ticks':stat[19],'status':'spawned','claimed_at':time.time(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}}
  tmp=claim.with_suffix('.tmp');tmp.write_text(json.dumps(value));os.replace(tmp,claim)
 print(claim.read_text())
'''
    return remote_json(recovery, code, 'claim_or_reconcile_exact_once_launch')


def snapshot(recovery, remote_job, request_id):
    code = f'''from pathlib import Path
import fcntl,json
j=Path({str(remote_job)!r});claim=json.loads((j/'launch_claim.json').read_text())
state=json.loads((j/'state.json').read_text()) if (j/'state.json').exists() else {{'phase':'launch_ambiguous'}}
assert claim['request_id']=={request_id!r}
identity=state.get('identity') or claim
p=Path('/proc')/str(identity.get('pid',0));alive=False
if p.exists() and identity.get('start_ticks'):
 stat=(p/'stat').read_text().rsplit(')',1)[1].split()
 cmd=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
 alive=stat[19]==identity['start_ticks'] and {str(remote_job)!r} in cmd and identity.get('boot_id')==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
locked=False
with Path('/mnt/aspire-work/episode.lock').open('a+') as lock:
 lock.seek(0)
 try:owner=json.loads(lock.read() or '{{}}')
 except json.JSONDecodeError:owner={{}}
 try:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 except BlockingIOError:
  locked=owner.get('request_id')=={request_id!r} and owner.get('pid')==identity.get('pid') and owner.get('start_ticks')==identity.get('start_ticks')
state.update(process_identity_verified=alive,launch_claim=claim,group_lock_verified=locked)
print(json.dumps(state))
'''
    return remote_json(recovery, code, 'reconcile_process_and_request_identity')


def verify_archive(archive, destination, prefix, expected_source):
    """Reject traversal/links, verify every file, then publish the complete seed tree."""
    destination = Path(destination)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            rel = PurePosixPath(member.name)
            if rel.is_absolute() or '..' in rel.parts or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe archive member')
            if not rel.is_relative_to(PurePosixPath(prefix)):
                raise ValueError('Archive member outside completed seed')
        names = [m.name for m in members]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive members')
        tar.extractall(destination, filter='data')
    seed_root = destination / prefix
    inventory = json.loads((seed_root / '.transfer-inventory.json').read_text())
    actual = {p.relative_to(seed_root).as_posix() for p in seed_root.rglob('*') if p.is_file()}
    if actual != {i['path'] for i in inventory} | {'.transfer-inventory.json'}:
        raise ValueError('Archive inventory does not enumerate every file')
    for item in inventory:
        p = (seed_root / item['path']).resolve()
        if not p.is_relative_to(seed_root.resolve()) or p.is_symlink():
            raise ValueError('Inventory path escapes seed')
        if p.stat().st_size != item['size_bytes'] or digest(p) != item['sha256']:
            raise ValueError('All-file inventory size/SHA verification failed')
    runs = list(seed_root.rglob('run.json'))
    if len(runs) != 1:
        raise ValueError('Expected exactly one completed run')
    run = runs[0].parent
    if json.loads(runs[0].read_text())['status'] != 'finalized':
        raise ValueError('Run has not finalized')
    if digest(run / 'source/program.py') != expected_source:
        raise ValueError('Archived source differs from frozen program')
    manifest = json.loads((run / 'manifest.json').read_text())
    files = []
    for item in manifest['files']:
        p = (run / item['path']).resolve()
        if not p.is_relative_to(run.resolve()) or p.is_symlink():
            raise ValueError('Manifest path outside run')
        if p.stat().st_size != item['size_bytes'] or digest(p) != item['sha256']:
            raise ValueError('Artifact size/SHA verification failed')
        files.append(dict(item, relative=p.relative_to(destination).as_posix()))
    return [dict(i, relative=(seed_root / i['path']).relative_to(destination).as_posix())
            for i in inventory]


def backup_seed(recovery, local_task, remote_task, remote_job, request, request_id, seed):
    receipt_path = local_task / '.requests' / request_id / f'seed_{seed:04d}_receipt.json'
    old = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    if old and old.get('remote_retired'):
        return old
    if seed == 101 and request.get('reuse_pilot101') and not old:
        prior_id = request['reuse_pilot101']['from_request_id']
        prior_path = local_task / '.requests' / prior_id / 'seed_0101_receipt.json'
        prior = json.loads(prior_path.read_text())
        if prior.get('source_sha256') != request['source_sha256'] or not prior.get('remote_retired'):
            raise ValueError('Reused pilot101 lacks a verified durable backup receipt')
        if digest(prior['archive']) != prior['archive_sha256']:
            raise ValueError('Reused pilot101 archive changed')
        for item in prior['verified_files']:
            p = local_task / item['relative']
            if p.stat().st_size != item['size_bytes'] or digest(p) != item['sha256']:
                raise ValueError('Reused pilot101 artifact changed')
        reused = dict(prior, request_id=request_id, reused_from_request_id=prior_id,
                      reuse_verified_at=time.time())
        atomic_json(receipt_path, reused)
        return reused
    relative = PurePosixPath(request['output_root']).relative_to(remote_task) / f'{seed:04d}'
    remote_archive = remote_job / f'seed_{seed:04d}.tar.gz'
    local_archive = receipt_path.with_suffix('.tar.gz')
    if not old:
        code = f'''from pathlib import Path
import io,json,tarfile,hashlib,os
t=Path({str(remote_task)!r});p=t/{relative.as_posix()!r};a=Path({str(remote_archive)!r})
assert p.resolve().is_relative_to(t.resolve()) and not p.is_symlink()
if not a.exists():
 items=[]
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink()
  if f.is_file():
   h=hashlib.sha256()
   with f.open('rb') as stream:
    for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b)
   items.append({{'path':f.relative_to(p).as_posix(),'size_bytes':f.stat().st_size,'sha256':h.hexdigest()}})
 data=json.dumps(items).encode()
 tmp=a.with_suffix('.partial')
 with tarfile.open(tmp,'w:gz',compresslevel=1) as f:
  f.add(p,arcname={relative.as_posix()!r})
  info=tarfile.TarInfo({(relative / '.transfer-inventory.json').as_posix()!r});info.size=len(data)
  f.addfile(info,io.BytesIO(data))
 os.replace(tmp,a)
h=hashlib.sha256()
with a.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
print(json.dumps({{'size_bytes':a.stat().st_size,'sha256':h.hexdigest()}}))
'''
        expected = remote_json(recovery, code, 'package_completed_seed', timeout=300)
        partial = local_archive.with_suffix('.partial')

        def transfer():
            with recovery.sftp() as sftp:
                sftp.get(str(remote_archive), str(partial))
        recovery.run(transfer, 'download_completed_seed')
        if partial.stat().st_size != expected['size_bytes'] or digest(partial) != expected['sha256']:
            raise ValueError('Seed archive size/SHA mismatch')
        partial.replace(local_archive)
        files = verify_archive(local_archive, local_task, relative.as_posix(), request['source_sha256'])
        old = dict(request_id=request_id, seed=seed, source_sha256=request['source_sha256'],
                   archive=str(local_archive), archive_sha256=expected['sha256'],
                   archive_bytes=expected['size_bytes'], verified_files=files,
                   verified_at=time.time(), remote_retired=False)
        # Receipt is durable BEFORE retirement; a reconnect never recopies retired payload.
        atomic_json(receipt_path, old)
    else:
        if digest(old['archive']) != old['archive_sha256']:
            raise ValueError('Previously verified local archive changed')
        for item in old['verified_files']:
            p = local_task / item['relative']
            if p.stat().st_size != item['size_bytes'] or digest(p) != item['sha256']:
                raise ValueError('Previously verified artifact changed')
    # The verifier enumerates ALL manifest files. Retain complete metadata on server.
    retain = {'run.json', 'outcome.json', 'manifest.json', 'episode/reset.json',
              'source/program.py', 'source/program-result.json', 'source/program-error.json',
              'trace/events.jsonl'}
    retiring = [i for i in old['verified_files']
                if not any(i['path'] == name or i['path'].endswith('/' + name) for name in retain)]
    code = f'''from pathlib import Path
import hashlib,json,os
t=Path({str(remote_task)!r});items={retiring!r};receipt=Path({str(remote_job / receipt_path.name)!r})
for item in items:
 p=(t/item['relative']).resolve();assert p.is_relative_to(t.resolve()) and not p.is_symlink()
 if p.exists():
  assert p.stat().st_size==item['size_bytes']
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  assert h.hexdigest()==item['sha256']
  p.unlink()
value={{'request_id':{request_id!r},'seed':{seed},'local_archive_sha256':{old['archive_sha256']!r},'verified':True,'remote_retired':True}}
tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(value));os.replace(tmp,receipt)
a=Path({str(remote_archive)!r})
if a.exists():a.unlink()
print(json.dumps(value))
'''
    remote_receipt = remote_json(recovery, code, 'retire_only_sha_verified_seed_payload', timeout=300)
    old.update(remote_retired=True, remote_receipt=remote_receipt)
    atomic_json(receipt_path, old)
    return old


def ensure_frozen_policy(task, request, request_id):
    """Keep the worker's detailed freeze intact; bind the controller request separately."""
    freeze = dict(source_sha256=request['source_sha256'], request_id=request_id,
                  program=request['program'], seeds=request['seeds'])
    worker_path = task / 'freeze_manifest.json'
    if worker_path.exists():
        worker = json.loads(worker_path.read_text(encoding='utf-8'))
        hashes = {worker[k] for k in ('source_sha256', 'sha256') if k in worker}
        if hashes != {request['source_sha256']}:
            raise ValueError('Frozen policy source cannot change')
        if worker.get('program', worker.get('selected_program')) != request['program']:
            raise ValueError('Frozen policy program cannot change')
        if worker.get('seeds', worker.get('unseen_seeds')) != request['seeds']:
            raise ValueError('Frozen unseen partition cannot change')
        if 'request_id' in worker and worker['request_id'] != request_id:
            raise ValueError('Frozen request identity cannot change')
    else:
        atomic_json(worker_path, freeze)
    controller_path = task / 'controller_freeze_manifest.json'
    if controller_path.exists() and json.loads(controller_path.read_text(encoding='utf-8')) != freeze:
        raise ValueError('Frozen controller request cannot change')
    atomic_json(controller_path, freeze)


def execute_request(recovery, args, task, remote_task, request, request_id, source):
    directory = task / '.requests' / request_id
    directory.mkdir(parents=True, exist_ok=True)
    reservation = dict(request, request_id=request_id, phase='reserved', reserved_at=time.time())
    if not (directory / 'reservation.json').exists():
        atomic_json(directory / 'reservation.json', reservation)
        (directory / 'program.py').write_bytes(source.read_bytes())
        (directory / 'request.json').write_bytes(canonical(request))
    elif digest(directory / 'program.py') != request['source_sha256']:
        raise ValueError('Immutable local source snapshot changed')
    if request['stage'] == 'unseen':
        ensure_frozen_policy(task, request, request_id)
    job_path = Path(getattr(args, 'job_script', Path(__file__).with_name('aspire_robosuite_job.py')))
    content = job_path.read_bytes()
    remote_script = args.remote_run_root / '.infrastructure' / f'robosuite_job_{hashlib.sha256(content).hexdigest()}.py'
    remote_job = remote_task / '.requests' / request_id
    put_immutable(recovery, remote_script, content)
    put_immutable(recovery, remote_job / 'program.py', (directory / 'program.py').read_bytes())
    put_immutable(recovery, remote_job / 'request.json', canonical(request))
    launch = launch_once(recovery, args.remote_run_root, remote_task, request_id, remote_script, args.remote_gate)
    atomic_json(directory / 'launch_identity.json', launch)
    launch_grace = time.monotonic() + 15
    while True:
        state = snapshot(recovery, remote_job, request_id)
        atomic_json(directory / 'last_remote_state.json', state)
        atomic_json(task / 'coordinator_status.json', dict(state, request_id=request_id))
        for seed in state.get('completed_seeds', []):
            backup_seed(recovery, task, remote_task, remote_job, request, request_id, seed)
        emit(phase=state['phase'], request_id=request_id, suite=args.suite,
             completed=len(state.get('completed_seeds', [])), total=len(request['seeds']))
        if state['phase'] == 'finished':
            if set(state['completed_seeds']) != set(request['seeds']):
                raise ValueError('Finished job does not cover every seed')
            result = dict(phase='artifacts_ready', outcomes=state['outcomes'],
                          request_id=request_id, source_sha256=request['source_sha256'])
            atomic_json(directory / 'result.json', result)
            atomic_json(task / 'coordinator_status.json', dict(request, **result))
            return
        if state['phase'] == 'launch_ambiguous' and state['process_identity_verified'] and time.monotonic() < launch_grace:
            time.sleep(1)
            continue
        if state['phase'] not in ('running', 'claiming_gpu') or not state['process_identity_verified']:
            # Ambiguous launch, exited process, or remote error are never replayed.
            raise RuntimeError('Remote job needs inspection; exact-once claim retained: ' + state['phase'])
        if state['phase'] == 'running' and not state.get('group_lock_verified'):
            raise RuntimeError('Remote process no longer holds its verified exclusive group lock')
        time.sleep(args.poll_seconds)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--local-run-root', '--run-root', dest='local_run_root', type=Path, required=True)
    p.add_argument('--remote-run-root', type=PurePosixPath, required=True)
    p.add_argument('--suite', choices=sorted(SUITES), required=True)
    p.add_argument('--task-id', type=int, default=0)
    p.add_argument('--gate', type=Path)
    p.add_argument('--remote-gate', type=PurePosixPath)
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--poll-seconds', type=float, default=10)
    args = p.parse_args()
    if args.task_id != 0 or not args.remote_run_root.is_absolute() or '..' in args.remote_run_root.parts:
        p.error('Absolute remote campaign root and task_id 0 are required')
    args.remote_run_root.relative_to('/mnt/aspire-work/ASPIRE/outputs/runs')
    if args.poll_seconds < 1:
        p.error('poll-seconds must be >=1')
    task = args.local_run_root.resolve() / 'robosuite' / args.suite / f'task_{args.task_id}'
    remote_task = args.remote_run_root / 'robosuite' / args.suite / f'task_{args.task_id}'
    task.mkdir(parents=True, exist_ok=True)
    args.gate = args.gate or args.local_run_root / 'execution-ready.json'
    args.remote_gate = args.remote_gate or args.remote_run_root / 'execution-ready.json'
    args.remote_gate.relative_to(args.remote_run_root)
    (task / 'code').mkdir(exist_ok=True)
    emit(phase='prepared', local_task=str(task), remote_task=str(remote_task),
         gate=str(args.gate), default_action='wait_for_root_execution_gate')
    if args.prepare_only:
        return
    lock = acquire_local_lock(task / 'controller.lock')
    recovery = None
    rejected = set()
    try:
        while not (task / 'controller.stop').exists():
            history = history_records(task)
            pending = [h for h in history if h.get('phase') != 'artifacts_ready']
            request_file = task / 'requested_runs.json'
            if not pending and (not local_gate(args.gate, args.remote_run_root, args.suite, args.task_id) or
                                not request_file.exists() or time.time() - request_file.stat().st_mtime < 2):
                time.sleep(args.poll_seconds); continue
            payload = request_file.read_bytes() if request_file.exists() else b''
            payload_sha = hashlib.sha256(payload).hexdigest()
            if not pending and payload_sha in rejected:
                time.sleep(args.poll_seconds); continue
            try:
                raw = pending[0].get('worker_request') if pending else (json.loads(payload) if payload else None)
                # A pending reservation always takes precedence over later worker requests.
                candidates = pending or [h for h in history if h.get('worker_request') == raw]
                if not candidates:
                    # Same source/partition must never rerun because of irrelevant request changes.
                    validate_settings(raw, args.suite, args.task_id)
                    program = PurePosixPath(raw['program'])
                    if program.is_absolute():
                        program = program.relative_to(remote_task)
                    if len(program.parts) != 2 or program.parts[0] != 'code' or '..' in program.parts:
                        raise ValueError('Program must be task-local code/<version>.py')
                    submitted_hash = digest(task / str(program))
                    candidates = [h for h in history if h['source_sha256'] == submitted_hash and
                                  h['seeds'] == raw.get('seeds')]
                if not candidates:
                    request, request_id, source = build_request(raw, task, remote_task,
                                                               args.suite, args.task_id, history)
            except (ValueError, KeyError, TypeError, OSError) as error:
                rejection = task / '.rejections' / payload_sha
                rejection.mkdir(parents=True, exist_ok=True)
                (rejection / 'request.json').write_bytes(payload)
                failure = dict(phase='prelaunch_rejected', request_sha256=payload_sha,
                               error_type=type(error).__name__, error=str(error), time=time.time())
                atomic_json(rejection / 'error.json', failure)
                atomic_json(task / 'controller_error.json', failure)
                atomic_json(task / 'coordinator_status.json', failure)
                emit(**failure)
                rejected.add(payload_sha)
                continue
            if candidates:
                old = candidates[0]
                if old.get('phase') == 'artifacts_ready':
                    prior_result = json.loads((task / '.requests' / old['request_id'] / 'result.json').read_text())
                    atomic_json(task / 'coordinator_status.json', dict(old, **prior_result, deduplicated=True))
                    time.sleep(args.poll_seconds); continue
                request_id = old['request_id']
                directory = task / '.requests' / request_id
                request = json.loads((directory / 'request.json').read_text())
                source = directory / 'program.py'
            else:
                directory = task / '.requests' / request_id
                if (directory / 'result.json').exists():
                    time.sleep(args.poll_seconds); continue
                directory.mkdir(parents=True, exist_ok=True)
                reservation = dict(request, request_id=request_id, phase='reserved',
                                   worker_request=raw, reserved_at=time.time())
                atomic_json(directory / 'reservation.json', reservation)
                (directory / 'program.py').write_bytes(source.read_bytes())
                (directory / 'request.json').write_bytes(canonical(request))
            if recovery is None:
                state_root = args.local_run_root / 'network-monitoring'
                state_root.mkdir(parents=True, exist_ok=True)
                recovery = SSHRecovery.interactive(state_root / f'{args.suite}-task{args.task_id}-controller.json',
                    dict(benchmark='robosuite', suite=args.suite, task_id=args.task_id,
                         run_root=str(args.remote_run_root), role='controller'))
            execute_request(recovery, args, task, remote_task, request, request_id, source)
    except Exception as error:
        failure = dict(phase='controller_error', error_type=type(error).__name__, error=str(error), time=time.time())
        atomic_json(task / 'controller_error.json', failure)
        atomic_json(task / 'coordinator_status.json', failure)
        emit(**failure)
        raise
    finally:
        if recovery:
            recovery.close()
        lock.close()


if __name__ == '__main__':
    main()
