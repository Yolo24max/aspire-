"""Root-controlled isolated verifier queue; never reads the proposer's program."""
import ast
import argparse
import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import time

from aspire_network_recovery import SSHRecovery, acquire_local_lock, atomic_json
from aspire_policy_budget import is_observation_only
from aspire_robosuite_controller import execute_request, put_immutable, remote_json
from aspire_robosuite_job import digest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--remote-run-root', required=True)
    options = parser.parse_args()
    from aspire_robosuite_verifier_job import SUITES
    assert options.suite in SUITES
    suite = options.suite
    V = options.run_root.resolve() / 'verification' / f'robosuite__{suite}__task_0'
    REMOTE = PurePosixPath(options.remote_run_root) / 'verification' / f'robosuite__{suite}__task_0'
    audit = json.loads((options.run_root / 'robosuite' / suite / 'task_0/coordinator_validation_audit.json').read_text())
    assert audit['suite'] == suite and audit['status'] == 'PASS' and audit['cases_verified'] == 100
    assert not (V / 'verification_report.json').exists(), 'Completed independent verifier must never restart'
    lease = acquire_local_lock(V / 'root-controller.lock')
    network = SSHRecovery.interactive(V / 'network-recovery.json', f'robosuite:independent-{suite}-verifier:root-controller')
    task = V / 'robosuite' / suite / 'task_0'
    task.mkdir(parents=True, exist_ok=True)
    remote_task = REMOTE / 'robosuite' / suite / 'task_0'
    args = SimpleNamespace(remote_run_root=REMOTE, remote_gate=REMOTE / 'execution-ready.json',
                           suite=suite, task_id=0, poll_seconds=3,
                           job_script=Path(__file__).with_name('aspire_robosuite_verifier_job.py'))
    gate = dict(benchmark='robosuite', owner='robosuite', gpu=0, launch_enabled=True,
                run_root=str(REMOTE), suite=suite, task_id=0, purpose='independent_skill_verification')
    put_immutable(network, args.remote_gate, json.dumps(gate).encode())
    put_immutable(network, REMOTE / '.infrastructure/aspire_robosuite_job.py', Path(__file__).with_name('aspire_robosuite_job.py').read_bytes())
    try:
        while True:
            for path in sorted((V / 'requests').glob('*.json')):
                raw = json.loads(path.read_text())
                rid = raw['request_id']
                assert rid == path.stem and rid.replace('_', '').replace('-', '').isalnum()
                response = V / 'responses' / (rid + '.json')
                if response.exists():
                    continue
                stage = raw['stage']
                assert stage in ['scene', 'v01', 'v02']
                assert raw['seeds'] == ([101] if stage == 'scene' else list(range(101, 106)))
                program = (V / raw['program_relative']).resolve()
                assert program.is_relative_to(V / 'code') and not program.is_symlink()
                source = program.read_text(encoding='utf-8')
                tree = ast.parse(source)
                assert not any(isinstance(n, ast.ImportFrom) for n in ast.walk(tree))
                assert all(all(a.name == 'math' for a in n.names) for n in ast.walk(tree) if isinstance(n, ast.Import))
                assert not any(isinstance(n, ast.Attribute) and n.attr.startswith('_') for n in ast.walk(tree))
                forbidden = {'open', 'eval', 'exec', 'compile', '__import__', 'getattr', 'globals', 'locals', 'vars'}
                assert not any(isinstance(n, ast.Name) and n.id in forbidden for n in ast.walk(tree))
                assert is_observation_only(source) == (stage == 'scene')
                previous = list((task / '.requests').glob('*/reservation.json'))
                records = [json.loads(p.read_text()) for p in previous]
                selected = [x for x in records if x['stage'] == ('observe' if stage == 'scene' else 'verification_' + stage)]
                assert not selected or all(x['source_sha256'] == digest(program) for x in selected)
                assert len({x['source_sha256'] for x in records if not x['observation_only']}) <= 2
                if stage == 'v02':
                    assert any(x['stage'] == 'verification_v01' for x in records)
                request = dict(benchmark='robosuite', suite=suite, task_id=0, init_mode='saved',
                               max_steps=1000, camera_width=800, camera_height=512, workers=1, gpu=0,
                               seeds=raw['seeds'], failure_mode='independent_transmission_test',
                               program=raw['program_relative'], source_sha256=digest(program),
                               observation_only=(stage == 'scene'), execution_mode='fresh_per_seed',
                               stage='observe' if stage == 'scene' else 'verification_' + stage,
                               output_root=str(remote_task / 'debug' / stage))
                import hashlib
                request_id = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                atomic_json(V / 'coordinator-status.json', dict(phase='executing_request', request_id=rid, stage=stage))
                execute_request(network, args, task, remote_task, request, request_id, program)
                result = json.loads((task / '.requests' / request_id / 'result.json').read_text())
                result.update(local_task=str(task), stage=stage, worker_request_id=rid,
                              artifacts_root=str(task / 'debug' / stage), independent_verification=True)
                atomic_json(response, result)
                atomic_json(V / 'coordinator-status.json', dict(phase='response_ready', request_id=rid, stage=stage))
                print(json.dumps(dict(response_ready=str(response))), flush=True)
            if (V / 'verification_report.json').exists():
                return
            time.sleep(2)
    finally:
        network.close(); lease.close()


if __name__ == '__main__':
    main()
