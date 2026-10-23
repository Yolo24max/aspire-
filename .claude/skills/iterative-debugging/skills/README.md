# Shared Robot Skills

These files contain reusable, observation-only robot-control knowledge shared across
iterative-debugging campaigns. Pipeline orchestration belongs in the pipeline files one level up.

| Skill | Purpose |
|---|---|
| [grasp.md](grasp.md) | Grasp selection, orientations, grasp verification, and pick/place skeletons |
| [localize.md](localize.md) | SAM3 prompting, disambiguation, and 3D localization helpers |
| [transport.md](transport.md) | Waypoints, collision-free transit, and placement approaches |
| [manipulation.md](manipulation.md) | Drawers, knobs, switches, pushing, and other contact tasks |

All snippets use only the documented public CaP program APIs (`docs/api-reference.md`): no
imports, no NumPy, no simulator internals, and a top-level `result` variable per program.

Promoted findings should include provenance: source benchmark/suite/task, development seeds,
held-out result when available, source code path, and date. Avoid universal claims from one
scene or seed.

## How an entry gets here

**Application record (2026-10-20).** The isolated `libero_goal_swap/task_3/retry_02`
worker used only its frozen shared library as the cross-task channel and proposed no additions
or edits. Its selected policy measured 15/15 development (51–65) and 15/15 exact-once unseen
(66–80). The application records below describe whole-policy use, without isolated efficacy
claims; the original task-3 attempt remains protocol-invalid. No release/settling efficacy was
measured because successful episodes terminated during lowering.

Nothing is written into these files by the agent that discovered it. An entry arrives only by
this route, and every step is on disk:

```
subagent proposes  →  verifier reproduces the fix   →  coordinator promotes
(skill_report.json)   from the proposal ALONE          (edits this directory)
                      (verification_report.json)
```

The verifier gets the library and the proposal, and is denied the proposer's program, findings,
and run artifacts. If it cannot reach the fix on five seeds within two attempts, the proposal is
**refuted** and stays out. So an entry here means: *written down, on its own, this was enough for
an agent that had never seen the solution.*

What that does **not** mean is that the entry generalizes. Proposals are verified on the task
they came from, so passing shows the text transmits, not that it transfers. Evidence of transfer
accumulates separately, as later tasks grade the entry `useful` in their own reports — which is
why the evidence lines matter and why they should name every task, not just the first.

Entries are also graded on the way out. Every subagent reports each section it opened as `useful`,
`misleading`, `wrong`, or `not-applicable`, and the coordinator repairs what comes back bad
before dispatching more work. An entry that keeps drawing `misleading` usually has a trigger
problem — it is being read by tasks it was never meant for — and the fix is to narrow the
trigger, not to bolt a warning onto the end.
