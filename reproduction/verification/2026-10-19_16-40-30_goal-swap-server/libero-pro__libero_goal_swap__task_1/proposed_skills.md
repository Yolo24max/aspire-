# Skills Under Test

Proposals from `libero_goal_swap/task_1`. **They are staged here and are deliberately NOT in the shared library** — whether they get promoted is what your verdict decides. Do not go looking for them under `skills/`; this file is their only home. Re-solve the task from the library PLUS this file, without seeing the author's program.

The task's own program scores **12/50** held-out. Read that before drawing conclusions from your own score: on a task whose residual failure is kinematic, a low score of your own is expected and is **not** by itself a refutation. Judge each proposal on whether it transmits and whether its mechanism reproduces.

---

## Edits

### `grasp.md` § Standard Pick-and-Place Template

**Change.** Replace the unqualified preferred-for-irregular-objects backend comment with a conditional choice and a measured application record: returned top_down candidates remain contact hypotheses and require observed object-lift verification; public-geometry alternatives can outperform them on open bowls. Record task1 v07 generated-grasp0/3 versus v08 geometry-rim14/15 as task-specific evidence, without a universal backend ranking or an untested selection threshold.

*Why:* All3 generated-grasp selections in v07 failed54/57/60; forcing the existing manual rim path in v08 flipped those3 and preserved the other outcomes,11/15 to14/15. This edit qualifies guidance; it does not propose a new untested controller or geometry rule.


---

## Standing disputes — report on any your scene touches

- **Identity selectors.** `localize.md` orders them: the relation the instruction states, else the
  sign of the support gap, else the candidate's own height, else proximity. Tasks measured these
  head to head and got different answers on different scenes. **Compute all of them in-program and
  report the column.**
- **The near-base descent.** Two regimes with opposite remedies — settle-time (more ticks fix it)
  and a servo wall (they do not). The `>= ~50 ticks` duration bar is RETIRED; so is the
  outward-drift test, which one task measured backwards. What survives is **where it froze**
  (achieved z against commanded z) and **which axis is short**. Report both.
- **The jaw as a slip test.** Five numeric bars have been tried and all five failed; a jaw that
  *rises* is a distinct signal (something is prying it). If you deliberately spoil a grasp, report
  the jaw at close / after lift / before place for both it and a good one.
- **Release height.** Measure your band and grade on the landed pose, not the pass count.
- **The first `move_to_pose`.** `tries=3` and stage only if all three fail. Report what yours does.

Verifications have refuted claims outright while their symptoms held, and found helper functions
that entries CALL and that were defined nowhere. Treat "it passed" as the beginning of the question.
