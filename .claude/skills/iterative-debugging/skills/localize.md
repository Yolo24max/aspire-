---
name: localize
description: Object localization via SAM3 — prompting strategies, multi-prompt fallback pattern, candidate disambiguation, and per-object prompt registry. Grows through experiment.
---

# Localize — SAM3 Prompting & Object Localization

> This skill tracks **what SAM3 prompts work for which objects** and the standard
> localization helper pattern. Prompt strings go in the registry table; any selection or
> filtering logic that needs code becomes its own subsection (trigger → code → evidence),
> modeled on *Disambiguation* below.
> Programs cannot import modules — all helpers below are pure Python over public contracts.

---

## Standard Localization Helper

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) applied prompt fallback and public cloud-size guards to cabinet and bowl localization. Its first clean seed-51 policy was v05; no helper ablation was performed.

**Application record (2026-10-19).** `libero_goal_swap/task_1` reported this section useful in public-API bowl placement; selected-source development 14/15 and exact-once unseen 13/15. Prompt fallback plus minimum-point guards correctly localized bowl and stove on51. v07 clean success; no isolated helper ablation. This records application, not isolated efficacy.


**Application record (2026-10-19).** `libero_goal_swap/task_0` used prompt fallback and point-count guards; localization completed in all 15 selected development scenes. Other manipulation stages were evaluated separately.

`localize_object()` already composes text segmentation, RGB-D projection, and geometry
estimation. Wrap it with a prompt-fallback loop and a minimum-point guard:

```python
def locate(queries, camera_name="agentview"):
    """Try prompts in order, return the first LocalizationResult with >= 20 points."""
    base_frame = get_robot_state().base_frame
    for query in queries:
        found = localize_object(query, camera_name=camera_name, target_frame=base_frame)
        if found.ok and len(found.point_cloud.points) >= 20:
            return found
    return None

bottle = locate(("<specific prompt>", "<fallback prompt>"))
if bottle is None:
    raise ValueError("object not found")
center = bottle.geometry.pose.position   # framed center from estimate_geometry
```

**Why the geometry center over a raw mean:** `estimate_geometry` gives a more robust center
for elongated or partially occluded objects than averaging raw points.

---

## Prompt Registry

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) reused `black cabinet` for the intended cabinet; the public seed-51 cloud supported that selection. This extends the application record, not the prompt's universal scope.

Discovered working prompts, indexed by object. Add entries as you find them.
List prompts in priority order — first hit wins. This table is for prompt strings and scores
only — if a finding needs procedure or code (candidate filtering, camera choice, occlusion
handling), write it as a subsection instead and keep at most a pointer row here.

| Object | Working Prompts | Benchmark/Suite/Task | Notes |
|---|---|---|---|
| Upright dark wine bottle | `wine bottle` | LIBERO-Pro / `libero_goal_swap` / task 2 | Independent verifier localized it on seeds 51–55; 1,581–1,638 points. |
| Closed black drawer cabinet | `black cabinet` | LIBERO-Pro / `libero_goal_swap` / task 2 | Independent verifier localized it on seeds 51–55; 7,054–9,014 points. |

---

## Disambiguation: Two Similar Objects in Scene

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) projected high-score handle candidates and selected the highest plausible cloud height. v04/v05 opened the intended top drawer on 51; this is not an isolated selection test.

**Application record (2026-10-19).** `libero_goal_swap/task_0` ordered three observed handle heights to select the middle handle instead of taking the highest segmentation score. All 15 selected development scenes reached that target.

When a scene contains two visually similar objects, the top-scored candidate is often the wrong
one. Inspect all candidates from `segment_text()` and discriminate by bbox pixel area, image
position, or projected 3D geometry:

```python
def smallest_box_candidate(camera_name, prompts, max_center_y=None):
    """Select the candidate with smallest bbox area (most compact matching shape).
    max_center_y: if set, only accept boxes whose center row is above it (upper image = farther).
    """
    for prompt in prompts:
        found = segment_text(camera_name, prompt)
        if not found.ok:
            continue
        best = None
        best_area = None
        for candidate in found.segmentations[:10]:
            if candidate.box_xyxy is None:
                continue
            x1, y1, x2, y2 = (float(value) for value in candidate.box_xyxy)
            area = (x2 - x1) * (y2 - y1)
            center_y = (y1 + y2) / 2.0
            if max_center_y is not None and center_y >= max_center_y:
                continue
            if best_area is None or area < best_area:
                best_area = area
                best = candidate
        if best is not None:
            return best
    return None
```

