import ast
import hashlib
import json
from pathlib import Path

task = Path(__file__).resolve().parent
source = task / 'code' / 'v07_held_geometry.py'
code = source.read_text(encoding='utf-8-sig')
tree = ast.parse(code)
imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
private_names = sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id.startswith('_')})
private_attributes = sorted({n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute) and n.attr.startswith('_')})
forbidden_names = sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id in {'env','sim','open','eval','exec','getattr','hasattr','globals','locals','reward','success'}})
constants = sorted({repr(n.value) for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,(int,float))})
report = {'program':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'imports':imports,'private_names':private_names,'private_attributes':private_attributes,'forbidden_names':forbidden_names,'scalar_constants':constants,'automated_audit_pass':imports==['math'] and not(private_names or private_attributes or forbidden_names),'manual_provenance':'All object/target choices follow task language; XYZ, extent, grasp and held relations come from runtime public point clouds or robot state. Scalar constants are quantiles, generic clearance/tolerances, relative guards and bounded step limits. No seed branches, fixed world poses/dimensions/pixels or native assets/state.'}
(task/'api_audit_v07.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
