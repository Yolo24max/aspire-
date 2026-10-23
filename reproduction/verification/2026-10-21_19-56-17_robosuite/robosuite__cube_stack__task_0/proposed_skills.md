# Candidate skills under independent verification

[
  {
    "trigger": "Empty parallel jaws approaching a top-down cube grasp after a runtime-derived yaw rotation. The first public move_to_pose times out with a partially reached free-space pose. Inputs position, downward and frame are the same existing perception-derived target pose and robot base frame; report is a dictionary with motions initialized to an empty list. Start at the current observed pose, target a stand-off0.15m above the cloud-derived grasp before descending. This wrapper reissues only typed timeout results, at most3 calls; use cap250 for pregrasp. No collision guarantee: do not retry a known obstructed contact. Each call can cost up to cap ticks, so worst-case3*250=750 ticks for pregrasp; observed selected whole policies409-533 ticks, with empty jaws during pregrasp and the cube only after closing. Preserve1000-tick whole-episode ceiling.",
    "evidence": "v01 to v02 changed only this move helper; task success15/25 to25/25 on full development101-125. Flipped103,108,109,110,113,114,118,119,123,124 with no regression. Sources frozen and original public traces retained. Requires independent verifier before promotion.",
    "title": "Bounded public pose convergence after a rotated pregrasp timeout",
    "skill": "transport.md",
    "code": "def move(position, cap=220):\n    for attempt in range(3):\n        motion = move_to_pose(Pose(position, downward, frame), tolerance=0.015, max_steps=cap)\n        report[\"motions\"].append(motion)\n        if motion.ok:\n            return\n        if motion.status != \"timeout\":\n            break\n    raise ValueError(\"motion failed after bounded convergence retries\")"
  }
]
