v00 — initial program from scene analysis
v00 result — grasp-retention and target-perception failure on seed 51: CGN returned two candidates but top_down selection was None; the bowl remained on the table after release and the cabinet mask covered the rack.
v01 — grasp-retention: lower the observed-rim fallback into the bowl interior when top_down CGN selection is None
v01 result — grasp approach timed out at the lower fallback pose (program_error, no pickup evidence); the fallback was too low for this IK branch.
v02 — grasp-retention: choose a bounded CGN candidate near the observed bowl height when top_down selection returns None

v03 — grasp-retention: lower the top-down bowl fallback from bowl_top+0.005 to bowl_top-0.005 after v02 dropped the bowl during transport
v03 result — IK/planning failure: lowering fallback was not exercised because five CGN candidates were accepted; the top scored candidate was offset at y=-0.013 and pre-grasp timed out before contact (program_error).
v04 — ik-planning: re-anchor any accepted CGN orientation at the observed bowl center to avoid the out-of-workspace candidate pose
v04 result — IK/planning remained blocked: re-anchoring did not help because the accepted CGN orientation itself made the pre-grasp unreachable (147-step timeout).
v05 — execution: force the reachable top-down frame and shallow interior contact, bypassing unreachable CGN orientations
v05 result — execution failure: top-down shallow interior contact made the grasp approach timeout after a successful pre-grasp; target is below the reachable contact band.
v06 — execution: use the reachable bowl_top contact plane and repeat the close command before lift to improve retention
v06 result — execution completed but retention still failed: the bowl was back at its original tabletop position after lift despite a repeated close command.
v07 — perception: use task-language cabinet-top prompts before the generic black-cabinet fallback to reject the leaked rack/table mask
