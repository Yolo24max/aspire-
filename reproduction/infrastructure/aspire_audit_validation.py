"""Audit complete local heldout evidence after the durable transfer finishes."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--task-dir',type=Path,required=True)
parser.add_argument('--task-id',type=int,required=True)
args=parser.parse_args();task=args.task_dir.resolve()
source=(task/'fix_code.py').read_bytes();sha=hashlib.sha256(source).hexdigest()
matches=[]
for p in (task/'validation').rglob('manifest.json'):
    m=json.loads(p.read_text(encoding='utf-8'))
    if m.get('identity',{}).get('code_sha256')==sha:matches.append((p,m))
assert len(matches)==1
manifest_path,manifest=matches[0];identity=manifest['identity']
assert manifest['status']=='complete' and manifest['trials']==50
assert identity['seeds']==list(range(1,51))
assert identity['benchmark']=='libero-pro' and identity['suite']=='libero_goal_swap'
assert identity['task_id']==args.task_id and identity['init_mode']=='seeded'
assert identity['max_steps']==1000 and identity['camera_width']==800 and identity['camera_height']==512
rows=[]
for p in sorted((manifest_path.parent/'results').rglob('outcome.json')):
    run=p.parent;meta=json.loads((run/'run.json').read_text(encoding='utf-8'))
    outcome=json.loads(p.read_text(encoding='utf-8'))
    assert meta['status']=='finalized' and meta['init_mode']=='seeded'
    assert meta['task_id']==args.task_id and meta['suite']=='libero_goal_swap'
    assert meta['capture']=={'camera_height':512,'camera_width':800,'max_steps':1000,'profile':'balanced_evidence','videos':True}
    assert not outcome['finalization_errors']
    assert (run/'source/program.py').read_bytes()==source
    reported=manifest['results'][str(meta['seed'])]
    assert outcome['task_success']==reported['task_success'] and outcome['program_ok']==reported['program_ok']
    files={item['path']:item for item in json.loads((run/'manifest.json').read_text(encoding='utf-8'))['files']}
    cameras=json.loads((run/'episode/reset.json').read_text(encoding='utf-8'))['observation']['cameras']
    videos=[]
    for camera in cameras:
        relative=f'media/videos/{camera}.mp4';video=run/relative
        assert video.is_file() and video.stat().st_size>512
        assert hashlib.sha256(video.read_bytes()).hexdigest()==files[relative]['sha256']
        videos.append(str(video))
    rows.append({'seed':meta['seed'],'task_success':outcome['task_success'],'program_ok':outcome['program_ok'],
                 'steps':outcome['steps_executed'],'run':str(run),'videos':videos})
assert len(rows)==50 and {row['seed'] for row in rows}==set(range(1,51))
passes=sum(row['task_success'] for row in rows)
assert passes==manifest['passes']
audit={'gate':'PASS','task_id':args.task_id,'trials':50,'passes':passes,'pass_rate':passes/50,
       'program_ok':sum(row['program_ok'] for row in rows),'source_sha256':sha,'manifest':str(manifest_path),
       'video_count':sum(len(row['videos']) for row in rows),'settings':identity,'runs':rows}
(task/'coordinator_validation_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
(task/'validation_all_camera_video_index.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['runs','settings']},indent=2))
