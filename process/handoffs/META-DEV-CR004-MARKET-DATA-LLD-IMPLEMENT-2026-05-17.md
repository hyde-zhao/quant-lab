---
handoff_id: "META-DEV-CR004-MARKET-DATA-LLD-IMPLEMENT-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-xu"
workflow_id: "local_backtest"
change_id: "CR-004"
story_id: "market_data"
wave_id: "CR-004"
status: "completed-lld-batch-a"
created_at: "2026-05-17T12:01:04+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e3438-ba2b-7a70-8b60-4768ef960902"
  agent_name: "dev-xu"
  thread_id: ""
  spawned_at: "2026-05-17T12:36:38+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T12:45:43+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-dev；agent_id=019e3438-ba2b-7a70-8b60-4768ef960902, agent_name=dev-xu。本轮仅起草 CP5 批次 A（STORY-014 + STORY-015）LLD，不授权代码实现。meta-dev 已完成两个 LLD。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable_key: "meta-dev|local_backtest|CR-004|market_data|CR-004"
fork_context: false
---

# Handoff：CR-004 可移植市场数据组件 LLD / 实现

## 任务

请以 `meta-dev` 身份在 CR-004 的 HLD、Story 计划、CP3 / CP4 / CP5 门控满足后，输出 Story LLD 并实施最小可运行版本。目标是新增仓库内独立包 `market_data/`，实现 fake/offline 数据获取、数据湖写入、canonical 标准化、质量校验、只读 reader 和 CLI 闭环。

## 前置门控

不得跳过以下条件：

1. `meta-se` 已完成 CR-004 HLD / Story 规划修订。
2. 需要重开的 CP3 / CP4 已按 meta-flow 通过。
3. 当前 Story 或小批次 Story 的 CP5 LLD 已通过人工确认。
4. `process/STATE.md` 中该 Story 状态已进入 `dev-ready`。

## 最小上下文

请读取：

- `process/STATE.md`
- `process/changes/CR-004-MARKET-DATA-COMPONENT-2026-05-17.md`
- CR-004 对应 HLD / ADR / Story / LLD（由 meta-se 和 CP5 确认后提供）
- `pyproject.toml`
- `uv.lock`
- `engine/data_prep.py`
- `engine/manifest.py`
- `engine/normalizer.py`
- `engine/quality.py`
- `engine/data_loader.py`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`
- 相关 `tests/`

不要加载：

- 真实私有行情数据
- 凭据、token、cookie、session
- 无关历史 Story LLD
- `__pycache__/` 或 notebook checkpoint

## 实施边界

必须：

1. 新增 `market_data/` 包骨架，保持未来可迁移。
2. 实现 fake connector，默认测试和 CLI 示例均走 fake/offline。
3. 实现 planner / runtime / storage / normalization / validation / readers / cli 的最小闭环或等价模块职责。
4. manifest 记录 source、interface、params、attempts、status、raw_path、canonical_path、错误和时间信息。
5. canonical parquet schema 稳定，reader 只读 parquet，不触发 connector 或网络。
6. 真实 TickFlow / AkShare / Tushare adapter 只实现边界、配置入口和 fail-fast 行为；默认测试不得真实联网。
7. 使用 `uv` 管理依赖；新增依赖需更新 `pyproject.toml` 和 `uv.lock`。
8. 新增 pytest，覆盖 fake connector、重试/熔断、manifest、canonical parquet、质量校验、reader 和 CLI。

禁止：

1. 不真实联网抓全量行情。
2. 不提交任何凭据或 token。
3. 不把实验十 / 十二改成运行时自动联网。
4. 不删除既有 `engine/` 行为或 CR-002 / CR-003 产物。
5. 不提交真实生产行情、缓存大文件、`__pycache__/`、`.pyc` 或 notebook checkpoint。

## 建议验证

- `uv lock --check`
- `uv run --python 3.11 pytest -q`
- 针对新增 CLI 的 fake/offline 命令 smoke test
- 如新增依赖，先 `uv sync --python 3.11`

## 完成输出

请返回修改文件列表、依赖变更、实现摘要、已运行命令及结果、CP6 可用的 Agent Dispatch Evidence 文本。没有真实平台调度证据前，不得把本 handoff 标记为 completed。
