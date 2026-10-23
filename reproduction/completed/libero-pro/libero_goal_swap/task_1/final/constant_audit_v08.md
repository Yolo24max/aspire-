# v08 Constant Provenance Audit

Policy SHA256:6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226

PASS. No task geometry was obtained from native state, assets, another task, fixed scene coordinates, or seed identities.

- Object/goal prompts: `grey bowl`/`bowl` and `stove`/`hot plate`, taken from authoritative task language and verified with selected public segmentation records.
- Grasp XYZ: current bowl point-cloud X85 percentile, geometry Y center, current Z95 percentile minus12mm generic rim offset. Generated candidates are disabled by a measured one-variable ablation after all3 generated-grasp selections failed in the15-seed development sweep. Orientation: public initial tool orientation composed with generic quarter-turn yaw for fallback jaw direction.
- Initial bowl center/radius: public geometry pose and projected point-cloud quantiles; no stored object dimensions.
- Placement XYZ: stove point-cloud medians/upper quantiles, front-center bound using0.6 times observed bowl radius, and measured held EEF-to-bowl offset. No copied snapshot pose.
- Held geometry: public localization in literal `bowl` prompt on agentview then wrist camera. Bounds use observed bowl span, live EEF, and initial observed top. Values0.2/1.8/2/3 are relative span guards;30mm is generic lift-evidence margin and10mm generic depth margin.
- Motion constants:35mm Cartesian staging,140mrad joint increments,25mrad joint tolerance,18mm Cartesian acceptance,50mrad final joint acceptance,1mrad progress test. These are generic convergence/control settings; no hidden controller values were read.
- Clearances:120mm pregrasp and300mm transit above observed object/target height. These are tuned relative clearances, not absolute world heights or asset dimensions.
- Release: +25 mm is a vertical target offset relative to the measured held relation and stove surface. The lower-motion catch-all Exception handler checks only measured XY distance <=25 mm before allowing release. Its lower_contact_blocked label is a heuristic after any lower exception, not direct evidence of physical contact.
- Bounds:24 joint stages;18 ticks per staged joint call;3 stalled stages;no generated-grasp call;40 held points and20 localization points;15 intended settling calls (typed invalid_request;0 executed settling ticks due own omitted embodiment). Index/shape/arithmetic values0/1/2/3 and quantile fractions carry no scene geometry. `cap=160` is an unused inherited function argument.
- All action dimensions, measured joints, poses, frame names, and point coordinates come from public API returns. Math is the only import. No filesystem/network/evaluator access is present inside policy.

Evaluation evidence: selected v08 measured14/15 development task success and 15/15 program_ok, followed by exactly one frozen-source unseen66–80measurement: 13/15 task and 15/15 program_ok. Heldout1–50remains root-only and was never accessed. No later worker policy requests or tuning. fix_code.py is a byte-identical copy made after full coverage and access/provenance audit PASS.
