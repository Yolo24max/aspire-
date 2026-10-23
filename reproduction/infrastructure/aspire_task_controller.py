"""Root-owned single-GPU request queue; workers only write task-local requests."""
import hashlib
import argparse
import json
from pathlib import Path, PurePosixPath
import shlex
import tarfile
import time
from aspire_policy_budget import check_budget, is_observation_only

# Reuse the audited connection bootstrap. Password stays in process memory only.
bootstrap = Path(__file__).with_name('aspire_remote.py').read_text(encoding='utf-8').split('\ntry:\n    for line in sys.stdin:')[0]
exec(compile(bootstrap, str(Path(__file__).with_name('aspire_remote.py')), 'exec'))

parser = argparse.ArgumentParser()
parser.add_argument('--task-id', type=int, default=0)
parser.add_argument('--local-task-dir', type=Path)
parser.add_argument('--server-task-dir')
parser.add_argument('--verification', action='store_true')
parser.add_argument('--incremental-artifacts', action='store_true')
parser.add_argument('--max-policy-versions', type=int)
parser.add_argument('--prepare-task-dir', action='store_true')
parser.add_argument('--run-existing-request', action='store_true',
                    help='Retry only a locally rejected pre-launch request after root inspection')
options = parser.parse_args()

def open_transfer_sftp():
    return paramiko.SFTPClient.from_transport(client.get_transport(),
                                             window_size=16 * 1024 * 1024,
                                             max_packet_size=64 * 1024)

local_task = Path('C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap') / f'task_{options.task_id}'
remote_task = PurePosixPath('/mnt/aspire-work/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap') / f'task_{options.task_id}'
if options.local_task_dir:
    local_task = options.local_task_dir.resolve()
if options.server_task_dir:
    remote_task = PurePosixPath(options.server_task_dir)
remote_task.relative_to('/mnt/aspire-work/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server')
local_task.mkdir(parents=True, exist_ok=True)
status_file = local_task / 'coordinator_status.json'
history_file = local_task / 'coordinator_history.jsonl'
request_file = local_task / 'requested_runs.json'
mode_path = Path('C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/validation-artifacts/execution-mode.json')
fresh_processes = mode_path.exists() and json.loads(mode_path.read_text(encoding='utf-8'))['mode'] == 'fresh_per_seed'
seen = {hashlib.sha256(request_file.read_bytes()).hexdigest()} if request_file.exists() else set()
if options.run_existing_request:
    assert request_file.exists()
    prior = json.loads(status_file.read_text(encoding='utf-8'))
    assert prior['phase'] == 'controller_error'
    history_hashes = {json.loads(line)['request_hash'] for line in history_file.read_text(encoding='utf-8').splitlines()} if history_file.exists() else set()
    assert not (seen & history_hashes), 'Existing request already has completed artifacts'
    seen.clear()

def save_status(status):
    temporary = status_file.with_suffix('.pending')
    temporary.write_text(json.dumps(status, indent=2), encoding='utf-8')
    # Windows readers (including a worker polling this file) can briefly hold
    # the destination open and make os.replace raise PermissionError. The
    # durable history and episode must not be retried because of that race.
    for attempt in range(50):
        try:
            temporary.replace(status_file)
            break
        except PermissionError:
            if attempt == 49:
                raise
            time.sleep(0.1)
    print(json.dumps(status), flush=True)

def remote_python(source):
    stdin, stdout, stderr = client.exec_command('python3 -u -', timeout=30)
    stdin.write(source)
    stdin.flush()
    stdin.channel.shutdown_write()
    stdout.channel.settimeout(180)
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    code = stdout.channel.recv_exit_status()
    if code:
        raise RuntimeError(f'remote error {code}: {error} {output}')
    return output

