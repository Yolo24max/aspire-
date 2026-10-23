import csv
import json
from pathlib import Path
root = Path(r"C:/Users/24683/Documents/ChatGPT/RSI/ASPIRE/outputs/runs/2026-10-19_16-40-30_goal-swap-server/libero-pro/libero_goal_swap/task_3/retry_02")
rows = []
for outcome_path in sorted((root/"debug").rglob("outcome.json")):
    run = outcome_path.parent
    seed = int(run.parent.name)
    if seed < 51 or seed > 80:
        raise ValueError("Unexpected seed in retry-owned debug artifacts")
    outcome = json.loads(outcome_path.read_text(encoding="utf-8-sig"))
    videos = sorted((run/"media/videos").glob("*.mp4"))
    videos = [path for path in videos if ".partial." not in path.name]
    rows.append({"seed":seed,"run_dir":str(run),"outcome_path":str(outcome_path),"program_ok":outcome["program_ok"],"task_success":outcome["task_success"],"steps":outcome["steps_executed"],"termination":outcome["termination_reason"],"videos":[str(path) for path in videos]})
(root/"artifact_index.json").write_text(json.dumps({"schema_version":1,"retry_classification":"user-authorized independent retry_02","runs":rows},indent=2),encoding="utf-8")
with (root/"video_index.csv").open("w",newline="",encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle,fieldnames=["seed","program_ok","task_success","steps","run_dir","video"])
    writer.writeheader()
    for row in rows:
        for video in row["videos"]:
            writer.writerow({key:row[key] for key in ["seed","program_ok","task_success","steps","run_dir"]}|{"video":video})
lines = ["# Artifact index: independent retry_02", "", "All paths below are absolute. Validation/held-out artifacts are coordinator-owned and excluded.", "", "- [Machine-readable complete run index]("+str(root/"artifact_index.json")+")", "- [Absolute video index]("+str(root/"video_index.csv")+")", "- [Frozen source identity]("+str(root/"freeze.json")+")", "- [Provenance audit]("+str(root/"provenance_audit.md")+")", "- [Static source audit]("+str(root/"policy_source_audit.json")+")", "- [Version budget]("+str(root/"budget.json")+")", "- [Change log]("+str(root/"code/CHANGELOG.md")+")", "- [Findings]("+str(root/"findings.md")+")", "- [Skill report]("+str(root/"skill_report.json")+")", "", "## Runs", ""]
for row in rows:
    lines.append("- Seed "+str(row["seed"])+": ["+row["run_dir"]+"]("+row["run_dir"]+"), program_ok="+str(row["program_ok"])+", task_success="+str(row["task_success"])+", steps="+str(row["steps"])+".")
(root/"artifact_index.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps({"run_count":len(rows),"video_count":sum(len(row["videos"]) for row in rows)}))
