# 把碗放到抽屉柜顶部

- 任务：`libero-pro/libero_goal_swap:4`
- 正式成绩：**50/50（100%）**
- 定稿轮次：`retry_03`；run ID：`9ab7f7e487a965f5`
- 代码 SHA-256：`f60e9cd008601cf483bd4998f9786106f178f9a11c3ef3889c48642c3970cec1`
- 重要说明：定稿为用户授权的独立 retry_03。技能查阅台账缺失，已保留披露与报告修订；不能把50/50成功归因为已验证的技能库贡献。

从 [final/fix_code.py](final/fix_code.py) 开始；`final/code/` 保存策略版本，`final/` 保存原始发现、技能报告、配置和审计说明。`history/`（如有）保存未选中的历史尝试。不得把历史失败或重试混为同一轮结果。

[逐seed正式结果](evidence/episodes.json) 与 [原始正式清单](evidence/formal-manifest.json) 可交叉核对。失败的轻量日志在 `evidence/failures/`（有本地记录时导出）。视频、逐帧图像、完整动作轨迹和压缩归档仍在本地备份，未放入 Git。

执行环境与新输出目录要求见 [运行说明](../../../../../RUNNING.zh-CN.md)。策略由 cap-harness 注入公共 API 后执行，不能直接 `python fix_code.py`。
