---
handoff_id: "META-DEV-CR006-BATCH-A-DEV-W2-S02-2026-05-19"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-zhu"
status: "completed"
created_at: "2026-05-19T21:45:00+08:00"
change_id: "CR-006"
batch_id: "CR006-BATCH-A"
story_id: "CR006-S02-canonical-gold-lightweight-engine-adapter"
wave_id: "CR006-DEV-W2"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_name: "dev-zhu"
  tool_name: "resume_agent"
  agent_id: "019e3b8b-14a3-78a2-942b-4c696480fd80"
  thread_id: "019e3b8b-14a3-78a2-942b-4c696480fd80"
  spawned_at: ""
  resumed_at: "not-provided-by-main-thread"
  completed_at: "2026-05-19T22:07:53+08:00"
  evidence_status: "completed-cp6-pass"
  evidence: "用户回报主线程已真实调度 meta-dev/dev-zhu，agent_id/thread_id=019e3b8b-14a3-78a2-942b-4c696480fd80；CP6 文件 process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md status=PASS；S02 4 passed，相关 57 passed，S01 扩展 27 passed，全量 115 passed。"
---

# Handoff: CR006 DEV W2 / S02

## 目标

请 meta-dev 在 W1/S01 CP6 完成后实现 `CR006-S02-canonical-gold-lightweight-engine-adapter`。CP5 已由用户人工批准，本 handoff 只授权按 S02 LLD 进入代码实现和 CP6 编码完成检查；不得跳过 CP6/CP7。

## 必读输入

- `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
- `process/checks/CP5-CR006-S02-canonical-gold-lightweight-engine-adapter-LLD-IMPLEMENTABILITY.md`
- `process/checks/CR006-DATA-CONTRACT-CP5-CONTEXT-2026-05-19.md`
- `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STATE.md`
- `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`

## 允许写入范围

- `engine/data_loader.py`
- `engine/backtest.py`
- `experiments/run_experiment_06_07.py`
- `experiments/run_experiment_08_10.py`
- `experiments/run_experiment_11_12.py`
- `experiments/run_experiment_13_15.py`
- `experiments/run_experiment_16_20.py`
- `experiments/run_experiment_21.py`
- `market_data/readers.py`
- `tests/test_cr006_lightweight_engine_adapter.py`
- `process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md`

如发现必须修改以上范围外文件，停止实现并回报 meta-po，不得自行扩大范围。

## 禁止范围

- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`README.md`、`docs/USER-MANUAL.md`、`delivery/**`。
- 不读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize、revalidate、replay 或回补 job。
- 不把 raw/manifest 或旧 repo `data/**` 作为轻量 engine 默认运行时输入。

## 实现边界

- P0 运行输入为 `market_data` canonical/gold reader。
- external `legacy_flat` 仅可作为可选兼容派生入口，不是默认事实源，也不得 fallback repo `data/`。
- 缺数据、质量失败和未授权路径必须返回结构化错误和只读补齐建议。

## CP6 要求

完成后写入 `process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md`，至少包含：

- Agent Dispatch Evidence：主线程真实 `spawn_agent` / `resume_agent` / `send_input` 的 agent_id/thread_id、时间和完成状态。
- 修改文件清单与是否超出允许范围。
- 执行命令与结果，最低要求：`uv run --python 3.11 pytest -q tests/test_cr006_lightweight_engine_adapter.py`。
- 安全声明：未触碰真实 `data/**`、未读取凭据、未执行真实 Tushare/lake 操作。
- 后续 CP7 建议验证范围。

## 调度门槛

- 本 handoff 是 CR006-BATCH-A 的 dev wave 2。
- 默认必须等待 W1/S01 CP6 PASS 后调度。
- S02 与 S03 共享 `market_data/readers.py`、`engine/backtest.py`，不得与 S03 并行。

## 完成回填

- 状态：`completed-cp6-pass`
- 执行 agent：`meta-dev/dev-zhu`
- agent_id / thread_id：`019e3b8b-14a3-78a2-942b-4c696480fd80`
- CP6：`process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md`
- 测试：S02 4 passed；相关 57 passed；S01 扩展 27 passed；全量 115 passed。
- 安全声明：未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取/打印 `.env`、真实 token 或 NAS 凭据；未执行真实 Tushare/lake/normalize/revalidate/replay job。
