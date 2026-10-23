# 打开中层抽屉

- 任务：`libero-pro/libero_goal_swap:0`
- 正式成绩：**37/50（74%）**
- 定稿轮次：`original`；run ID：`292af3382f08f96c`
- 代码 SHA-256：`f887cdf810fc31953ed69dd918806bbdc82189e7faa1495332516e1ec89c7e23`
- 重要说明：此项已完成正式评测。程序正常返回不等于任务成功，具体以逐seed原始结果为准。

从 [final/fix_code.py](final/fix_code.py) 开始；`final/code/` 保存策略版本，`final/` 保存原始发现、技能报告、配置和审计说明。`history/`（如有）保存未选中的历史尝试。不得把历史失败或重试混为同一轮结果。

[逐seed正式结果](evidence/episodes.json) 与 [原始正式清单](evidence/formal-manifest.json) 可交叉核对。失败的轻量日志在 `evidence/failures/`（有本地记录时导出）。视频、逐帧图像、完整动作轨迹和压缩归档仍在本地备份，未放入 Git。

执行环境与新输出目录要求见 [运行说明](../../../../../RUNNING.zh-CN.md)。策略由 cap-harness 注入公共 API 后执行，不能直接 `python fix_code.py`。
