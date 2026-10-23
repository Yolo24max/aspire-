import json
from pathlib import Path
base=Path(__file__).resolve().parent
unseen=json.loads((base/'unseen_summary.json').read_text()); assert unseen['seeds']==list(range(66,81))
score=unseen['successes']; pok=unseen['program_ok']
p=base/'api_audit_v08.json'; audit=json.loads(p.read_text())
audit['evaluation_status']={'development_seeds':'51-65','development_task_success':14,'development_program_ok':15,'unseen_seeds':'66-80','unseen_request_count':1,'unseen_task_success':score,'unseen_program_ok':pok,'heldout_accessed_by_worker':False,'later_worker_policy_requests':0}
audit['operational_limitation']='Own adaptation omitted ArmCommand.embodiment in dedicated settling loop; selected development225calls rejected,0ticks. Retraction still advances physics. This is a command-acceptance defect, not an access/provenance violation; source frozen unchanged.'
p.write_text(json.dumps(audit,indent=2),encoding='utf-8')
p=base/'constant_audit_v08.md'; text=p.read_text(encoding='utf-8-sig')
start=text.find('Evidence limits:')
if start>=0: text=text[:start]+f'Evaluation evidence: selected v08measured14/15development task success and15/15program_ok, followed by exactly one frozen-source unseen66–80measurement: {score}/15task and{pok}/15program_ok. Heldout1–50remains root-only and was never accessed. No later worker policy requests or tuning. fix_code.py is a byte-identical copy made after full coverage and access/provenance auditPASS.\n'
text=text.replace('v08measured','v08 measured').replace('/15development','/15 development').replace('/15program_ok','/15 program_ok').replace('/15task','/15 task').replace('and15','and 15').replace('and'+str(pok),'and '+str(pok)).replace('auditPASS','audit PASS')
p.write_text(text,encoding='utf-8')
p=base/'constant_audit_v07.md'; text=p.read_text(encoding='utf-8-sig'); start=text.find('Evidence limits:')
if start>=0: text=text[:start]+f'Historical evaluation evidence: v07clean seed51 success, then11/15full development task successes and12/15program_ok. v07was not run on unseen. Selected v08later measured14/15development and{score}/15exact-once unseen; see v08audit and coverage inventory.\n'
p.write_text(text,encoding='utf-8')
p=base/'provenance_ledger.md'; text=p.read_text(encoding='utf-8-sig')
text=text.replace('Current API/provenance audit:','Final API/provenance audit:')
text=text.replace('- No other task directories read. No heldout/unseen seeds requested.',f'- No other task directories read. Selected v08was requested exactly once on unseen66–80after full14/15development; measured{score}/15unseen. Heldout1–50was never requested or accessed.')
text=text.replace('- fix_code.py intentionally absent until measured dev/unseen protocol and audit complete.','- fix_code.py copied byte-identically from frozenv08only after complete selected-source development/unseen coverage and access/provenance auditPASS.')
text+=f'\nFinal measured status: v07full development11/15task,12/15program; v08selected development14/15task,15/15program; exact-once unseen{score}/15task,{pok}/15program. Eight valid policy versions, with OOM-onlyv00/firstv01 excluded. Own incomplete settling adaptation and zero executed dedicated settling ticks are recorded in settling_audit.json and findings; the complete skill recipe was correct.\n'
p.write_text(text,encoding='utf-8')
p=base/'task_analysis.md'; text=p.read_text(encoding='utf-8-sig')
text=text.replace('It is being measured across all15 development scenes; no generalization claim yet.',f'It later measured11/15development. v08selected after14/15development, then measured exactly once on unseen66–80: {score}/15; no tuning afterward.')
p.write_text(text,encoding='utf-8')
p=base/'debug'/'blocked'/'placement_border.md'; text=p.read_text(encoding='utf-8-sig').replace('Full15 results pending.','Full15result:14/15task,15/15program;65retains this observed border regime.')
p.write_text(text,encoding='utf-8')
print('Final status notes updated; historical OOM entries preserved; policy bytes unchanged')
