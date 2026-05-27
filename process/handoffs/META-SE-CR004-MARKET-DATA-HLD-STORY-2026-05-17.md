---
handoff_id: "META-SE-CR004-MARKET-DATA-HLD-STORY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-se"
agent_name: "se-chu"
workflow_id: "local_backtest"
change_id: "CR-004"
story_id: "market_data"
wave_id: "CR-004"
status: "completed"
created_at: "2026-05-17T12:01:04+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "spawn_agent"
  agent_id: "019e341d-d59e-7b23-8c26-4231e005c258"
  agent_name: "se-chu"
  thread_id: ""
  spawned_at: "2026-05-17T12:07:19+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T12:22:40+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-se；agent_id=019e341d-d59e-7b23-8c26-4231e005c258, agent_name=se-chu。meta-se 已完成 CR-004 HLD/ADR/Story 规划增量修订。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable_key: "meta-se|local_backtest|CR-004|market_data|CR-004"
fork_context: false
---

# Handoff：CR-004 可移植市场数据组件 HLD / Story 规划修订

## 任务

请以 `meta-se` 身份执行 CR-004 的方案设计和 Story 规划修订。目标是在不破坏既有本地回测交付物的前提下，定义仓库内独立包 `market_data/` 的架构、数据湖分层、connector 边界、最小可运行 Story DAG 和后续实验十 / 十二接入路线。

## 最小上下文

请读取：

- `process/STATE.md`
- `process/changes/CR-004-MARKET-DATA-COMPONENT-2026-05-17.md`
- `process/REQUIREMENTS.md`
- `process/USE-CASES.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `pyproject.toml`
- `engine/data_prep.py`
- `engine/akshare_adapter.py`
- `engine/normalizer.py`
- `engine/quality.py`
- `engine/data_loader.py`
- `experiments/run_experiment_10.py`
- `experiments/run_experiment_12.py`

不要加载：

- 完整会话 transcript
- 无关历史失败轮次
- 真实私有行情数据或凭据
- `__pycache__/`、`.ipynb_checkpoints/`、报告 PNG 等生成物

## 必须输出

1. HLD 增量修订建议：`market_data/` 独立包边界、数据湖层级、connector 接口、默认 fake/offline、真实 adapter 配置边界。
2. ADR 修订建议：回测主路径只读、真实联网 adapter 默认关闭、数据湖 canonical schema 与 manifest 契约。
3. Story 拆解：最小闭环 Story 与后续接入 Story，包含依赖 DAG、文件所有权、并行安全和验收标准。
4. 对实验十 / 十二和真实沪深 300 基准的接入路线：先 reader 只读接入，再切换真实基准数据，不直接联网。
5. 是否需要重开 CP3 / CP4，以及 CP5 批次策略建议。

## 文件写入边界

允许 meta-se 修改：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/STORY-*.md`（仅新增或修订 CR-004 相关 Story）

禁止 meta-se 修改：

- `market_data/**`
- `engine/**`
- `experiments/**`
- `tests/**`
- `pyproject.toml`
- `uv.lock`
- 真实数据、报告数据、凭据或 `delivery/**`

## 完成输出

请返回修改文件列表、设计结论、Story DAG、CP3 / CP4 / CP5 门控建议和开放问题。没有真实平台调度证据前，不得把本 handoff 标记为 completed。
