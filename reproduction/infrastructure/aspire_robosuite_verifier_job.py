"""Independent verifier partition; reuse original episode/lock/backup contracts."""
import argparse
from pathlib import Path
import aspire_robosuite_job as job

SUITES = {'cube_lifting', 'cube_stack', 'cube_restack', 'nut_assembly', 'spill_wipe', 'two_arm_lift', 'two_arm_handover'}


def validate(request, suite, task_id):
    fixed = dict(benchmark='robosuite', suite=suite, task_id=0, init_mode='saved',
                 max_steps=1000, camera_width=800, camera_height=512, workers=1, gpu=0)
    assert suite in SUITES and task_id == 0
    assert all(type(request.get(k)) is type(v) and request[k] == v for k, v in fixed.items())
    assert request['stage'] in ['observe', 'verification_v01', 'verification_v02']
    assert request['seeds'] == ([101] if request['stage'] == 'observe' else list(range(101, 106)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--suite', required=True)
    parser.add_argument('--task-id', type=int, required=True)
    parser.add_argument('--request-dir', type=Path, required=True)
    parser.add_argument('--gate', required=True)
    args = parser.parse_args()
    assert args.run_root.name == f'robosuite__{args.suite}__task_0' and args.run_root.parent.name == 'verification'
    job.validate_settings = validate
    job.run_job(args)
