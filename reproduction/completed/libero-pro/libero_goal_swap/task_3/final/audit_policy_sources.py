import ast
import hashlib
import json
from pathlib import Path
root = Path(r"C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_3/retry_02")
reports = []
for source in sorted((root/"code").glob("v[0-9][0-9]_*.py")):
    raw = source.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"))
    imports = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
    private_names = sorted({node.id for node in ast.walk(tree) if isinstance(node,ast.Name) and node.id.startswith("_")})
    private_attributes = sorted({node.attr for node in ast.walk(tree) if isinstance(node,ast.Attribute) and node.attr.startswith("_")})
    calls = sorted({ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node,ast.Call)})
    forbidden = [name for name in calls if any(token in name for token in ("getattr","setattr","hasattr","open(","native","sim.","eval","exec(","reward","check_success"))]
    reports.append({"source":str(source),"sha256":hashlib.sha256(raw).hexdigest(),"imports":imports,"private_names":private_names,"private_attributes":private_attributes,"forbidden_calls":forbidden,"all_calls":calls,"global_statements":sum(isinstance(node,ast.Global) for node in ast.walk(tree)),"provenance_static_pass":imports==["import math"] and not private_names and not private_attributes and not forbidden})
output = {"schema_version":1,"scope":"Offline source audit only; not simulator execution, not complete sandbox acceptance","policies":reports}
(root/"policy_source_audit.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
print(json.dumps({"policies":len(reports),"all_static_pass":all(row["provenance_static_pass"] for row in reports),"v00_global_known_rejection":reports[0]["global_statements"]}))
