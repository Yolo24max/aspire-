"""Offline final audit of Robosuite100 provenance and every backed-up file."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import time

from aspire_network_recovery import atomic_json
from aspire_robosuite_validation_offload import verify_case
from aspire_robosuite_validation_job import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task-dir', type=Path, required=True)
    parser.add_argument('--suite', choices=['cube_lifting', 'cube_stack', 'cube_restack', 'nut_assembly', 'spill_wipe', 'two_arm_lift', 'two_arm_handover'], required=True)
    options = parser.parse_args()
    task = options.task_dir.resolve()
    assert task.name == 'task_0' and task.parent.name == options.suite
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    receipt = read(task / 'validation_offload_receipt.json')
    rid = receipt['run_id']; source = digest(task / 'fix_code.py')
    manifest_path = task / 'validation/runs' / rid / 'manifest.json'
    manifest = read(manifest_path)
    assert receipt['phase'] == 'complete' and receipt['cases_verified'] == 100
    assert set(map(int, receipt['cases'])) == set(map(int, manifest['results'])) == set(range(1, 101))
    assert manifest['status'] == 'complete' and manifest['trials'] == receipt['trials'] == 100
    assert source == receipt['source_sha256'] == manifest['identity']['code_sha256']
    assert digest(manifest_path) == receipt['manifest_sha256']
    assert manifest['identity']['seeds'] == list(range(1, 101))
    assert all(manifest['identity'][k] == v for k, v in dict(benchmark='robosuite', suite=options.suite, task_id=0, init_mode='saved', max_steps=1000, camera_width=800, camera_height=512).items())
    args = SimpleNamespace(suite=options.suite, task_id=0, source_sha256=source)
    files = total_bytes = videos = 0
    paths = set()
    for seed in range(1, 101):
        case = receipt['cases'][str(seed)]
        assert case['seed'] == seed and case['source_sha256'] == source
        assert case['remote_retired'] and case['payload_retired']
        assert case['remote_receipt']['verified'] and case['remote_receipt']['remote_retired']
        facts = verify_case(task, case['relative_run'], args, seed)
        assert facts['cameras'] == case['cameras'] and facts['videos'] == case['videos']
        outcome = read(task / case['relative_run'] / 'outcome.json')
        row = manifest['results'][str(seed)]
        assert not outcome['finalization_errors']
        assert all(outcome[k] == row[k] for k in ['program_ok', 'task_success'])
        for item in case['verified_files']:
            p = task / item['relative']
            assert not p.is_symlink() and p.resolve().is_relative_to(task)
            assert item['relative'].startswith(case['relative_run'] + '/')
            assert item['relative'] not in paths
            paths.add(item['relative'])
            assert p.stat().st_size == item['size_bytes'] and digest(p) == item['sha256']
            files += 1; total_bytes += item['size_bytes']
        actual = {p.relative_to(task).as_posix() for p in (task / case['relative_run']).rglob('*') if p.is_file()}
        assert actual == {item['relative'] for item in case['verified_files']}
        videos += facts['videos']
    for item in receipt['final_metadata'].values():
        p = task / item['relative']
        assert p.resolve().is_relative_to(task) and not p.is_symlink()
        assert p.stat().st_size == item['size_bytes'] and digest(p) == item['sha256']
    before = read(task.parents[2] / 'network-monitoring/restart-20261022/manifest-before.json') if (task.parents[2] / 'network-monitoring/restart-20261022/manifest-before.json').exists() else None
    if before and before.get('identity', {}).get('suite') == options.suite:
        assert all(manifest['results'][key] == row for key, row in before['results'].items())
    else:
        before = None
    assert videos == receipt['verified_videos'] == 200
    result = dict(status='PASS', checked_at=time.time(), benchmark='robosuite', suite=options.suite, task_id=0,
                  run_id=rid, source_sha256=source, trials=100, task_success=manifest['passes'],
                  program_ok=sum(bool(row['program_ok']) for row in manifest['results'].values()),
                  cases_verified=100, videos=videos, verified_files=files, verified_bytes=total_bytes,
                  all_file_size_sha256='PASS', actual_camera_coverage='PASS', manifest_identity='PASS',
                  completed_pre_restart_results_preserved='PASS' if before else 'receipt_available_separately',
                  skill_promotion='pending_independent_verification')
    atomic_json(task / 'coordinator_validation_audit.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