def stream_artifact_tree(relative, archive_path, expected_source_hash):
    """Copy, hash-check, and verify a finalized seed before freeing its server payload."""
    relative = PurePosixPath(relative)
    assert not relative.is_absolute() and '..' not in relative.parts
    remote_archive = '/mnt/aspire-work/' + archive_path.name
    code = f'''from pathlib import Path
import hashlib,json,tarfile
task=Path({str(remote_task)!r});source=task/{str(relative)!r}
assert source.resolve().is_relative_to(task.resolve()) and source.is_dir()
target=Path({remote_archive!r})
with tarfile.open(target,mode='w:gz',compresslevel=1) as archive:
 archive.add(source,arcname={str(relative)!r})
h=hashlib.sha256()
with target.open('rb') as handle:
 for chunk in iter(lambda:handle.read(8*1024*1024),b''):h.update(chunk)
print(json.dumps({{'bytes':target.stat().st_size,'sha256':h.hexdigest()}}))
'''
    expected = json.loads(remote_python(code))
    partial = archive_path.with_suffix('.gz.partial')
    with open_transfer_sftp() as sftp:
        sftp.get(remote_archive, str(partial))
    digest = hashlib.sha256()
    with partial.open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    assert partial.stat().st_size == expected['bytes']
    assert digest.hexdigest() == expected['sha256'], 'Remote/local seed archive hash mismatch'
    partial.replace(archive_path)
    with tarfile.open(archive_path) as archive:
        archive.extractall(local_task, filter='data')

    local_seed = local_task / str(relative)
    run_dirs = sorted(p.parent for p in local_seed.rglob('run.json'))
    assert run_dirs, f'No finalized run in backed-up seed tree: {relative}'
    payloads = []
    verified_bytes = 0
    verified_files = 0
    retained = {'run.json', 'outcome.json', 'manifest.json', 'episode/reset.json',
                'source/program.py', 'source/program-result.json', 'source/program-error.json',
                'trace/events.jsonl'}
    for run_dir in run_dirs:
        metadata = json.loads((run_dir / 'run.json').read_text(encoding='utf-8'))
        assert metadata['status'] == 'finalized'
        assert hashlib.sha256((run_dir / 'source/program.py').read_bytes()).hexdigest() == expected_source_hash
        manifest = json.loads((run_dir / 'manifest.json').read_text(encoding='utf-8'))
        for item in manifest['files']:
            item_path = run_dir / item['path']
            assert item_path.resolve().is_relative_to(run_dir.resolve()) and not item_path.is_symlink()
            assert item_path.stat().st_size == item['size_bytes']
            item_digest = hashlib.sha256()
            with item_path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
                    item_digest.update(chunk)
            assert item_digest.hexdigest() == item['sha256'], str(item_path)
            verified_bytes += item['size_bytes']
            verified_files += 1
            if item['path'] not in retained:
                payloads.append((run_dir.relative_to(local_task).as_posix() + '/' + item['path']))
    # The archive, every published file hash, and selected source were checked
    # before any remote payload is removed. Keep metadata for later inspection.
    retire = f'''from pathlib import Path
import json
task=Path({str(remote_task)!r});paths={payloads!r};removed=0
for relative in paths:
 p=task/relative
 assert p.resolve().is_relative_to(task.resolve()) and not p.is_symlink()
 if p.is_file():
  removed+=p.stat().st_size;p.unlink()
print(json.dumps({{'removed_payload_bytes':removed}}))
'''
    removed = json.loads(remote_python(retire))
    with open_transfer_sftp() as sftp:
        sftp.remove(remote_archive)
    return {'relative':str(relative),'archive':str(archive_path),
            'bytes':archive_path.stat().st_size,'sha256':digest.hexdigest(),
            'verified_bytes':verified_bytes,'verified_files':verified_files,
            **removed}

def check_policy_partition_request(seeds, history, source_hash):
    """Reject an irreversible partition violation before launching an episode."""
    assert all(type(seed) is int for seed in seeds)
    assert len(seeds) == len(set(seeds)), 'Duplicate seed request'
    unseen = set(range(66, 81))
    assert not any(set(row['seeds']) & unseen for row in history), 'No policy requests after unseen evaluation'
    selected = set(seeds)
    assert selected in ({51}, set(range(51, 66)), unseen), 'Use pilot51 or a complete fifteen-seed partition'
    if selected == unseen:
        assert any(set(row['seeds']) == set(range(51, 66)) and
                   row['source_hash'] == source_hash and row['phase'] == 'artifacts_ready'
                   for row in history), 'Frozen source needs complete measured development before unseen'

