# 阅读、校验与重新评测

## 只复盘代码

不需要GPU或原服务器。任务README、最终策略、历史代码、JSON配置、审计报告和逐seed成绩都在 `reproduction/completed/`。先读最终策略，再根据失败seed和历史策略定位修改。完整视频和逐帧记录保存在原本机离线备份，不在仓库中。

```bash
python reproduction/verify_archive.py
```

此命令只校验本仓库的文件和成绩关联，不运行仿真。

## 搭建可执行环境

建议使用有NVIDIA GPU的Linux环境。依赖与CUDA要求以本仓库 `docs/host-setup.md`、`docs/libero-pro.md`、`docs/robosuite.md` 为准。第三方提交已锁定在 `configs/dependency-lock.json`，保留子模块引用。

```bash
git clone --recurse-submodules https://github.com/Yolo24max/aspire-.git
cd aspire-
bash scripts/bootstrap_libero.sh     # LIBERO-Pro
# 或 bash scripts/bootstrap_robosuite.sh
```

感知/规划模型服务需要按 `docs/environments.md` 配置；门控权重需要你自己的访问授权。仿真、模型服务与资产并不随代码归档自动具备。

## 重新评测示例

以下为新的独立复测，不能覆盖归档结果；必须使用全新的输出目录。策略由harness注入 `get_task_context`、感知、规划及运动公共API，不能直接用Python执行策略文件。

```bash
source .venv-libero/bin/activate
export LIBERO_CONFIG_PATH="$PWD/.libero"
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl EGL_PLATFORM=device
cap-harness run --benchmark libero-pro --suite libero_goal_swap --task-id 0 \
  --seed 1 --init-mode seeded --max-steps 1000 \
  --program reproduction/completed/libero-pro/libero_goal_swap/task_0/final/fix_code.py \
  --output-root outputs/independent-recheck-goal0
```

运行前先检查当前CLI帮助与已启动服务。逐任务的 `evidence/formal-manifest.json` 中保存原实验 `identity`（初始化模式、seed、相机、步数上限、代码哈希）。LIBERO正式评测为每任务50个seed，Robosuite为100个seed；它们的开发与未见seed分区不同，应按相应task原始报告恢复。不得把结构性smoke测试当作任务成功评测。

`reproduction/infrastructure/` 留作当时协调实现的复盘材料，部分模块从实验目录加载辅助文件；它们不是可直接运行的免配置一键恢复器。SSH恢复模块已将原服务器端点改为环境变量：`ASPIRE_SSH_HOST`、`ASPIRE_SSH_PORT`、`ASPIRE_SSH_USER`、`ASPIRE_SSH_KNOWN_HOSTS`，密码从环境或交互读取。`ASPIRE_SSH_INTERFACE_INDEX` 可选。导出清单记录了该模块改动前后的哈希；8份最终策略没有改动。连接信息应单独配置，避免将私密信息写进仓库。
