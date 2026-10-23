"""Verify exported code and result provenance without running simulations."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=read(ROOT/'reproduction/source-manifest.json');files=manifest['files'];errors=[]
 for r in files:
  p=ROOT/r['path']
  if not p.is_file():errors.append('Missing: '+r['path']);continue
  if p.stat().st_size!=r['bytes'] or digest(p)!=r['sha256']:errors.append('Hash/size mismatch: '+r['path'])
 data=read(ROOT/'reproduction/results.json');tasks=data['tasks'];total=0
 assert len(tasks)==8 and len({(t['benchmark'],t['suite'],t['task_id']) for t in tasks})==8
 for t in tasks:
  p=ROOT/t['path'];v=read(p/'final/validation_result.json');m=read(p/'evidence/formal-manifest.json');episodes=read(p/'evidence/episodes.json')
  assert digest(ROOT/t['policy'])==t['source_sha256']==v['code_sha256']==m['identity']['code_sha256']
  assert t['run_id']==v['run_id']
  assert len(episodes)==t['trials']==v['trials']==len(m['results'])
  assert sum(bool(e['task_success']) for e in episodes)==t['passes']==v['passes']==m['passes']
  assert len({e['seed'] for e in episodes})==len(episodes)
  assert sorted(e['seed'] for e in episodes)==sorted(t['scientific_settings']['seeds'])
  if t['selected_attempt']!='original':assert (p/'history').is_dir() and t['caveat']
  total+=len(episodes)
 assert total==550==data['formal_episodes']
 py=0;js=0
 for p in ROOT.rglob('*'):
  if not p.is_file() or '.git' in p.parts:continue
  if p.suffix=='.py':
   try:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));py+=1
   except SyntaxError as e:errors.append(str(e))
  elif p.suffix=='.json':
   try:read(p);js+=1
   except Exception as e:errors.append(str(p)+': '+str(e))
 assert not errors,'\n'.join(errors)
 print(json.dumps({'status':'PASS','exported_files_verified':len(files),'completed_tasks':len(tasks),'formal_episodes':total,'python_files_parsed':py,'json_files_parsed':js,'simulations_started':0}))
if __name__=='__main__':main()
