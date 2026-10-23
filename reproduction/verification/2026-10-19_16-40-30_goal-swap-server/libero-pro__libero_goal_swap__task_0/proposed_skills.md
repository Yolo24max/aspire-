# Skills Under Test

Proposals from `libero_goal_swap/task_0`. **They are staged here and are deliberately NOT in the shared library** — whether they get promoted is what your verdict decides. Do not go looking for them under `skills/`; this file is their only home. Re-solve the task from the library PLUS this file, without seeing the author's program.

The task's own program scores **37/50** held-out. Read that before drawing conclusions from your own score: on a task whose residual failure is kinematic, a low score of your own is expected and is **not** by itself a refutation. Judge each proposal on whether it transmits and whether its mechanism reproduces.

---

## 1. → `manipulation.md` — Stop normally on public episode termination during an articulated motion

**Trigger.** Inside an existing motion helper, motion is the documented ExecutionResult and result is the mutable report mapping. The helper returns a continuation boolean; its caller must check False and return immediately, including within a pull loop. A terminated flag is an episode boundary, not proof of success. The excerpt replaces an exception on every non-ok motion.

```python
if motion.terminated or motion.truncated:
    result["phase"] = "environment_ended"
    result["environment_terminated"] = bool(motion.terminated)
    result["environment_truncated"] = bool(motion.truncated)
    return False
```

**Evidence.** In one development trial, the earlier policy reached task_success=True but program_ok=False because it raised on the public TERMINATED status. Changing only terminal control flow made both flags pass. The selected policy used this same block and measured 15/15 task_success and 15/15 program_ok across the development partition. This is proposer provenance; independently test transmission. The policy never reads task success or reward.

---


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
