v00 — initial program from scene analysis
v00 — grasp-retention/IK: CGN returned no top-down candidate; the geometry fallback targeted below the bowl's reachable top and timed out on seed 51.
v01 — grasp approach: raise geometry fallback to observed bowl top plus a derived 0.02 m clearance.
v02 — grasp retention: v01 reached and released, but the bowl stayed on the table; use a derived side approach with a horizontal gripper orientation and public center/robot direction.
v03 — grasp retention and side IK: the handcrafted side quaternion was unreachable; use the highest-score public CGN candidate, preserving its observed pose and orientation.
v04 — grasp IK: the CGN pre-grasp offset timed out; try a direct move to the public CGN contact pose before closing.
v05 — contact strategy: lower the reachable top-down pose to observed rim plus 0.005 m and preserve close-gripper contact completion despite a final approach timeout.
v06 — grasp-retention verification: lower the observed rim contact by 0.003 m and require public post-lift re-localization; descent timed out before contact.
v07 — grasp-retention verification: reach the observed upper band, shift to a derived x-edge rim point, descend, close, and verify; motion completed but the bowl remained on the table and task_success was false.
v08 — controller rejected before launch: live-pose quaternion side grasp was prepared after top-down retention failures, but the official eight-version policy budget was exhausted.
SELECTED: v05_rim_contact.py — 0/15 development sweep (no full sweep authorized; seed-51 pilot program_ok true, task_success false); selected as the simplest measured program_ok-tie.