def validate(request):
    assert request['benchmark'] == 'libero-pro'
    assert request['suite'] == 'libero_goal_swap'
    assert request['task_id'] == options.task_id
    assert request['init_mode'] == 'seeded'
    assert request['max_steps'] == 1000 and request['gpu'] == 0
    assert request['workers'] in (1, 4)
    allowed_seeds = set(range(51,56)) if options.verification else set(range(51,81))
    assert request['seeds'] and set(request['seeds']) <= allowed_seeds
    program = PurePosixPath(request['program'])
    relative_program = program.relative_to(remote_task)
    assert relative_program.parts[0] == 'code'
    if not options.verification:
        history = [json.loads(line) for line in history_file.read_text(encoding='utf-8').splitlines()] if history_file.exists() else []
        source_hash = hashlib.sha256((local_task / str(relative_program)).read_bytes()).hexdigest()
        check_policy_partition_request(request['seeds'], history, source_hash)
    output = PurePosixPath(request['output_root'])
    output.relative_to(remote_task / 'debug')
    command = shlex.split(request['command'].split(' && ', 1)[-1])
    log = PurePosixPath(command[command.index('--log-dir') + 1])
    log.relative_to(remote_task / 'debug/logs')
    # Construct the executable argv ourselves; shell text is never executed.
    argv = ['timeout', '600', '/mnt/aspire-work/ASPIRE/.venv-libero/bin/cap-harness',
            'run-batch', '--benchmark', 'libero-pro', '--suite', 'libero_goal_swap',
            '--task-id', str(options.task_id), '--seeds', *map(str, request['seeds']),
            '--program', str(program), '--output-root', str(output),
            '--flat-run-dir', '--init-mode', 'seeded', '--workers', str(request['workers']),
            '--max-steps', '1000', '--log-dir', str(log),
            '--results-jsonl', str(output / 'results.jsonl')]
    request['command'] = shlex.join(argv)
    if fresh_processes:
        request['execution_mode'] = 'fresh_per_seed'
        request['workers'] = 1
    if options.incremental_artifacts:
        assert fresh_processes, 'Incremental evidence copying requires fresh serial processes'
        request['artifact_transport'] = 'incremental_dev_stream'
    if not options.verification and any(s != 51 for s in request['seeds']):
        outcomes = local_task.glob('debug/**/outcome.json')
        passed_first = False
        for p in outcomes:
            if p.is_relative_to(local_task/'debug/explore'):
                continue
            record = json.loads(p.read_text(encoding='utf-8'))
            if '0051' in p.parts and record.get('task_success') and record.get('program_ok'):
                passed_first = True
                break
        assert passed_first, 'First development seed must succeed before expansion'
    return relative_program

if options.prepare_task_dir:
    preflight = remote_python('from pathlib import Path\nimport json,urllib.request,subprocess\np=Path(' + repr(str(remote_task)) + ')\np.mkdir(parents=True,exist_ok=True)\n(p/"code").mkdir(exist_ok=True)\nchecks={}\nfor port in (8114,8115,8116,8118):\n with urllib.request.urlopen("http://127.0.0.1:"+str(port)+"/openapi.json",timeout=15) as response: checks[str(port)]=response.status\nprocesses=subprocess.check_output(["ps","-eo","pid,args"],text=True)\nactive=[line for line in processes.splitlines() if ("cap-harness run" in line or "cap-harness eval" in line) and "ps -eo" not in line]\nassert not active, "Another harness episode is active: "+repr(active)\nprint(json.dumps({"services":checks,"active_harness":active,"task_dir":str(p)}))')
    print(preflight, flush=True)
prior_history = [json.loads(line) for line in history_file.read_text(encoding='utf-8').splitlines()] if history_file.exists() else []
if prior_history and request_file.exists() and prior_history[-1]['request_hash'] == hashlib.sha256(request_file.read_bytes()).hexdigest():
    # Recover a completed request after a local status-file write error;
    # never execute that immutable request a second time.
    save_status(prior_history[-1])
else:
    save_status({'phase': 'idle', 'message': 'Awaiting a new task-local request'})
