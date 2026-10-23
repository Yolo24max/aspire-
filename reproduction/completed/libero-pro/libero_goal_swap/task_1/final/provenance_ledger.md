# Working provenance and consultation ledger

Canonical library hash read before manipulation: 4f6964b8ab59e95a.

Opened sections:
- task-exploration.md: Initial Scene Analysis; Triage from disk; Wrap every run; Sandbox constraints.
- localize.md: Standard Localization Helper; Prompt Registry; Disambiguation; Key Signals; Prompting Strategy; Placement Z Notes.
- grasp.md: Standard Pick-and-Place Template; Cylindrical Side Grasp; Key Conventions; Object Geometry Utilities.
- transport.md: Waypoint Sequences; Pre-Probe IK Conditioning; Safe Transit; Placement Approach / Physics Settling; Basket / Container Placement.
- manipulation.md: Knob / Switch; Hinged Door; Pushing / Sliding; General Notes (read before task interaction was confirmed, mostly not applicable).

Final API/provenance audit:
- Imports: math only.
- Public object choices: bowl and stove from authoritative task language; prompts correspond to those nouns.
- Every position/dimension/pixel: no copied snapshot constants. Poses computed from current public projected point clouds and generated/public orientation.
- Constants are quantile fractions, generic relative grasp/clearance offsets, convergence tolerances, and bounded tick limits.
- No native simulator, reward, success predicate, asset, credential, filesystem or networking access inside policy.
- No other task directories read. Selected v08was requested exactly once on unseen66–80after full14/15development; measured13/15unseen. Heldout1–50was never requested or accessed.
- v00 failed before motion due CGN inference OOM (coordinator diagnosis); v01 failed before motion due SAM3 inference OOM. Neither establishes manipulation efficacy.
- fix_code.py copied byte-identically from frozenv08only after complete selected-source development/unseen coverage and access/provenance auditPASS.

Final measured status: v07full development11/15task,12/15program; v08selected development14/15task,15/15program; exact-once unseen13/15task,15/15program. Eight valid policy versions, with OOM-onlyv00/firstv01 excluded. Own incomplete settling adaptation and zero executed dedicated settling ticks are recorded in settling_audit.json and findings; the complete skill recipe was correct.
