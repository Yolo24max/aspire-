"""Root-only Robosuite100 incremental all-file backup with durable receipts.

Uses the same audited transport/verification primitive as Stage1, while keeping a
different identity, lease, receipt and remote directory for the held-out sweep.
"""
import json
from pathlib import Path, PurePosixPath
import time

from aspire_network_recovery import SSHRecovery, acquire_local_lock, atomic_json
from aspire_robosuite_controller import backup_seed, remote_json
from aspire_robosuite_validation_job import SEEDS, digest
from aspire_robosuite_validation_monitor import parse_args, read_snapshot, validate_snapshot


def relative_run(value, canonical_task, args):
    candidate = PurePosixPath(value)
    for root in (PurePosixPath(canonical_task), args.remote_task):
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            continue
        prefix = PurePosixPath('validation/runs') / args.run_id / 'results'
        if '..' not in relative.parts and relative.is_relative_to(prefix):
            return relative.as_posix()
    raise ValueError('Run is outside the uniquely owned formal evaluation tree')


def verify_case(local_task, relative, args, seed):
    run = (local_task / relative).resolve()
    if not run.is_relative_to((local_task / 'validation').resolve()):
        raise ValueError('Case path escaped formal evaluation')
    metadata = json.loads((run / 'run.json').read_text())
    wanted = dict(status='finalized', benchmark='robosuite', suite=args.suite,
                  task_id=args.task_id, seed=seed, init_mode='saved')
    if any(metadata.get(k) != v for k, v in wanted.items()) or digest(run / 'source/program.py') != args.source_sha256:
        raise ValueError('Case identity or frozen program mismatch')
    capture = metadata.get('capture', {})
    if any(capture.get(k) != v for k, v in dict(max_steps=1000, camera_width=800, camera_height=512, videos=True).items()):
        raise ValueError('Case capture settings changed')
    reset = json.loads((run / 'episode/reset.json').read_text())
    cameras = sorted(reset['observation']['cameras'])
    if len(cameras) not in (2, 3):
        raise ValueError('Unexpected actual Robosuite camera count; preserve evidence')
    videos = sorted(p for p in (run / 'media/videos').glob('*.mp4') if not p.name.startswith('.'))
    expected_names = {name + '.mp4' for name in cameras}
    if {p.name for p in videos} != expected_names or any(p.stat().st_size == 0 for p in videos):
        raise ValueError('Missing, empty or unexpected camera videos')
    index = json.loads((run / 'media/video-index.json').read_text())
    if set(index['frames']) != set(cameras) or any(frames <= 0 for frames in index['frames'].values()):
        raise ValueError('Camera video frame counts are incomplete')
    return dict(seed=seed, relative_run=relative, cameras=cameras, videos=len(videos),
                video_files=[p.relative_to(local_task).as_posix() for p in videos])


