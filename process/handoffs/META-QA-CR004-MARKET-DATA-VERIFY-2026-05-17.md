---
handoff_id: "META-QA-CR004-MARKET-DATA-VERIFY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-qa"
agent_name: "qa-he"
workflow_id: "local_backtest"
change_id: "CR-004"
story_id: "market_data"
wave_id: "CR-004"
status: "dispatched-test-strategy"
created_at: "2026-05-17T12:01:04+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e341d-d5fe-7ea2-95ae-a97a68ee1028"
  agent_name: "qa-shi"
  thread_id: ""
  spawned_at: "2026-05-17T12:07:19+08:00"
  resumed_at: ""
  completed_at: ""
  evidence: "主线程通过 spawn_agent 真实调度 meta-qa；agent_id=019e341d-d5fe-7ea2-95ae-a97a68ee1028, agent_name=qa-shi。本轮先执行 CR-004 测试策略准备，待实现完成后再执行正式 CP7 验证。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable_key: "meta-qa|local_backtest|CR-004|market_data|CR-004"
fork_context: false
---

# Handoff：CR-004 可移植市场数据组件验证

## 任务

请以 `meta-qa` 身份为 CR-004 输出测试策略并验证实现结果。重点验证默认路径 fake/offline、reader 只读、manifest 可追溯、canonical parquet schema、质量校验、多源比对接口边界、CLI smoke test 和既有回测 / Notebook 能力未回退。

## 前置门控

不得跳过以下条件：

1. `meta-dev` 已完成对应 Story 实现并提供 CP6 证据。
2. 对应 LLD / CP5 已确认。
3. 不存在未解释的真实联网、凭据、真实行情大文件或缓存入库。

## 最小上下文

请读取：

- `process/STATE.md`
- `process/changes/CR-004-MARKET-DATA-COMPONENT-2026-05-17.md`
- CR-004 对应 Story / LLD
- `market_data/`
- `tests/`
- `pyproject.toml`
- `uv.lock`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`
- `README.md`
- `docs/USER-MANUAL.md`

不要加载：

- 真实私有行情数据
- 凭据、token、cookie、session
- 无关历史失败轮次

## 验证清单

1. `uv lock --check` 或依赖一致性检查通过。
2. `uv run --python 3.11 pytest -q` 通过，新增测试覆盖 fake/offline 闭环。
3. 默认测试路径不发起真实网络请求。
4. fake connector 输出 raw + manifest，并可派生 canonical parquet。
5. reader 只读 canonical parquet，不触发 connector。
6. 质量校验能识别字段缺失、重复、异常价格或覆盖缺口。
7. 多源比对接口存在且可用 fake/reference 测试，不依赖真实 TickFlow / AkShare / Tushare。
8. CLI fake/offline smoke test 通过。
9. 实验十 / 十二接入若已实施，必须只读 reader，不直接联网。
10. 未提交凭据、真实生产行情、`__pycache__/`、`.pyc`、notebook checkpoint 或大缓存。

## 完成输出

请输出 PASS / FAIL、阻塞项、建议项、命令证据、涉及文件和 CP7 可用的 Agent Dispatch Evidence 文本。若 FAIL，需要列明返工目标 agent 和具体修复点。没有真实平台调度证据前，不得把本 handoff 标记为 completed。
