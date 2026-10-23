# v07 Constant Provenance Audit

Policy SHA256:0977105f67c596d36de5c61c7dbb0a4e9d27030dff512d755bfbe20ac5c30351

PASS. No task geometry was obtained from native state, assets, another task, fixed scene coordinates, or seed identities.

- Object/goal prompts: `grey bowl`/`bowl` and `stove`/`hot plate`, taken from authoritative task language and verified with selected public segmentation records.
- Grasp XYZ: current bowl point-cloud X85 percentile, geometry Y center, current Z95 percentile minus12mm generic rim offset. Generated top-down candidates remain first choice. Orientation: public initial tool orientation composed with generic quarter-turn yaw for fallback jaw direction.
- Initial bowl center/radius: public geometry pose and projected point-cloud quantiles; no stored object dimensions.
- Placement XYZ: stove point-cloud medians/upper quantiles, front-center bound using0.6 times observed bowl radius, and measured held EEF-to-bowl offset. No copied snapshot pose.
- Held geometry: public localization in literal `bowl` prompt on agentview then wrist camera. Bounds use observed bowl span, live EEF, and initial observed top. Values0.2/1.8/2/3 are relative span guards;30mm is generic lift-evidence margin and10mm generic depth margin.
- Motion constants:35mm Cartesian staging,140mrad joint increments,25mrad joint tolerance,18mm Cartesian acceptance,50mrad final joint acceptance,1mrad progress test. These are generic convergence/control settings; no hidden controller values were read.
- Clearances:120mm pregrasp and300mm transit above observed object/target height. These are tuned relative clearances, not absolute world heights or asset dimensions.
- Release: +25 mm is a vertical target offset relative to the measured held relation and stove surface. The lower-motion catch-all Exception handler checks only measured XY distance <=25 mm before allowing release. Its lower_contact_blocked label is a heuristic after any lower exception, not direct evidence of physical contact.
- Bounds:24 joint stages;18 ticks per staged joint call;3 stalled stages;10 grasp candidates;40 held points and20 localization points;15 intended settling calls (typed invalid_request;0 executed settling ticks due own omitted embodiment). Index/shape/arithmetic values0/1/2/3 and quantile fractions carry no scene geometry. `cap=160` is an unused inherited function argument.
- All action dimensions, measured joints, poses, frame names, and point coordinates come from public API returns. Math is the only import. No filesystem/network/evaluator access is present inside policy.

Historical evaluation evidence: v07clean seed51 success, then11/15full development task successes and12/15program_ok. v07was not run on unseen. Selected v08later measured14/15development and13/15exact-once unseen; see v08audit and coverage inventory.
