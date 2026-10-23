"""Root-owned Robosuite episode job. No imports connect or launch anything.

The controller installs this exact file remotely. Every request has a durable launch
claim and separate source copy; a killed/ambiguous job is never automatically replayed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

SUITES = {'cube_lifting', 'cube_restack', 'cube_stack', 'nut_assembly',
          'spill_wipe', 'two_arm_lift', 'two_arm_handover'}
DEV = list(range(101, 126))
UNSEEN = list(range(126, 131))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def scoped(root, value):
    root = Path(root).resolve()
    path = Path(value)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError('Path must be strictly inside its owning root')
    return path


def validate_settings(request, suite, task_id):
    required = {'benchmark': 'robosuite', 'suite': suite, 'task_id': task_id,
                'init_mode': 'saved', 'max_steps': 1000, 'camera_width': 800,
                'camera_height': 512, 'workers': 1, 'gpu': 0}
    if suite not in SUITES or task_id != 0:
        raise ValueError('Only the seven official task_id 0 suites are supported')
    for key, expected in required.items():
        if type(request.get(key)) is not type(expected) or request[key] != expected:
            raise ValueError(f'Invalid official setting: {key}')
    seeds = request.get('seeds')
    if not isinstance(seeds, list) or any(type(s) is not int for s in seeds):
        raise ValueError('Seeds must be an integer list')
    if seeds not in ([101], DEV, UNSEEN):
        raise ValueError('Use pilot 101, complete dev 101-125, or unseen 126-130')
    if not isinstance(request.get('failure_mode'), str) or not request['failure_mode'].strip():
        raise ValueError('failure_mode is required')


def enforce_history(request, history, source_hash, observation_only):
    """Count reservations, including interrupted jobs, before any execution."""
    sources = {}
    for old in history:
        if old['program'] == request['program'] and old['source_sha256'] != source_hash:
            raise ValueError('Numbered source was edited; write a new immutable version')
        if old.get('stage') == 'unseen':
            raise ValueError('No further policy requests after unseen reservation')
        if not old.get('observation_only'):
            sources.setdefault(old['source_sha256'], old['failure_mode'])
    mode = request['failure_mode']
    if source_hash in sources and sources[source_hash] != mode:
        raise ValueError('Cannot relabel a source to reset its failure-mode budget')
    if not observation_only and source_hash not in sources:
        if len(sources) >= 8 or sum(m == mode for m in sources.values()) >= 3:
            raise ValueError('Official policy budget exhausted (8 total / 3 per mode)')
    seeds = request['seeds']
    if observation_only:
        if seeds != [101]:
            raise ValueError('Observation-only exploration is limited to seed101')
        return 'observe'
    if seeds == [101]:
        return 'pilot'
    pilots = [h for h in history if h.get('stage') == 'pilot' and
              h['source_sha256'] == source_hash and h.get('phase') == 'artifacts_ready' and
              len(h.get('outcomes', [])) == 1 and
              h['outcomes'][0].get('seed') == 101 and
              type(h['outcomes'][0].get('program_ok')) is bool and
              type(h['outcomes'][0].get('task_success')) is bool]
    if not pilots:
        raise ValueError('Same frozen source needs completed, backed-up pilot101 before expansion')
    if seeds == DEV:
        return 'development'
    if not any(h.get('stage') == 'development' and h['source_sha256'] == source_hash and
               h.get('phase') == 'artifacts_ready' and
               {o['seed'] for o in h.get('outcomes', [])} == set(DEV) for h in history):
        raise ValueError('Frozen source needs all 25 development outcomes before unseen')
    return 'unseen'


def reused_pilot_outcome(prior, reuse, source_hash):
    """A completed scientific failure is scored unchanged, never replayed."""
    outcomes = prior.get('outcomes', [])
    if (prior.get('phase') != 'finished' or prior.get('source_sha256') != source_hash or
            prior.get('seeds') != [101] or len(outcomes) != 1):
        raise ValueError('Pilot101 provenance is not a completed matching request')
    pilot = outcomes[0]
    if (pilot.get('seed') != 101 or type(pilot.get('program_ok')) is not bool or
            type(pilot.get('task_success')) is not bool):
        raise ValueError('Pilot101 lacks a finalized scientific outcome')
    if {k: v for k, v in reuse.items() if k != 'from_request_id'} != pilot:
        raise ValueError('Reused pilot101 outcome differs from its original result')
    return pilot


def gate_check(run_root, gate_path, suite, task_id):
    gate_path = scoped(run_root, gate_path)
    gate = json.loads(gate_path.read_text())
    expected = {'benchmark': 'robosuite', 'owner': 'robosuite',
                'launch_enabled': True, 'gpu': 0}
    if any(type(gate.get(k)) is not type(v) or gate.get(k) != v for k, v in expected.items()):
        raise ValueError('Root execution-ready gate has not granted this campaign GPU ownership')
    if Path(gate.get('run_root', '')).resolve() != Path(run_root).resolve():
        raise ValueError('Execution-ready gate belongs to a different campaign path')
    if gate.get('suite', suite) != suite or gate.get('task_id', task_id) != task_id:
        raise ValueError('Execution-ready gate belongs to a different task')
    return gate


def proc_identity(pid=None):
    pid = pid or os.getpid()
    base = Path('/proc') / str(pid)
    stat = (base / 'stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'start_ticks': stat[19],
            'command': (base / 'cmdline').read_bytes().replace(b'\0', b' ').decode(),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def admission(root, state, state_path):
    """Pause admissions on constrained storage/memory; retain identity and lock."""
    while True:
        disk = os.statvfs(root)
        disk_free = disk.f_bavail * disk.f_frsize
        meminfo = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        headroom = int(meminfo['MemAvailable'].split()[0]) * 1024
        for base, used, limit in ((Path('/sys/fs/cgroup'), 'memory.current', 'memory.max'),
                                  (Path('/sys/fs/cgroup/memory'), 'memory.usage_in_bytes', 'memory.limit_in_bytes')):
            if (base / limit).exists() and (base / used).exists():
                maximum = (base / limit).read_text().strip()
                if maximum != 'max':
                    headroom = min(headroom, int(maximum) - int((base / used).read_text()))
                break
        state['resource_admission'] = dict(disk_free_bytes=disk_free,
                                           memory_headroom_bytes=headroom, checked_at=time.time())
        if min(disk_free, headroom) >= 3 * 1024**3:
            state['activity'] = 'admitted'
            atomic(state_path, state)
            return
        state['activity'] = 'waiting_resource_headroom'
        atomic(state_path, state)
        time.sleep(20)


def episode_environment(runtime):
    # Runtime exports normally already contain CUDA/EGL selections. Mapping
    # unpacking deliberately overrides them without duplicate-keyword errors.
    return {**os.environ, **runtime, 'CUDA_VISIBLE_DEVICES': '0',
            'MUJOCO_EGL_DEVICE_ID': '0', 'CAP_HARNESS_ROBOSUITE_GPU': '0'}


def run_job(args):
    import fcntl
    root = args.run_root.resolve()
    task = scoped(root, root / 'robosuite' / args.suite / f'task_{args.task_id}')
    job = scoped(task, args.request_dir)
    request_path = job / 'request.json'
    request = json.loads(request_path.read_text())
    if hashlib.sha256(canonical(request)).hexdigest() != job.name:
        raise ValueError('Immutable request identity mismatch')
    validate_settings(request, args.suite, args.task_id)
    source = job / 'program.py'
    if digest(source) != request['source_sha256']:
        raise ValueError('Frozen source SHA mismatch')
    state_path = job / 'state.json'
    # State creation is exclusive. A job with prior state must never execute twice.
    with state_path.open('x', encoding='utf-8') as f:
        json.dump({'phase': 'claiming_gpu', 'request_id': job.name,
                   'identity': proc_identity(), 'started_at': time.time()}, f)
    state = json.loads(state_path.read_text())
    state.update(source_sha256=request['source_sha256'], seeds=request['seeds'],
                 completed_seeds=[], outcomes=[], suite=args.suite, task_id=args.task_id)
    lock = Path('/mnt/aspire-work/episode.lock').open('a+')
    acquired = False
    child = None
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
        gate_check(root, args.gate, args.suite, args.task_id)
        lock.seek(0); lock.truncate()
        lock.write(json.dumps({'owner': 'robosuite', 'run_root': str(root),
                               'request_id': job.name, **state['identity']}))
        lock.flush(); os.fsync(lock.fileno())
        state.update(phase='running', episode_running=True)
        atomic(state_path, state)
        atomic(root / 'gpu-ledger.json', dict(state, owner='robosuite', gpu=0))
        repo = Path('/mnt/aspire-work/ASPIRE')
        runtime = json.loads(Path('/mnt/aspire-work/runtime-env.json').read_text())
        env = episode_environment(runtime)
        output = scoped(task, request['output_root'])
        output.mkdir(parents=True, exist_ok=True)
        existing = list(output.rglob('run.json'))
        reuse = request.get('reuse_pilot101')
        if reuse:
            if request['seeds'] != DEV or request['stage'] != 'development':
                raise ValueError('Pilot101 reuse is restricted to its full development sweep')
            prior = json.loads((task / '.requests' / reuse['from_request_id'] / 'state.json').read_text())
            pilot = reused_pilot_outcome(prior, reuse, request['source_sha256'])
            run = scoped(task, pilot['relative_run'])
            if existing != [run / 'run.json'] or digest(run / 'source/program.py') != request['source_sha256']:
                raise ValueError('Output root has unrelated runs or pilot source drift')
            state['completed_seeds'].append(101)
            state['outcomes'].append(dict(pilot, reused_from_request_id=reuse['from_request_id']))
            atomic(state_path, state)
        elif existing:
            raise ValueError('Output root already has run evidence; never overwrite or replay')
        logs = job / 'logs'; logs.mkdir()
        for seed in request['seeds']:
            if reuse and seed == 101:
                continue
            admission(root, state, state_path)
            # Fresh interpreter per seed; the group lock stays held until all finish.
            command = ['timeout', '900', str(repo / '.venv-robosuite/bin/cap-harness'),
                       'run', '--benchmark', 'robosuite', '--suite', args.suite,
                       '--task-id', str(args.task_id), '--seed', str(seed),
                       '--program', str(source), '--output-root', str(output),
                       '--max-steps', '1000', '--init-mode', 'saved',
                       '--camera-width', '800', '--camera-height', '512', '--flat-run-dir']
            if request['stage'] == 'observe':
                command.append('--no-videos')
            with (logs / f'seed_{seed:04d}.log').open('w') as log:
                child = subprocess.Popen(command, cwd=repo, env=env, stdout=log,
                                         stderr=subprocess.STDOUT)
                state.update(current_seed=seed, child_identity=proc_identity(child.pid),
                             command=command)
                atomic(state_path, state)
                atomic(root / 'gpu-ledger.json', dict(state, owner='robosuite', gpu=0))
                code = child.wait()
            seed_root = output / f'{seed:04d}'
            runs = list(seed_root.rglob('run.json'))
            if len(runs) != 1:
                raise RuntimeError(f'Seed {seed} lacks exactly one finalized run; do not replay')
            run = runs[0].parent
            meta = json.loads((run / 'run.json').read_text())
            if meta.get('status') != 'finalized' or digest(run / 'source/program.py') != request['source_sha256']:
                raise ValueError('Unfinalized run or source mismatch')
            outcome = json.loads((run / 'outcome.json').read_text())
            row = {'seed': seed, 'program_ok': outcome.get('program_ok'),
                   'task_success': outcome.get('task_success'), 'exit_code': code,
                   'relative_run': run.relative_to(task).as_posix()}
            state['outcomes'].append(row)
            state['completed_seeds'].append(seed)
            state['child_identity'] = None
            atomic(state_path, state)
            print(json.dumps(row), flush=True)
        state.update(phase='finished', finished_at=time.time())
    except BaseException as error:
        state.update(phase='runner_error' if acquired else 'gpu_lock_unavailable',
                     error_type=type(error).__name__, error=str(error), finished_at=time.time())
        raise
    finally:
        # Keep the group lock if a bookkeeping failure happened after child launch.
        # Its original timeout still bounds the run; never admit another simulator.
        if child is not None and child.poll() is None:
            child.wait()
        state.update(episode_running=False)
        atomic(state_path, state)
        if acquired:
            atomic(root / 'gpu-ledger.json', dict(state, owner='robosuite', gpu=0))
        lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', required=True, type=Path)
    parser.add_argument('--suite', required=True, choices=sorted(SUITES))
    parser.add_argument('--task-id', type=int, default=0)
    parser.add_argument('--request-dir', required=True, type=Path)
    parser.add_argument('--gate', required=True)
    run_job(parser.parse_args())


if __name__ == '__main__':
    main()
