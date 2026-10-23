# ASPIRE 已完成任务复现与代码复盘

本仓库整理截至 **2026-10-22** 已完成的 **8个 ASPIRE 任务**，于2026-10-23发布。包含最终控制代码、历史策略、正式评测配置、逐seed结果、失败日志及技能/协议审计说明，共覆盖 **550次正式评测**。

这是个人复现实验归档。上游项目为 [NVlabs/ASPIRE](https://github.com/NVlabs/ASPIRE)，实验记录中的上游基线提交为 `fa00f0ef2bc1d91d594b9aa502c22133c9f538f7`。保留 NVIDIA 上游 LICENSE、NOTICE 和框架源码；本仓库成绩不代表上游论文原始模型或全量基准成绩。

| 类别 | 任务 | 正式成绩 | 定稿轮次 |
|---|---|---:|---|
| libero-pro | [打开中层抽屉](reproduction/completed/libero-pro/libero_goal_swap/task_0/README.md) | 37/50 | original |
| libero-pro | [把碗放到炉灶上](reproduction/completed/libero-pro/libero_goal_swap/task_1/README.md) | 42/50 | original |
| libero-pro | [把酒瓶放到抽屉柜顶部](reproduction/completed/libero-pro/libero_goal_swap/task_2/README.md) | 50/50 | original |
| libero-pro | [打开上层抽屉并把碗放进去](reproduction/completed/libero-pro/libero_goal_swap/task_3/README.md) | 49/50 | retry_02 |
| libero-pro | [把碗放到抽屉柜顶部](reproduction/completed/libero-pro/libero_goal_swap/task_4/README.md) | 50/50 | retry_03 |
| robosuite | [抓起并举起方块](reproduction/completed/robosuite/cube_lifting/task_0/README.md) | 100/100 | original |
| robosuite | [红方块叠到绿方块上](reproduction/completed/robosuite/cube_stack/task_0/README.md) | 95/100 | original |
| robosuite | [交换上下方块后重新堆叠](reproduction/completed/robosuite/cube_restack/task_0/README.md) | 100/100 | original |

## 从哪里开始

1. 点击上表任务：先读任务README，再读 `final/fix_code.py`。
2. 对照 `final/code/`、`findings.md`、`task_analysis.md`、技能报告及审计JSON阅读修改原因。
3. 用 `evidence/episodes.json` 和原始 `formal-manifest.json` 对照成功/失败seed；可用的失败日志在 `evidence/failures/`。
4. [运行说明](RUNNING.zh-CN.md) 说明环境、公共API注入和新输出目录要求；[完整性检查](reproduction/verify_archive.py) 检查源文件及最终策略哈希。

## 目录

```text
reproduction/completed/       # 8个已完成任务；final与history明确分开
reproduction/results.json     # 汇总成绩、配置、run ID、最终代码SHA-256
reproduction/infrastructure/  # 当时使用的协调、评测、审计与断线恢复脚本
reproduction/source-manifest.json # 已导出文件的来源与SHA-256
src/cap_harness/              # ASPIRE框架源码
scripts/ configs/ tests/      # 环境搭建、锁定依赖、上游测试
docs/ examples/               # 上游接口、任务与运行说明
```

## 结果口径和限制

- Goal-Swap任务3采用 `retry_02`，任务4采用 `retry_03`，原先失败或协议无效尝试单独保留，不称作首次尝试成绩。
- Goal-Swap任务4存在技能查阅台账缺口；50/50是任务评测成绩，不能据此声称技能复用机制已得到完整验证。
- Robosuite有3项正式成绩；螺母装配、擦拭、双臂抬锅、双臂交接尚未完成。BEHAVIOR也没有完成正式任务评测。本仓库未将它们列为成果。
- 上游框架支持更多任务；框架包含某任务接口，并不代表本仓库已完成该任务。
- 本仓库导出代码和轻量证据。大体积视频、逐帧观察、完整动作轨迹、权重与数据资产仍保存在本地离线备份，未上传 GitHub。原始清单中的绝对路径是实验溯源信息，不是当前可访问的仓库链接。
- `reproduction/infrastructure/` 是实验现场脚本，含当时的目录约定；恢复运行前需重新配置路径、连接及资源。不要直接启动旧协调器重复正式seed。

## 许可与出处

ASPIRE上游代码沿用 [Apache-2.0许可证](LICENSE) 和 [NOTICE](NOTICE)。第三方代码使用 `.gitmodules` 与 `configs/dependency-lock.json` 锁定引用，不重新分发模型权重或资产。上游原README见 [docs/upstream-README.md](docs/upstream-README.md)。
