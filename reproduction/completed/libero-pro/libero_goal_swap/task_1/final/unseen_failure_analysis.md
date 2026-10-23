## Unseen residual regime

The exact-once frozen measurement scored 13/15 task success and 15/15 program_ok, close to the development result of 14/15. Residual failures are support-border placements on seeds 66 and 69, matching the observed development seed 65 regime. All six reported pose stages passed; final images show the bowl near the stove front/side edge with partial overhang, while the benchmark task result remains false. No new grasp or approach failure was observed.

Neither failed unseen run used the catch-all lower fallback: their lower stage passed its measured guard, and no lower_contact_blocked flag was reported. The flag is only a heuristic after any lower exception and is not evidence of physical contact.

The dedicated settling calls were rejected by the public API and advanced zero ticks; accepted retraction motions still advanced physics. It is unproven whether support contact, tilt or additional settling would change these outcomes. No hidden predicate was inspected, and no source change, new policy request or rerun followed the unseen measurement. These results support a remaining placement-border regime rather than a predicted heldout success rate.