def mirror_final_metadata(network, args, remote_task, receipt, receipt_path):
    owned = remote_task / '.heldout' / args.run_id
    code = f'''from pathlib import Path
import hashlib,json
t=Path({str(remote_task)!r});owned=t/'.heldout'/{args.run_id!r};v=t/'validation/runs'/{args.run_id!r}
paths=[t/n for n in ('validation_result.json','stage1_result.json','coordinator_handoff_audit.json','coordinator_provenance_review.json','freeze_manifest.json','fix_code.py')]
paths += [p for p in v.rglob('*') if p.is_file() and not p.is_relative_to(v/'results')]
paths += [p for p in owned.rglob('*') if p.is_file() and p.suffix=='.json' and '.tmp' not in p.name]
items=[]
for p in sorted(set(paths)):
 assert p.resolve().is_relative_to(t.resolve()) and not p.is_symlink()
 if not p.exists():continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 items.append({{'relative':p.relative_to(t).as_posix(),'size_bytes':p.stat().st_size,'sha256':h.hexdigest()}})
print(json.dumps(items))
'''
    items = remote_json(network, code, 'enumerate_final_validation_sidecar_hashes', timeout=120)
    done = receipt.setdefault('final_metadata', {})
    for item in items:
        relative = PurePosixPath(item['relative'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Metadata path traversal')
        target = args.local_task / item['relative']
        if done.get(item['relative']) == item and target.exists() and digest(target) == item['sha256']:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + '.download-partial')
        def transfer():
            with network.sftp() as sftp:
                sftp.get(str(remote_task / relative), str(partial))
        network.run(transfer, 'download_final_validation_sidecar')
        if partial.stat().st_size != item['size_bytes'] or digest(partial) != item['sha256']:
            raise ValueError('Final metadata size/SHA mismatch')
        partial.replace(target)
        done[item['relative']] = item
        atomic_json(receipt_path, receipt)
    return items


def main():
    args = parse_args(__doc__)
    prefix = f'{args.suite}-task{args.task_id}-validation'
    lease = acquire_local_lock(args.network_root / f'{prefix}-offload.lock')
    receipt_path = args.local_task / 'validation_offload_receipt.json'
    (args.local_task / '.requests' / args.run_id).mkdir(parents=True, exist_ok=True)
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else dict(
        run_id=args.run_id, source_sha256=args.source_sha256, suite=args.suite,
        task_id=args.task_id, cases={}, phase='copying', started_at=time.time())
    if receipt['run_id'] != args.run_id or receipt['source_sha256'] != args.source_sha256:
        lease.close(); raise ValueError('Backup receipt belongs to another formal evaluation identity')
    if receipt.get('phase') == 'complete' and set(map(int, receipt['cases'])) == set(SEEDS):
        print('ALREADY_COMPLETE_100_CASES_NO_REMOTE_WORK', flush=True); lease.close(); return
    network = SSHRecovery.interactive(args.network_root / f'{prefix}-offload-network.json',
        dict(role='validation_offload', run_root=str(args.remote_run_root), run_id=args.run_id,
             suite=args.suite, task_id=args.task_id, source_sha256=args.source_sha256))
    previous = None
    try:
        while True:
            state = read_snapshot(network, args)
            validate_snapshot(state, previous, args.expected, args.run_id)
            previous = state
            if state['phase'] == 'not_launched':
                if args.once:
                    return
                time.sleep(args.poll_seconds); continue
            remote_task = PurePosixPath(state['canonical_task'])
            remote_job = remote_task / '.heldout' / args.run_id / 'backup'
            remote_json(network, f'from pathlib import Path\nimport json\nPath({str(remote_job)!r}).mkdir(parents=True,exist_ok=True)\nprint(json.dumps({{"ready":True}}))\n', 'prepare_owned_backup_directory')
            request = dict(output_root=str(remote_task / 'validation/runs' / args.run_id / 'results'),
                           source_sha256=args.source_sha256)
            for key, row in sorted(state['results'].items(), key=lambda pair: int(pair[0])):
                seed = int(key)
                if receipt['cases'].get(key, {}).get('payload_retired'):
                    continue
                relative = relative_run(row['run_dir'], state['canonical_task'], args)
                # backup_seed first verifies ALL files and an all-file inventory,
                # commits a durable receipt, then idempotently retires remote payload.
                backup = backup_seed(network, args.local_task, remote_task, remote_job,
                                     request, args.run_id, seed)
                facts = verify_case(args.local_task, relative, args, seed)
                receipt['cases'][key] = dict(backup, **facts, payload_retired=True)
                atomic_json(receipt_path, receipt)
                print(json.dumps(dict(case_backed_up=seed, copied_cases=len(receipt['cases']),
                                      videos=sum(r['videos'] for r in receipt['cases'].values()))), flush=True)
            if state['phase'] == 'finished' and state['manifest_status'] == 'complete' and \
               set(map(int, receipt['cases'])) == set(SEEDS):
                mirror_final_metadata(network, args, remote_task, receipt, receipt_path)
                local_manifest = args.local_task / 'validation/runs' / args.run_id / 'manifest.json'
                manifest = json.loads(local_manifest.read_text())
                if manifest['identity'] != args.expected or set(map(int, manifest['results'])) != set(SEEDS):
                    raise ValueError('Final copied manifest identity or coverage mismatch')
                # Final report counts each case's actual cameras, rather than assuming
                # all single-arm and bimanual tasks have the same video count.
                receipt.update(phase='complete', finished_at=time.time(), trials=100,
                               passes=manifest['passes'], program_ok=sum(bool(r['program_ok']) for r in manifest['results'].values()),
                               verified_videos=sum(r['videos'] for r in receipt['cases'].values()),
                               cases_verified=100, manifest_sha256=digest(local_manifest))
                atomic_json(receipt_path, receipt)
                print(json.dumps(dict(phase='complete', run_id=args.run_id, cases=100,
                                      videos=receipt['verified_videos'], passes=receipt['passes'])), flush=True)
                return
            if args.once or state['phase'] in ('partial', 'runner_error', 'gpu_lock_unavailable'):
                receipt.update(phase='incomplete_preserved', remote_phase=state['phase'])
                atomic_json(receipt_path, receipt)
                return
            time.sleep(args.poll_seconds)
    finally:
        network.close(); lease.close()


if __name__ == '__main__':
    main()
