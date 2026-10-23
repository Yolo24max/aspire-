#!/usr/bin/env python3
"""Root-only, exact-once Robosuite Stage2 driver and per-seed admission wrapper.

Execute only after the coordinator's handoff/provenance audits. Transport loss
does not restart this job. A durable claim with an exited/unknown process requires
root inspection; it is never interpreted as permission to launch again.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

SUITES = {'cube_lifting', 'cube_restack', 'cube_stack', 'nut_assembly',
          'spill_wipe', 'two_arm_lift', 'two_arm_handover'}
SEEDS = list(range(1, 101))
REPO = Path('/mnt/aspire-work/ASPIRE')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def identity(suite, task_id, sha):
    return dict(benchmark='robosuite', suite=suite, task_id=task_id, code_sha256=sha,
                seeds=SEEDS, init_mode='saved', max_steps=1000, camera_width=800, camera_height=512)


def run_id(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:16]


def process_identity(pid=None):
    pid = pid or os.getpid(); base = Path('/proc') / str(pid)
    stat = (base / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=stat[19], boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command=(base / 'cmdline').read_bytes().replace(b'\0', b' ').decode())


def task_path(root, suite, task_id):
    root = Path(root).resolve()
    task = (root / 'robosuite' / suite / f'task_{task_id}').resolve()
    if suite not in SUITES or task_id != 0 or not task.is_relative_to(root):
        raise ValueError('Invalid owned Robosuite task')
    return task


def execution_gate(root, gate_path, suite, task_id):
    gate_path = Path(gate_path).resolve()
    if not gate_path.is_relative_to(Path(root).resolve()):
        raise ValueError('Execution gate outside campaign')
    gate = json.loads(gate_path.read_text())
    expected = dict(benchmark='robosuite', owner='robosuite', gpu=0, launch_enabled=True)
    if any(type(gate.get(k)) is not type(v) or gate.get(k) != v for k, v in expected.items()):
        raise ValueError('Root has not granted this campaign exclusive GPU ownership')
    if Path(gate.get('run_root', '')).resolve() != Path(root).resolve() or \
       gate.get('suite', suite) != suite or gate.get('task_id', task_id) != task_id:
        raise ValueError('Execution gate task identity mismatch')


def validate_handoff(root, task, suite, sha):
    campaign = json.loads((Path(root) / 'campaign.json').read_text())
    if campaign.get('heldout_count') != 100 or campaign.get('dev_seeds') != list(range(101, 126)) or \
       campaign.get('unseen_seeds') != list(range(126, 131)):
        raise ValueError('Campaign partition changed')
    audit = json.loads((task / 'coordinator_handoff_audit.json').read_text())
    review = json.loads((task / 'coordinator_provenance_review.json').read_text())
    if audit.get('gate') != 'PASS' or review.get('status') != 'PASS' or \
       audit.get('source_sha256') != sha or review.get('source_sha256') != sha or digest(task / 'fix_code.py') != sha:
        raise ValueError('Handoff/provenance or frozen-source gate failed')
    freeze = json.loads((task / 'freeze_manifest.json').read_text())
    freeze_hashes = {freeze[k] for k in ('source_sha256', 'sha256') if k in freeze}
    if freeze_hashes != {sha}:
        raise ValueError('Frozen policy identity mismatch')
    measured = {}
    for p in (task / '.requests').glob('*/request.json'):
        req = json.loads(p.read_text())
        if req.get('stage') not in ('development', 'unseen') or req.get('source_sha256') != sha:
            continue
        state = json.loads(p.with_name('state.json').read_text())
        if state.get('phase') != 'finished':
            raise ValueError('Incomplete source-matching Stage1 request')
        if req.get('benchmark') != 'robosuite' or req.get('suite') != suite or req.get('task_id') != 0 or \
           req.get('init_mode') != 'saved' or req.get('max_steps') != 1000 or req.get('camera_width') != 800 or \
           req.get('camera_height') != 512 or req.get('workers') != 1:
            raise ValueError('Stage1 settings mismatch')
        if req['stage'] in measured:
            raise ValueError('Duplicate source-matching Stage1 partition measurement')
        wanted = list(range(101, 126)) if req['stage'] == 'development' else list(range(126, 131))
        if req['seeds'] != wanted or state.get('completed_seeds') != wanted or \
           sorted(o['seed'] for o in state.get('outcomes', [])) != wanted:
            raise ValueError('Incomplete development/unseen source coverage')
        for outcome in state['outcomes']:
            run = (task / outcome['relative_run']).resolve()
            if not run.is_relative_to((task / 'debug').resolve()) or digest(run / 'source/program.py') != sha:
                raise ValueError('Stage1 evidence provenance mismatch')
            metadata = json.loads((run / 'run.json').read_text())
            required = dict(status='finalized', benchmark='robosuite', suite=suite,
                            task_id=0, seed=outcome['seed'], init_mode='saved')
            if any(metadata.get(k) != v for k, v in required.items()) or any(
                metadata.get('capture', {}).get(k) != v for k, v in
                dict(max_steps=1000, camera_width=800, camera_height=512, videos=True).items()):
                raise ValueError('Stage1 run identity/capture settings mismatch')
        measured[req['stage']] = p.parent.name
    if set(measured) != {'development', 'unseen'}:
        raise ValueError('Full25 development and exact-once frozen5 unseen are required')
    return measured


def wait_capacity(root, status_path):
    while True:
        stat = os.statvfs(root); disk = stat.f_bavail * stat.f_frsize
        mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        headroom = int(mem['MemAvailable'].split()[0]) * 1024
        for base, current, maximum in ((Path('/sys/fs/cgroup'), 'memory.current', 'memory.max'),
                (Path('/sys/fs/cgroup/memory'), 'memory.usage_in_bytes', 'memory.limit_in_bytes')):
            if (base / current).exists() and (base / maximum).exists():
                limit = (base / maximum).read_text().strip()
                if limit != 'max':
                    headroom = min(headroom, int(limit) - int((base / current).read_text()))
                break
        info = dict(disk_free_bytes=disk, memory_headroom_bytes=headroom,
                    phase='admitted' if min(disk, headroom) >= 3 * 1024**3 else 'waiting_resources',
                    checked_at=time.time())
        atomic(status_path, info)
        if info['phase'] == 'admitted':
            return
        time.sleep(20)


def guarded_argv(argv, suite, task_id, sha, task, expected_run_id):
    """Accept only the exact single-seed argv emitted by official run_validation.py."""
    if not argv or argv[0] != 'run' or argv.count('--flat-run-dir') != 1:
        raise ValueError('Only fresh single-seed official validation is allowed')
    values = {}; index = 1
    while index < len(argv):
        flag = argv[index]
        if flag in values:
            raise ValueError('Duplicate command option')
        if flag == '--flat-run-dir':
            values[flag] = True; index += 1
        else:
            if index + 1 >= len(argv):
                raise ValueError('Missing command option value')
            values[flag] = argv[index + 1]; index += 2
    fixed = {'--benchmark': 'robosuite', '--suite': suite, '--task-id': str(task_id),
             '--max-steps': '1000', '--camera-width': '800', '--camera-height': '512',
             '--init-mode': 'saved', '--flat-run-dir': True}
    if set(values) != set(fixed) | {'--program', '--output-root', '--seed'} or \
       any(values.get(k) != v for k, v in fixed.items()):
        raise ValueError('Official validation arguments changed')
    seed = int(values['--seed'])
    if seed not in SEEDS or Path(values['--program']).resolve() != (task / 'fix_code.py').resolve() or \
       digest(values['--program']) != sha or Path(values['--output-root']).resolve() != \
       (task / 'validation/runs' / expected_run_id / 'results').resolve():
        raise ValueError('Validation source, seed or output path changed')
    return seed


def run_guard(args):
    import fcntl
    root = args.run_root.resolve(); task = task_path(root, args.suite, args.task_id)
    rid = run_id(identity(args.suite, args.task_id, args.source_sha256))
    seed = guarded_argv(args.harness_argv, args.suite, args.task_id, args.source_sha256, task, rid)
    state = json.loads((task / '.heldout' / rid / 'state.json').read_text())
    if state.get('phase') != 'running' or state.get('source_sha256') != args.source_sha256:
        raise ValueError('No active root-owned formal evaluation permits this seed')
    owner = json.loads(Path('/mnt/aspire-work/episode.lock').read_text())
    expected_owner = state['process_identity']
    if owner.get('run_id') != rid or any(owner.get(k) != expected_owner[k] for k in ('pid', 'start_ticks', 'boot_id')):
        raise ValueError('Formal seed lacks matching root episode-lock identity')
    with Path('/mnt/aspire-work/episode.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            fcntl.flock(lock, fcntl.LOCK_UN)
            raise ValueError('Formal group lock is no longer held')
    claim_dir = task / '.heldout' / rid / 'seed_claims'; claim_dir.mkdir(parents=True, exist_ok=True)
    wait_capacity(root, claim_dir / f'{seed:04d}_admission.json')
    claim_path = claim_dir / f'{seed:04d}.json'
    value = dict(seed=seed, run_id=rid, source_sha256=args.source_sha256,
                 identity=process_identity(), phase='reserved', reserved_at=time.time())
    with claim_path.open('x') as f:
        json.dump(value, f); f.flush(); os.fsync(f.fileno())
    command = ['timeout', '900', str(REPO / '.venv-robosuite/bin/cap-harness'), *args.harness_argv]
    child = subprocess.Popen(command, env=os.environ.copy())
    value.update(phase='running', child_identity=process_identity(child.pid), command=command)
    try:
        atomic(claim_path, value)
        code = child.wait()
    finally:
        if child.poll() is None:
            child.wait()
    value.update(phase='exited', exit_code=code, finished_at=time.time())
    atomic(claim_path, value)
    return code


def run_validation(args):
    import fcntl
    root = args.run_root.resolve(); task = task_path(root, args.suite, args.task_id)
    gate = Path(args.gate or root / 'execution-ready.json')
    execution_gate(root, gate, args.suite, args.task_id)
    measured = validate_handoff(root, task, args.suite, args.source_sha256)
    expected = identity(args.suite, args.task_id, args.source_sha256); rid = run_id(expected)
    owned = task / '.heldout' / rid
    owned.mkdir(parents=True, exist_ok=True)
    if not args.execute:
        print(json.dumps(dict(phase='prepared_no_execution', run_id=rid,
                              identity=expected, measured_requests=measured)), flush=True)
        return 0
    state_path = owned / 'state.json'; claim_path = owned / 'launch_claim.json'
    with (owned / 'launch.lock').open('a') as launch_lock:
        fcntl.flock(launch_lock, fcntl.LOCK_EX)
        if claim_path.exists():
            print(json.dumps(dict(phase='existing_claim_no_relaunch', claim=json.loads(claim_path.read_text()))), flush=True)
            return 0
        manifest_path = task / 'validation/runs' / rid / 'manifest.json'
        if manifest_path.exists() or any((task / 'validation').glob('runs/*/manifest.json')):
            raise ValueError('Existing formal evidence without matching durable claim; root inspection required')
        state = dict(phase='claiming_gpu', run_id=rid, identity=expected,
                     process_identity=process_identity(), source_sha256=args.source_sha256,
                     started_at=time.time(), measured_requests=measured, workers=1,
                     execution_mode='fresh_per_seed', original_per_seed_timeout_seconds=900)
        with claim_path.open('x') as f:
            json.dump(state, f); f.flush(); os.fsync(f.fileno())
        atomic(state_path, state)
    lock = Path('/mnt/aspire-work/episode.lock').open('a+')
    acquired = False; child = None
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); acquired = True
        execution_gate(root, gate, args.suite, args.task_id)
        lock.seek(0); lock.truncate()
        lock.write(json.dumps(dict(owner='robosuite', run_root=str(root), run_id=rid,
                                   **state['process_identity'])))
        lock.flush(); os.fsync(lock.fileno())
        wrapper = owned / 'guarded-cap-harness'
        # Root-owned wrapper only; worker shell strings are never consumed.
        prefix = [str(REPO / '.venv-robosuite/bin/python'), str(Path(__file__).resolve()),
                  '--guarded-cap', '--run-root', str(root), '--suite', args.suite,
                  '--task-id', str(args.task_id), '--source-sha256', args.source_sha256, '--']
        wrapper.write_text('#!/bin/sh\nexec ' + shlex.join(prefix) + ' "$@"\n'); wrapper.chmod(0o700)
        command = [str(REPO / '.venv-robosuite/bin/python'),
                   str(REPO / '.claude/skills/iterative-debugging/scripts/run_validation.py'),
                   '--benchmark', 'robosuite', '--suite', args.suite, '--task-id', str(args.task_id),
                   '--gpu', '0', '--run-root', str(root), '--program', str(task / 'fix_code.py'),
                   '--cap-harness', str(wrapper), '--init-mode', 'saved', '--max-steps', '1000',
                   '--camera-width', '800', '--camera-height', '512', '--workers', '1',
                   '--seeds', *map(str, SEEDS)]
        runtime = json.loads(Path('/mnt/aspire-work/runtime-env.json').read_text())
        env = {**os.environ, **runtime, 'CUDA_VISIBLE_DEVICES': '0', 'MUJOCO_EGL_DEVICE_ID': '0',
               'CAP_HARNESS_ROBOSUITE_GPU': '0', 'MUJOCO_GL': 'egl',
               'PYOPENGL_PLATFORM': 'egl', 'EGL_PLATFORM': 'device'}
        with (owned / 'evaluation.log').open('a') as log:
            state.update(phase='running', child_identity=None, command=command)
            atomic(state_path, state)
            child = subprocess.Popen(command, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT)
            state.update(phase='running', child_identity=process_identity(child.pid), command=command)
            atomic(state_path, state)
            atomic(root / 'gpu-ledger.json', dict(state, owner='robosuite', episode_running=True, gpu=0))
            code = child.wait()
        manifest = json.loads(manifest_path.read_text())
        if manifest['identity'] != expected or digest(task / 'fix_code.py') != args.source_sha256:
            raise ValueError('Formal evaluation identity changed')
        state.update(phase='finished' if manifest['status'] == 'complete' and manifest['trials'] == 100 else 'partial',
                     exit_code=code, manifest=str(manifest_path), trials=manifest['trials'],
                     passes=manifest['passes'], pass_rate=manifest['pass_rate'], finished_at=time.time())
    except BaseException as error:
        state.update(phase='runner_error' if acquired else 'gpu_lock_unavailable',
                     error_type=type(error).__name__, finished_at=time.time())
        raise
    finally:
        if child is not None and child.poll() is None:
            child.wait()
        atomic(state_path, state)
        if acquired:
            atomic(root / 'gpu-ledger.json', dict(state, owner='robosuite', episode_running=False, gpu=0))
        lock.close()
    print(json.dumps(state), flush=True)
    return code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root', required=True, type=Path)
    p.add_argument('--suite', required=True, choices=sorted(SUITES))
    p.add_argument('--task-id', default=0, type=int)
    p.add_argument('--source-sha256', required=True)
    p.add_argument('--gate', type=Path)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--guarded-cap', action='store_true')
    p.add_argument('harness_argv', nargs=argparse.REMAINDER)
    args = p.parse_args()
    if args.harness_argv[:1] == ['--']:
        args.harness_argv = args.harness_argv[1:]
    if len(args.source_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.source_sha256):
        p.error('Exact lowercase SHA256 required')
    return run_guard(args) if args.guarded_cap else run_validation(args)


if __name__ == '__main__':
    raise SystemExit(main())
