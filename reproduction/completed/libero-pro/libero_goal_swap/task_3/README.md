# 打开上层抽屉并把碗放进去

- 任务：`libero-pro/libero_goal_swap:3`
- 正式成绩：**49/50（98%）**
- 定稿轮次：`retry_02`；run ID：`a8a61a6a6c3b516a`
- 代码 SHA-256：`11fdfca995faf2c82c7eee9f1174ee2f31c6e9e696ac055ada4dc2fd41fff026`
- 重要说明：定稿为用户授权的独立 retry_02；原始尝试存在协议问题，历史记录单独保留，不作为首次尝试成绩。

从 [final/fix_code.py](final/fix_code.py) 开始；`final/code/` 保存策略版本，`final/` 保存原始发现、技能报告、配置和审计说明。`history/`（如有）保存未选中的历史尝试。不得把历史失败或重试混为同一轮结果。

[逐seed正式结果](evidence/episodes.json) 与 [原始正式清单](evidence/formal-manifest.json) 可交叉核对。失败的轻量日志在 `evidence/failures/`（有本地记录时导出）。视频、逐帧图像、完整动作轨迹和压缩归档仍在本地备份，未放入 Git。

执行环境与新输出目录要求见 [运行说明](../../../../../RUNNING.zh-CN.md)。策略由 cap-harness 注入公共 API 后执行，不能直接 `python fix_code.py`。
