# 红方块叠到绿方块上

- 任务：`robosuite/cube_stack:0`
- 正式成绩：**95/100（95%）**
- 定稿轮次：`original`；run ID：`36b52071f46795fc`
- 代码 SHA-256：`7fc56577e5ba890f62f109f65e544664d73fc8448ee9403e1673df040cb518db`
- 重要说明：此项已完成正式评测。程序正常返回不等于任务成功，具体以逐seed原始结果为准。

从 [final/fix_code.py](final/fix_code.py) 开始；`final/code/` 保存策略版本，`final/` 保存原始发现、技能报告、配置和审计说明。`history/`（如有）保存未选中的历史尝试。不得把历史失败或重试混为同一轮结果。

[逐seed正式结果](evidence/episodes.json) 与 [原始正式清单](evidence/formal-manifest.json) 可交叉核对。失败的轻量日志在 `evidence/failures/`（有本地记录时导出）。视频、逐帧图像、完整动作轨迹和压缩归档仍在本地备份，未放入 Git。

执行环境与新输出目录要求见 [运行说明](../../../../../RUNNING.zh-CN.md)。策略由 cap-harness 注入公共 API 后执行，不能直接 `python fix_code.py`。
