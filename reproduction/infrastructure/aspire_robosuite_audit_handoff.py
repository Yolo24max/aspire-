"""Root-only offline identity/backup gate; no policy debugging or episode launch."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time

from aspire_robosuite_controller import history_records
from aspire_network_recovery import atomic_json


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def frozen_identity(freeze):
    hashes = {freeze[k] for k in ('source_sha256', 'sha256') if k in freeze}
    programs = {freeze[k] for k in ('program', 'selected_program') if k in freeze}
    if len(hashes) != 1 or len(programs) != 1:
        raise ValueError('Missing or conflicting frozen identity aliases')
    return next(iter(hashes)), next(iter(programs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task-dir', type=Path, required=True)
    args = parser.parse_args(); task = args.task_dir.resolve()
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    freeze = read(task / 'freeze_manifest.json')
    source = task / 'fix_code.py'; expected = sha(source)
    frozen_hash, selected_program = frozen_identity(freeze)
    assert frozen_hash == expected == sha(task / selected_program)
    audit = read(task / 'policy_source_audit.json')
    assert audit['status'] == 'PASS' and audit['sha256'] == expected and not audit['issues']
    tree = ast.parse(source.read_text(encoding='utf-8'))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(isinstance(node, ast.Import) and all(a.name == 'math' for a in node.names) for node in imports)
    forbidden = {'eval', 'exec', 'compile', 'open', '__import__', 'getattr', 'globals', 'locals', 'vars'}
    assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Name) and n.id in forbidden for n in ast.walk(tree))
    history = history_records(task)
    policies = {h['source_sha256'] for h in history if not h.get('observation_only')}
    assert len(policies) <= 8
    modes = {}
    for h in history:
        if not h.get('observation_only'):
            modes.setdefault(h['failure_mode'], set()).add(h['source_sha256'])
    assert all(len(hashes) <= 3 for hashes in modes.values())
    partitions = {}; verified_files = 0; verified_bytes = 0; videos = 0
    for partition, seeds in [('development', list(range(101, 126))), ('unseen', list(range(126, 131)))]:
        rows = [h for h in history if h['stage'] == partition and h['source_sha256'] == expected]
        assert len(rows) == 1
        h = rows[0]; directory = task / '.requests' / h['request_id']
        state = read(directory / 'last_remote_state.json')
        assert h['phase'] == 'artifacts_ready' and state['phase'] == 'finished'
        assert h['seeds'] == state['completed_seeds'] == seeds
        assert h['benchmark'] == 'robosuite' and h['suite'] == freeze['suite'] and h['task_id'] == 0
        assert h['init_mode'] == 'saved' and h['max_steps'] == 1000
        assert (h['camera_width'], h['camera_height'], h['workers']) == (800, 512, 1)
        assert sorted(v['seed'] for v in h['outcomes']) == seeds
        for row in h['outcomes']:
            run = (task / row['relative_run']).resolve()
            assert run.is_relative_to(task / 'debug') and sha(run / 'source/program.py') == expected
            metadata = read(run / 'run.json'); outcome = read(run / 'outcome.json')
            assert metadata['status'] == 'finalized' and metadata['seed'] == row['seed']
            assert metadata['benchmark'] == 'robosuite' and metadata['suite'] == freeze['suite']
            assert metadata['task_id'] == 0 and metadata['init_mode'] == 'saved'
            assert outcome['task_success'] == row['task_success'] and outcome['program_ok'] == row['program_ok']
            assert not outcome['finalization_errors']
            receipt = read(directory / f"seed_{row['seed']:04d}_receipt.json")
            assert receipt['source_sha256'] == expected and receipt['remote_retired']
            for item in receipt['verified_files']:
                p = (task / item['relative']).resolve()
                assert p.is_relative_to(task) and not p.is_symlink()
                assert p.stat().st_size == item['size_bytes'] and sha(p) == item['sha256']
                verified_files += 1; verified_bytes += item['size_bytes']
                videos += item['relative'].endswith('.mp4')
        partitions[partition] = dict(request_id=h['request_id'], seeds=seeds,
            trials=len(seeds), task_success=sum(bool(v['task_success']) for v in h['outcomes']),
            program_ok=sum(bool(v['program_ok']) for v in h['outcomes']))
    unseen = next(h for h in history if h['request_id'] == partitions['unseen']['request_id'])
    assert not any(h['reserved_at'] > unseen['reserved_at'] for h in history)
    assert partitions['development']['task_success'] == partitions['development']['program_ok'] == 25
    assert partitions['unseen']['task_success'] == partitions['unseen']['program_ok'] == 5
    assert videos == 60
    report = read(task / 'skill_report.json')
    assignment = read(task / 'root_assignment.json')
    library_sha = freeze.get('skill_library_sha', assignment['library_sha'])
    assert report['skill_library_sha'] == library_sha == assignment['library_sha']
    assert not list((task / 'validation').rglob('manifest.json'))
    result = dict(gate='PASS', benchmark='robosuite', suite=freeze['suite'], task_id=0,
        source_sha256=expected, checked_at=time.time(), partitions=partitions,
        unique_policies=len(policies), max_policies=8, verified_files=verified_files,
        verified_bytes=verified_bytes, videos=videos, heldout_started=False,
        exactly_once_unseen=True, no_post_unseen_tuning=True,
        skill_library_sha=library_sha,
        library_identity_evidence='worker freeze and dispatch' if 'skill_library_sha' in freeze else 'recorded dispatch assignment and attempt skill report; original worker freeze preserved',
        unseen_execution_evidence='unique completed frozen-source request; prelaunch counters are not execution evidence')
    atomic_json(task / 'coordinator_handoff_audit.json', result)
    atomic_json(task / 'coordinator_provenance_review.json', dict(status='PASS', source_sha256=expected,
        benchmark='robosuite', suite=freeze['suite'], task_id=0, public_api_static_audit='PASS',
        frozen_source_and_partition_provenance='PASS', full_file_backup_audit='PASS',
        skill_library_sha=library_sha,
        unpromoted_proposals=len(report.get('proposed_new', []))+len(report.get('proposed_edits', [])),
        heldout_status='NOT_STARTED; ready for coordinator-owned single seeds1-100 evaluation'))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
