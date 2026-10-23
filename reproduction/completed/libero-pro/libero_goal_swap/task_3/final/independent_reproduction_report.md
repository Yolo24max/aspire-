# ASPIRE task 3：独立重跑 retry_02

本轮经用户明确授权，由不继承原轮历史的新代理独立开发。原 task 3 的超预算及禁用示例程序问题已保留违规标记；本结果不修复、不覆盖原轮记录。

任务：Open the top layer of the drawer and put the bowl inside。

| 分区 | task_success | program_ok | 使用次数 |
|---|---:|---:|---|
| 开发 51–65 | 15/15 | 15/15 | 按预算迭代后，所选 v07 完整覆盖 |
| unseen 66–80 | 15/15 | 15/15 | 冻结后一次测量 |
| 正式 heldout 1–50 | 49/50 (98%) | 50/50 | 同一冻结源码，每例一次 |

正式未成功种子：[25]。program_ok 为 false 的种子：[]。这些结果只作最终测量记录，没有用于修改策略或重测失败例。

开发共使用 8 个策略源码版本，各失败模式最多 3 版；初始公开观察与冻结技能库的隔离校验通过。最终源码为 `code/v07_staged_lift_confidence.py`，与 `fix_code.py` 字节一致；SHA256 为 `11fdfca995faf2c82c7eee9f1174ee2f31c6e9e696ac055ada4dc2fd41fff026`。冻结技能库哈希为 `eb66214c23cc9d5a`。

正式验证使用 seeded 初始化、每例独立进程、1000 步上限、800×512 双相机、GPU 0。验证 identity 为 `a8a61a6a6c3b516a`。种子 1–50 完整且无重复；各例源码、设置、最终状态和 manifest 计数一致。50 例完整证据均已本地备份并逐文件校验，100 段相机视频的 SHA256 校验通过。服务端仅在确认本地备份后回收大体积载荷，保留元数据、源码、轨迹和备份位置记录。

## 结果的解释范围

成功率按官方原生 `task_success` 统计，`program_ok` 单列。开发和 unseen 的成功例均在下放过程中触发成功并终止，尚未执行释放及静置，因此不能据此声称已经验证释放后稳定放置。冻结源码的静置尾段含文档未支持的 `ArmCommand(embodiment=...)` 参数；该尾段在 Stage1 成功例中未被执行，源码在正式评测前后均保持不变。

v07 同时改变两项行为，观测只支持完整策略的表现，不支持单项改动的因果归因。技能报告的 14 项“有用”评级只补充到现有条目的应用记录；没有新技能或技能修改提案，也没有未经验证的配方入库。后续实时技能库哈希为 `c050e38ea9eff52c`，本轮冻结快照不变。

## 核对入口

- [最终统计](coordinator_reproduction_summary.json)
- [Stage1 交接审计](coordinator_handoff_audit.json)
- [来源与 API 审计](coordinator_provenance_review.json)
- [正式验证审计](coordinator_validation_audit.json)
- [100 段视频索引](validation_all_camera_video_index.json)
- [完整备份校验凭证](validation_offload_receipt.json)
- [技能库应用记录](coordinator_library_curation.json)

截至本轮结束，本 campaign 的 task 0–3 已完成正式验证（task 3 明确为独立 retry_02）；task 4–9 尚未完成。未启动 task 4。
