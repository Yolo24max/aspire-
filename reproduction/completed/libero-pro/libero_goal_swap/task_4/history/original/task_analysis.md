# Initial Task Analysis

- Actual task language: Put the bowl on the top of the drawer.
- Manipulated object and likely prompts: The visible grey bowl is the pick object; try `grey bowl`, then `metal bowl`, then `bowl` through public localization.
- Goal/handle and likely prompts: The black drawer cabinet is the support; try `black cabinet`, then `drawer cabinet`, then `cabinet`. The top support plane must be computed from its observed point cloud.
- Visible obstacles and plausible approach: The bowl is on the tabletop near the centre-right and the cabinet occupies the left side. Detect both before the arm blocks the wide camera, approach the bowl from above, lift vertically, then move at a derived clearance above the cabinet before descending onto its observed top plane.
- Interaction type: pick/place.
- Uncertainties to verify from later seeds: bowl segmentation and top-down grasp retention; whether the cabinet cloud exposes a usable top plane; the bowl-bottom-to-gripper clearance needed for release; and whether direct interpolation crosses the table or cabinet during transport.
