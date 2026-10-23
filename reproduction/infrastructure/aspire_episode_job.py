"""Coordinator-only remote episode runner, with completion record and artifact archive."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import shlex
import subprocess
import tarfile
import time

def package_artifacts(archive_path, paths, task, request):
    task_root = task.resolve()
    with tarfile.open(archive_path, 'w:gz', compresslevel=1) as archive:
        for p in paths:
            if request.get('artifact_transport') == 'incremental_dev_stream' and p == Path(request['output_root']).resolve():
                # Completed seed trees are independently streamed to the coordinator.
                archive.add(p,arcname=str(p.relative_to(task_root)),recursive=False)
                for child in p.iterdir():
                    if child.name not in {f'{seed:04d}' for seed in request['seeds']}:
                        archive.add(child,arcname=str(child.relative_to(task_root)))
            else:
                archive.add(p, arcname=str(p.relative_to(task_root)))

parser = argparse.ArgumentParser()
parser.add_argument('--task-id', type=int, required=True)
parser.add_argument('--tag', required=True)
parser.add_argument('--task-dir', type=Path)
args = parser.parse_args()
w = Path('/mnt/aspire-work')
repo = w / 'ASPIRE'
root = Path((w / 'run-root.txt').read_text().strip())
task = args.task_dir or root / 'libero-pro/libero_goal_swap' / f'task_{args.task_id}'
task.resolve().relative_to(root.resolve())
lock = (w / 'episode.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
request = json.loads((task / 'requested_runs.json').read_text())
command = request['command']
argv = shlex.split(command.split(' && ', 1)[-1])
env = {**os.environ, **json.loads((w / 'runtime-env.json').read_text())}
status_path = w / f'job-{args.tag}.json'
archive_path = w / f'job-{args.tag}-artifacts.tar.gz'
status = {'task_id': args.task_id, 'tag': args.tag, 'phase': 'running',
          'seeds': request.get('seeds'), 'started': time.time(), 'pid': os.getpid()}
status_path.write_text(json.dumps(status, indent=2))
(root / 'gpu-ledger.json').write_text(json.dumps({**status, 'gpu': 0, 'episode_running': True}, indent=2))
try:
    if request.get('execution_mode') == 'fresh_per_seed':
        status['execution_mode'] = 'fresh_per_seed'
        status['completed_seeds'] = []
        log_dir = Path(argv[argv.index('--log-dir') + 1])
        log_dir.relative_to(task)
        log_dir.mkdir(parents=True, exist_ok=True)
        output_root = Path(request['output_root'])
        exit_code = 0
        for seed in request['seeds']:
            one = ['timeout', '600', str(repo/'.venv-libero/bin/cap-harness'), 'run',
                   '--benchmark', 'libero-pro', '--suite', 'libero_goal_swap',
                   '--task-id', str(args.task_id), '--seed', str(seed),
                   '--program', request['program'], '--output-root', str(output_root),
                   '--max-steps', '1000', '--init-mode', 'seeded', '--flat-run-dir']
            with (log_dir/f'seed_{seed:02d}.log').open('w') as log:
                one_result = subprocess.run(one, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
            if one_result.returncode:
                exit_code = one_result.returncode
            status['completed_seeds'].append(seed)
            status_path.write_text(json.dumps(status, indent=2))
            print(json.dumps({'completed_seed': seed, 'exit_code': one_result.returncode}), flush=True)
        outcome = subprocess.CompletedProcess([], exit_code)
    else:
        outcome = subprocess.run(argv, cwd=repo, env=env, check=False)
    paths = []
    for option in ('--output-root', '--log-dir'):
        if option in argv:
            p = Path(argv[argv.index(option) + 1]).resolve()
            p.relative_to(task.resolve())
            if p.exists() and p not in paths:
                paths.append(p)
    status['activity'] = 'packaging'
    status_path.write_text(json.dumps(status, indent=2))
    package_artifacts(archive_path, paths, task, request)
    status.update(phase='finished', exit_code=outcome.returncode,
                  finished=time.time(), archive=str(archive_path),
                  archive_bytes=archive_path.stat().st_size)
except BaseException as exc:
    status.update(phase='runner_error', error=repr(exc), finished=time.time())
    raise
finally:
    status_path.write_text(json.dumps(status, indent=2))
    (root / 'gpu-ledger.json').write_text(json.dumps({**status, 'gpu': 0, 'episode_running': False}, indent=2))
    print(json.dumps(status), flush=True)
