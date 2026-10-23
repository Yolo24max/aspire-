"""Root-owned Stage1 gate: identity, settings, coverage and published videos."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

def check_first_seed_gate(history):
    clean = None
    for request in history:
        if any(seed != 51 for seed in request['seeds']):
            assert clean is not None, 'Development expansion preceded the first clean seed51'
        if clean is None and any(row.get('seed') == 51 and row.get('program_ok')
                                 and row.get('task_success') for row in request['outcomes']):
            clean = {'tag': request['tag'], 'source_sha256': request['source_hash']}
    assert clean is not None, 'No actual first-seed success before generalization'
    return clean

def check_unseen_history(history, selected_source):
    checks = [(index, row) for index, row in enumerate(history)
              if any(seed in range(66, 81) for seed in row['seeds'])]
    assert len(checks) == 1, 'Unseen partition must be measured exactly once'
    index, unseen = checks[0]
    assert sorted(unseen['seeds']) == list(range(66, 81))
    assert unseen['source_hash'] == selected_source
    assert index == len(history) - 1, 'Policy requests followed the one-time unseen check'
    assert any(row['source_hash'] == selected_source
               and sorted(row['seeds']) == list(range(51, 66))
               and len(row['outcomes']) == 15 for row in history[:index]), \
        'Frozen source lacks an earlier complete development sweep'
    return {'tag': unseen['tag'], 'source_sha256': selected_source,
            'one_request': True, 'no_later_tuning_requests': True}

parser = argparse.ArgumentParser()
parser.add_argument('--task-dir', type=Path, required=True)
parser.add_argument('--task-id', type=int, required=True)
parser.add_argument('--selected', required=True)
parser.add_argument('--development-root', required=True)
parser.add_argument('--unseen-root', default='debug/holdout')
args = parser.parse_args()
task = args.task_dir.resolve()
source = (task / args.selected).read_bytes()
source_hash = hashlib.sha256(source).hexdigest()
assert (task / 'fix_code.py').read_bytes() == source, 'Selected/fix source mismatch'
tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        assert all(alias.name == 'math' for alias in node.names)
    assert not isinstance(node, ast.ImportFrom)
    if isinstance(node, ast.Attribute):
        assert not node.attr.startswith('_')
    if isinstance(node, ast.Name):
        assert not node.id.startswith('_')
        assert node.id not in {'getattr','hasattr','eval','exec','open','globals','locals','vars'}
assert (task / 'findings.md').is_file()
assert (task / 'skill_report.json').is_file()
report = json.loads((task / 'skill_report.json').read_text(encoding='utf-8'))
assert report['skill_library_sha']
partitions = []
for label, relative, seeds in [('development', args.development_root, set(range(51,66))),
                               ('unseen', args.unseen_root, set(range(66,81)))]:
    measured = []
    for outcome_path in sorted((task / relative).rglob('outcome.json')):
        run = outcome_path.parent
        meta = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        outcome = json.loads(outcome_path.read_text(encoding='utf-8'))
        assert meta['status'] == 'finalized'
        assert meta['benchmark'] == 'libero-pro' and meta['suite'] == 'libero_goal_swap'
        assert meta['task_id'] == args.task_id and meta['init_mode'] == 'seeded'
        assert meta['capture']['videos'] is True
        assert meta['capture']['max_steps'] == 1000
        assert meta['capture']['camera_width'] == 800 and meta['capture']['camera_height'] == 512
        assert not outcome['finalization_errors']
        assert (run / 'source/program.py').read_bytes() == source
        manifest = {item['path']: item for item in json.loads((run/'manifest.json').read_text(encoding='utf-8'))['files']}
        cameras = json.loads((run/'episode/reset.json').read_text(encoding='utf-8'))['observation']['cameras']
        videos = []
        for camera in cameras:
            relative_video = f'media/videos/{camera}.mp4'
            p = run / relative_video
            assert p.is_file() and p.stat().st_size > 512
            assert hashlib.sha256(p.read_bytes()).hexdigest() == manifest[relative_video]['sha256']
            videos.append(str(p))
        measured.append({'seed': meta['seed'], 'run': str(run), 'task_success': outcome['task_success'],
                         'program_ok': outcome['program_ok'], 'steps': outcome['steps_executed'], 'videos': videos})
    assert len(measured) == len(seeds) and {row['seed'] for row in measured} == seeds
    partitions.append({'partition':label,'trials':len(measured),
                       'task_success':sum(row['task_success'] for row in measured),
                       'program_ok':sum(row['program_ok'] for row in measured), 'runs':measured})
history = [json.loads(line) for line in (task/'coordinator_history.jsonl').read_text(encoding='utf-8').splitlines()]
first_seed_gate = check_first_seed_gate(history)
unseen_history = check_unseen_history(history, source_hash)
result = {'gate':'PASS','task_id':args.task_id,'selected':args.selected,
          'source_sha256':source_hash,'skill_library_sha':report['skill_library_sha'],
          'first_seed_gate':first_seed_gate,
          'unseen_history':unseen_history,
          'settings':{'benchmark':'libero-pro','suite':'libero_goal_swap','init_mode':'seeded',
                      'max_steps':1000,'camera_width':800,'camera_height':512,'videos':True},
          'partitions':partitions,
          'scope':'Artifact/source integrity checks; worker provenance verdict reviewed separately by root.'}
(task/'coordinator_handoff_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({**{k:v for k,v in result.items() if k!='partitions'},
                  'partitions':[{k:v for k,v in p.items() if k!='runs'} for p in partitions]},indent=2))
