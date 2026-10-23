# 抓起并举起方块

- 任务：`robosuite/cube_lifting:0`
- 正式成绩：**100/100（100%）**
- 定稿轮次：`original`；run ID：`a317c464f031949f`
- 代码 SHA-256：`8db784f33c140d5a5fb718c3a351d1b2e7f8ffc263b60ef4a46ff40feba68912`
- 重要说明：此项已完成正式评测。程序正常返回不等于任务成功，具体以逐seed原始结果为准。

从 [final/fix_code.py](final/fix_code.py) 开始；`final/code/` 保存策略版本，`final/` 保存原始发现、技能报告、配置和审计说明。`history/`（如有）保存未选中的历史尝试。不得把历史失败或重试混为同一轮结果。

[逐seed正式结果](evidence/episodes.json) 与 [原始正式清单](evidence/formal-manifest.json) 可交叉核对。失败的轻量日志在 `evidence/failures/`（有本地记录时导出）。视频、逐帧图像、完整动作轨迹和压缩归档仍在本地备份，未放入 Git。

执行环境与新输出目录要求见 [运行说明](../../../../../RUNNING.zh-CN.md)。策略由 cap-harness 注入公共 API 后执行，不能直接 `python fix_code.py`。
