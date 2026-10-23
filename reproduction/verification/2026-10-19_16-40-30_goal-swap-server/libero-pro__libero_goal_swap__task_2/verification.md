# Independent verification: LIBERO-Pro Goal-Swap task 2

**Verdict: verified.** The first program attempt passed all five seeded development episodes (51–55), so no second attempt was used. The coordinator ran one fresh process per seed on GPU 0. Its recorded program source SHA-256 was `dfadce9b5748002ad7dfc1e5c8166f1628d1659a983f3be7a39ae54ff67f2e4f`, matching my `code/v01_from_skills.py`.

The public task language was “Put the wine bottle on the top of the drawer.” Before seeing the scene, I predicted that the proposed downward bottle-neck grasp, segmented cabinet-top transport, and two prompt-registry entries would apply. The scene showed one upright wine bottle and a black drawer cabinet; those predictions held. I used the shared grasp template's `quantile` helper, `close_gripper()` convention, and motion guards, then followed the proposed 80%-height target, 0.12 m pre-grasp, top-plane slice, measured grasp clearance, and three transport waypoints. The target prompts were exactly `wine bottle` and `black cabinet`.

| Seed | Program | Task | Steps | Bottle points | Cabinet points | Top-plane points | Release Z (m) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 51 | ok | success | 348 | 1591 | 8036 | 6227 | 0.34278 |
| 52 | ok | success | 347 | 1581 | 7791 | 5991 | 0.34324 |
| 53 | ok | success | 349 | 1593 | 7685 | 6003 | 0.34386 |
| 54 | ok | success | 354 | 1638 | 7054 | 5613 | 0.34432 |
| 55 | ok | success | 345 | 1619 | 9014 | 6534 | 0.34331 |

The `wine bottle` top segmentation score ranged 0.918–0.930; `black cabinet` ranged 0.365–0.500. Both selected masks and point clouds covered the intended objects on all five seeds. The cabinet's estimated top was at Z 0.21574–0.21577 m. The commanded release EEF Z was 0.1270–0.1286 m above that surface, placing the inferred bottle bottom about 0.012 m above it. Final keyframes show the bottle above the cabinet top after the jaws opened, and every run ended with `task_succeeded` during the 9–10 release ticks. This supports the release band in these scenes without an isolated or later settled-pose measurement.

The downward-neck proposal and its `grasp.md` cross-reference are **sound** here: the arm reached the neck from above, the bottle was visibly retained after lift, and five placements succeeded. The segmented cabinet-top proposal is **sound** here: all 15 lift, lateral transport, and lower stages completed, and five bottles reached the top. The prompt-registry edit is **sound**: both literal prompts worked on all seeds. These are whole-policy observations; I did not retest the earlier side-wrist failure or ablate the top-plane calculation.

The first `move_to_pose` had one attempt and succeeded on all five seeds, so the standing three-try question was not exercised. This scene had no competing bottle identity or near-base descent; the identity-selector, descent-stall, and spoiled-grasp jaw disputes were not exercised. I did not read proposer code, other task directories, examples, or other verifier workspaces. Reading rules: **RESPECTED**.