attempt_count = len(history_file.read_text(encoding='utf-8').splitlines()) if history_file.exists() else 0
try:
    while not (local_task / 'controller.stop').exists():
        time.sleep(2)
        if not request_file.exists():
            continue
        payload = request_file.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest in seen:
            continue
        # Require an atomically completed or quiet file to avoid half-written JSON.
        if time.time() - request_file.stat().st_mtime < 2:
            continue
        request = json.loads(payload)
        relative_program = validate(request)
        if options.verification:
            assert attempt_count < 2, 'Verifier maximum two measured program attempts'
            assert set(request['seeds']) == set(range(51,56)), 'Verifier attempt must measure all five seeds'
        attempt_count += 1
        seen.add(digest)
        tag = f'task{options.task_id}-' + digest[:12]
        source_hash = hashlib.sha256((local_task / str(relative_program)).read_bytes()).hexdigest()
        if options.max_policy_versions is not None:
            current_history = [json.loads(line) for line in history_file.read_text(encoding='utf-8').splitlines()] if history_file.exists() else []
            for prior in current_history:
                old_rel = PurePosixPath(prior['program']).relative_to(remote_task)
                old_source = local_task / str(old_rel)
                assert hashlib.sha256(old_source.read_bytes()).hexdigest() == prior['source_hash'], 'Prior numbered source changed'
                prior['observation_only'] = is_observation_only(old_source.read_text(encoding='utf-8'))
            request['observation_only'] = is_observation_only((local_task / str(relative_program)).read_text(encoding='utf-8'))
            check_budget(current_history, request, source_hash, options.max_policy_versions)
        record = {'phase': 'uploading', 'request_hash': digest, 'source_hash': source_hash,
                  'tag': tag, 'program': request['program'], 'seeds': request['seeds']}
        if options.max_policy_versions is not None:
            record['failure_mode'] = request['failure_mode']
            record['observation_only'] = request['observation_only']
        save_status(record)
        with open_transfer_sftp() as sftp:
            for p in sorted((local_task / 'code').glob('*.py')):
                sftp.put(str(p), str(remote_task / 'code' / p.name))
            for name in ('task_analysis.md', 'code/CHANGELOG.md', 'findings.md'):
                p = local_task / name
                if p.exists():
                    sftp.put(str(p), str(remote_task / name))
            with sftp.file(str(remote_task / 'requested_runs.json'), 'w') as output:
                output.write(json.dumps(request, indent=2))
        save_status({**record, 'phase': 'running'})
        print(remote_python('from pathlib import Path\nimport subprocess\nw=Path("/mnt/aspire-work")\nwith (w/"logs"/' + repr(tag + '.log') + ').open("w") as f:\n p=subprocess.Popen(["python3",str(w/"episode_job.py"),"--task-id",' + repr(str(options.task_id)) + ',"--tag",' + repr(tag) + ',"--task-dir",' + repr(str(remote_task)) + '],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)\nprint(p.pid)'), flush=True)
        deadline = time.monotonic() + (2400 if fresh_processes else 900)
        copied_seeds = {}
        while True:
            time.sleep(5)
            with open_transfer_sftp() as sftp:
                try:
                    with sftp.file('/mnt/aspire-work/job-' + tag + '.json') as f:
                        completion = json.loads(f.read())
                except (FileNotFoundError, json.JSONDecodeError):
                    if time.monotonic() > deadline:
                        raise TimeoutError('No job status before execution deadline; will not duplicate execution')
                    continue
            if completion['phase'] == 'running' and time.monotonic() > deadline:
                raise TimeoutError('Execution completion deadline exceeded; will not duplicate execution')
            if options.incremental_artifacts:
                output_rel = PurePosixPath(request['output_root']).relative_to(remote_task)
                for seed in completion.get('completed_seeds', []):
                    if str(seed) in copied_seeds: continue
                    copied_seeds[str(seed)] = stream_artifact_tree(
                        output_rel / f'{seed:04d}', Path(__file__).parent / f'{tag}-seed{seed:04d}.tar.gz',
                        source_hash)
                    receipt_path = local_task / f'artifact_transfer_{digest[:12]}.json'
                    receipt_path.write_text(json.dumps({'request_hash':digest,'source_sha256':source_hash,
                                                        'copied_seeds':copied_seeds},indent=2),encoding='utf-8')
            if completion['phase'] != 'running':
                break
        assert completion['phase'] == 'finished', completion
        if options.incremental_artifacts:
            assert set(map(int,copied_seeds)) == set(request['seeds'])
        save_status({**record, 'phase': 'downloading', 'remote_result': completion})
        archive_path = Path(__file__).parent / (tag + '-artifacts.tar.gz')
        with open_transfer_sftp() as sftp:
            sftp.get(completion['archive'], str(archive_path))
        assert archive_path.stat().st_size == completion['archive_bytes']
        with tarfile.open(archive_path) as archive:
            archive.extractall(local_task, filter='data')
        # Only remove this disposable transfer archive after its complete local copy
        # has been verified and extracted. Original remote episode evidence stays.
        expected_archive = '/mnt/aspire-work/job-' + tag + '-artifacts.tar.gz'
        assert completion['archive'] == expected_archive
        with open_transfer_sftp() as sftp:
            sftp.remove(expected_archive)
        results = []
        output_rel = PurePosixPath(request['output_root']).relative_to(remote_task)
        for p in (local_task / str(output_rel)).rglob('outcome.json'):
            result = json.loads(p.read_text(encoding='utf-8'))
            results.append({'path': str(p), 'program_ok': result.get('program_ok'),
                            'task_success': result.get('task_success'),
                            'seed': next((int(part) for part in p.parts if len(part) == 4 and part.isdigit()), None)})
        record = {**record, 'phase': 'artifacts_ready', 'remote_result': completion,
                  'output_root': str(local_task / str(output_rel)), 'outcomes': results}
        with history_file.open('a', encoding='utf-8') as history:
            history.write(json.dumps(record) + '\n')
        save_status(record)
except BaseException as exc:
    save_status({'phase': 'controller_error', 'error': repr(exc)})
    raise
finally:
    client.close()
