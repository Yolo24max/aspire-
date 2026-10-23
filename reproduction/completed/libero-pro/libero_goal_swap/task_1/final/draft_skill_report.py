import json
from pathlib import Path
root=Path(__file__).resolve().parent
consulted=[]
def add(skill,section,verdict,evidence):
    consulted.append(dict(skill=skill,section=section,verdict=verdict,evidence=evidence))
add('task-exploration.md','Initial Scene Analysis','useful','Used mirrored public seed51 task language and scene. v07 clean success on51; scene hypotheses were revised from recorded evidence, not copied as executable coordinates.')
add('task-exploration.md','Triage from disk, not from a run: log line','useful','Read finalized outcome/source/trace/image files for every completed51 trial; distinguished provider OOM from manipulation failures.')
add('task-exploration.md','Wrap every run in timeout','not-applicable','Root-owned remote queue executes episodes; worker never launches simulator processes.')
add('task-exploration.md','Sandbox constraints when writing probes','useful','All valid51 policies use math only and documented builtins; no sandbox AST rejection occurred.')
add('localize.md','Standard Localization Helper','useful','Prompt fallback plus minimum-point guards correctly localized bowl and stove on51. v07 clean success; no isolated helper ablation.')
add('localize.md','Prompt Registry','not-applicable','The registry has no bowl/stove entry. Prompts came from current language and public scene evidence.')
add('localize.md','Disambiguation: Two Similar Objects in Scene','not-applicable','The inspected scene has one requested bowl; no multi-object candidate selector was used.')
add('localize.md','Key Signals','useful','Typed provider failures identified CGN and SAM3 OOM-only51 runs. Candidate ordering in typed JSON corrected an initial misreading of multi-box overlays.')
add('localize.md','Prompting Strategy','useful','Read authoritative runtime language and localized stove before grasp. grey bowl and stove selected correct masks on51; selected v07 succeeded.')
add('localize.md','Placement Z Notes','useful','Observed clouds represent visible surfaces. v07 measured held bowl relation rather than assuming initial center offset;51 succeeded, causal contributions not isolated.')
add('grasp.md','Standard Pick-and-Place Template','useful','Used staged approach, close/lift, transport and release structure. v07 succeeded51, with task-derived rim fallback and bounded public joint stages.')
add('grasp.md','Cylindrical Side Grasp (bottles, cans)','not-applicable','Requested object is an open bowl; used a rim grasp rather than cylindrical side grasp.')
add('grasp.md','Key Conventions','useful','close_gripper contact-stall completion preserved closed command during51 lift/transport. Public motion diagnostics were checked; no home call while holding.')
add('grasp.md','Object Geometry Utilities','useful','Computed bowl/rack clearance and held geometry from public point-cloud quantiles. v07 passed51 and provenance audit.')
add('transport.md','Waypoint Sequences','not-applicable','The section is a structural placeholder; authored Cartesian and joint staging from measured execution failures.')
add('transport.md','Pre-Probe IK Conditioning','not-applicable','Observed IK solved requested poses; failures were execution/contact, so no before-grasp placement previsit was justified.')
add('transport.md','Safe Transit (Lateral Escape Before Lift)','not-applicable','The section has no executable recipe, and the selected approach lifts vertically before lateral transport.')
add('transport.md','Placement Approach','not-applicable','No filled placement approach recipe exists in the section. Measured rack interception motivated runtime held offset and higher clearance.')
add('transport.md','Physics Settling After Release','useful','Used15 explicit public joint-position hold ticks with open gripper after release. The51 policy completed cleanly; tick-count ablation not performed.')
add('transport.md','Basket / Container Placement','not-applicable','Goal is a stove surface, not a container. Did not apply generic container release-height rule.')
add('manipulation.md','Knob / Switch Turning','not-applicable','Task language requests bowl placement; no knob/switch operation needed.')
add('manipulation.md','Hinged Door Opening / Closing','not-applicable','No requested articulated door action.')
add('manipulation.md','Pushing / Sliding','not-applicable','Selected policy grasps and transports the bowl; no push technique used.')
add('manipulation.md','General Notes','not-applicable','Articulated manipulation notes do not determine this bowl pick/place strategy.')
report={'schema_version':1,'benchmark':'libero-pro','suite':'libero_goal_swap','task_id':1,'skill_library_sha':'4f6964b8ab59e95a','consulted':consulted,'proposed_edits':[],'proposed_new':[]}
(root/'skill_report_draft.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('draft sections',len(consulted))
