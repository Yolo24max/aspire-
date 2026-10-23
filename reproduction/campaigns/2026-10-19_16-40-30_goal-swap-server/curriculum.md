# Initial curriculum

Single-GPU serial campaign for all ten libero_goal_swap tasks.

The supplied library contains localization, grasp, transport, and articulated-manipulation templates. No new skill has been verified or promoted in this campaign.

First: task 0, beginning with the public scene snapshot on development seed 51. Use its authoritative language and observation to choose the initial strategy. The other nine tasks remain pending until their turn. Task order may be revised from verified skills and observed requirements.

Development seeds 51-65; unseen check 66-80; held-out 1-50. Each task completes development before coordinator-owned held-out evaluation.


## Round 2 — 2026-10-19T10:41:23.065018+00:00

Library now covers localization, grasp, transport and manipulation scaffolds, with task0 application records and no newly promoted recipe. The completed task0 measured37/50 heldout; its new public-terminal-control proposal awaits independent verification.

Picked: isolated verifier for libero-pro/libero_goal_swap/task0 on the now-free GPU0. A transferable control-flow rule can help later task policies stop cleanly.

Deferred: remaining nine task episodes until this serial verification ends. Root already generated a fresh observation-only verifier scene after all50 evaluation trials completed. Verifier sees no proposer source or failure-seed identities. All future seeds run in fresh independent processes under the machine equivalence verdict.

## Round 3 — task 1

The task 0 verifier refuted its proposed terminal-control rule, so the canonical library remains unchanged. Task 1 completed Stage 1 on development seeds 51–65 (14/15) and one unseen sweep on 66–80 (13/15); its frozen selected source is `6c869cea3ba5bf7de27faa32cac7387dd53da2041d3349733581c907db8f7226`. The coordinator began the 50-seed held-out evaluation. Seeds 1–16 finished before the server reset and were recovered from individually SHA-verified local archives; only seeds 17–50 remain to run. The task 1 skill proposal still needs an independent verifier.

## Round 4 — server recovery and task 2 preparation

The restored server passed 80/80 LIBERO structural smoke cases and a GPU reset. The task 1 seeded-layout audit found 50/50 distinct held-out layouts with no overlap against development seeds 51–80. SAM3 checkpoint upload is in progress, so no new task episodes are being launched yet. Task 2 was selected next. A preparatory worker copied a repository example before inspecting a scene; to preserve the skill's baseline-free Stage 1 measurement, that draft and its notes were moved outside the task directory into `infrastructure/reference-prep-task2/`. A fresh worker must generate task 2's official v00 from its own public seed-51 scene without reading that preparation. GPU 0 remains reserved for the task 1 held-out continuation until that evaluation and artifact backup finish.

The task 0 seeded-layout audit also found 50/50 distinct held-out layouts and no overlap with development seeds 51–80. Both tasks' six sampled seed signatures were stable within and across fresh processes with a fixed Python hash seed; all four free joints varied, and seeded versus saved initialization differed.

## Round 5 — task 1 measured and verifier handoff

The restored provider stack passed the final doctor and an 80/80 structural smoke sweep. SAM3's local weight checksum matched the uploaded checkpoint, and a synthetic segmentation call returned five masks. Task 1's resumed held-out evaluation finished without repeating the first 16 seeds: 42/50 task successes, 50/50 trials, exit 0, manifest complete. A verified per-case transfer is copying all raw runs and videos to the coordinator workspace; the final local evidence audit follows transfer completion. An independent verifier received only its permitted public task view and ran seeds 51–55 once. Those five outcomes and their logs were transferred with file-hash checks. A path-alias error interrupted only the final packaging step; packaging was recovered from existing runs without repeating any seed. Verifier diagnosis and a possible second attempt are pending. Task 2 remains next after task 1 verification.

## Round 6 — task 1 final audit; task 2 official start

Task 1 held-out evidence is complete in the coordinator workspace: 50/50 runs, 42/50 task successes, 46/50 program_ok, 100/100 camera videos. The local audit verified selected-source identity, seed partition, seeded initialization, capture settings, reported outcomes, and every video SHA-256. The independent skill verifier measured v01 and v02 on seeds 51–55, with 0/5 in each attempt; its verdict is refuted. No task 1 proposal was promoted into the canonical library. The task 2 public seed-51 scene archive was transferred with matching SHA-256. A new official task 2 worker, isolated from the preparatory example, is deriving code from that scene. Its first observation-only probe completed with program_ok=true; no task 2 success claim has yet been measured.

## Round 7 — task 2 frozen evaluation

Task 2 selected v04 after a clean seed-51 pilot. Its frozen source scored 15/15 development and 15/15 exact-once unseen, all program_ok. The handoff gate verified 30 selected-source runs and 60 camera videos, including source hashes and per-video SHA-256; the root provenance review found only public APIs and runtime-derived geometry. The skill report proposes changes, but none are promoted before independent verification. The coordinator launched 50 held-out seeds serially with per-case offloading. Initial admission stalled because the shared cgroup counted more than 20 GiB of reclaimable inactive file cache against raw headroom; the root released cache for its own SAM3 checkpoint and changed the episode guard to count inactive file cache with a 6 GiB reclaimable-headroom threshold. Seed 1 then completed successfully and its video payload was hash-verified off-server. No task 2 formal seed was repeated.

## Round 8 — task 2 measured; isolated skill verification

Task 2's frozen program completed all 50 held-out seeds with 50/50 task success and 50/50 program_ok. The coordinator verified the selected-source hash, seeded initialization, run metadata, and SHA-256 of all 100 videos after durable offload. A static check initially rejected an undefined helper in the skill proposal's illustrative code; the proposer repaired only that documentation example, and lint passed. A fresh seed-51 observation-only scene was generated for an independent verifier after formal evaluation. The verifier has access to the shared library and proposal, but not to the proposer's program or held-out artifacts; no task 2 skill is promoted pending its measured verdict. Task 3 is selected next after this serial verification frees GPU 0.

## Round 9 — verified bottle and cabinet patterns; task 3

The independent task 2 verifier built its own code from the library and staged proposal and passed all five development scenes 51–55 on its first attempt. The coordinator verified its five seeded outcomes, source identity and all ten video hashes. Its report marked both new patterns and two proposed edits sound; the coordinator merged them into grasp.md, transport.md and localize.md, retaining the untested side-grasp comparison as a limit. Library lint passed with zero rejections, undefined helpers, unhandled empty searches, dangling references or advisories; the new library hash is `eb66214c23cc9d5a`. Task 3 now starts from that library. GPU 0 remains serial: its fresh public seed-51 observation-only scene completed, and a new isolated worker receives only this task's public snapshot and the shared library.