Project the selected candidate with `mask_to_point_cloud(candidate, camera_name)` and compare
observable geometry with `estimate_geometry()` — filter by 3D Z-height first when a taller or
larger object outranks the target, then pick the highest score among geometry-matching
candidates.

Never disambiguate with native simulator objects, hidden IDs, known seed coordinates, or fixed
pixel locations. Re-localize after contact or a failed grasp — the object may have moved; do not
reuse a stale center.

---

## Key Signals

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) distinguished populated CGN candidates from a `None` top-down selection in v04. The overlay supported the bowl mask before v05's fallback; mask identification alone did not verify grasp success.

**Application record (2026-10-19).** `libero_goal_swap/task_1` reported this section useful in public-API bowl placement; selected-source development 14/15 and exact-once unseen 13/15. Typed provider failures identified CGN and SAM3 OOM-only51 runs. Candidate ordering in typed JSON corrected an initial misreading of multi-box overlays. This records application, not isolated efficacy.


**Application record (2026-10-19).** `libero_goal_swap/task_0` treated weak, occluded post-pull masks as unavailable evidence rather than confirmation of retained grasp. No isolated ablation was performed.

- `segment_text(...).ok` false or zero `segmentations` → prompt not recognized — try a more
  specific or different description (the trace span records every candidate's score and box)
- `score < 0.5` → low confidence — try an alternative prompt before accepting
- `len(point_cloud.points) < 20` → mask too small or object occluded — try a different prompt
- `media/overlays/` in the recorded run renders the retained top-1 mask — verify it covers the
  intended object

---

## Prompting Strategy

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) read authoritative task language and localized `black cabinet` and `grey bowl` before manipulation. v05 reached the first clean seed-51 success; causal contributions were not isolated.

**Application record (2026-10-19).** `libero_goal_swap/task_1` reported this section useful in public-API bowl placement; selected-source development 14/15 and exact-once unseen 13/15. Read authoritative runtime language and localized stove before grasp. grey bowl and stove selected correct masks on51; selected v07 succeeded. This records application, not isolated efficacy.


**Application record (2026-10-19).** `libero_goal_swap/task_0` read the runtime goal and localized before grasping. Its selected policy measured 15/15 development and 12/15 unseen successes; these are whole-policy results.

1. **Be specific first** — include color + shape + material: `"blue rectangular box"`
2. **Fall back to generic** — shorter, simpler descriptions; prefer category or shape prompts
   when a product-specific prompt is unreliable
3. **For targets (bowls, plates, racks)** — a material descriptor helps: `"silver bowl"` > `"bowl"`
4. **Always confirm with `get_task_context().language`** — the authoritative instruction
   regardless of suite or task name
5. **Detect target BEFORE grasping** — post-lift re-observation is corrupted by the robot arm
   blocking the camera; detect both object and target while the arm is at home position and the
   view is clean
6. **ARM OCCLUSION PATTERN** — if the target object is in the CENTER of the table, it may be
   hidden behind the robot arm at home position. Move the arm to an observation pose with
   `move_to_pose` before observing. Symptom: SAM3 finds other objects but not the target, and
   scores are low (<0.2) for the intended object.

---

## Placement Z Notes

**Application record (2026-10-20).** `libero_goal_swap/task_3/retry_02` (development 51–65; unseen 66–80) used public quantiles and an observed held-bowl-to-EEF relation rather than treating the cloud centroid as support height. Success terminated during lowering; post-release settling was not measured.

**Application record (2026-10-19).** `libero_goal_swap/task_1` reported this section useful in public-API bowl placement; selected-source development 14/15 and exact-once unseen 13/15. Observed clouds represent visible surfaces. v07 measured held bowl relation rather than assuming initial center offset;51 succeeded, causal contributions not isolated. This records application, not isolated efficacy.


A mask's projected Z reflects the **camera-facing surface**, not the true top.
For targets with vertical extent (bowls, raised platforms), adjust placement Z from observed
run evidence.

| Target | Z formula | Notes |
|---|---|---|
