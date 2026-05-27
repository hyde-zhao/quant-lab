---
handoff_id: "META-SE-CR005-TUSHARE-BACKTRADER-HLD-STORY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-se"
status: "completed"
created_at: "2026-05-17T16:56:29+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-PLAN"
wave_id: "CR005-SOLUTION-DESIGN"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".codex/agents/meta-se.toml"
  tool_name: "spawn_agent"
  agent_id: "019e352c-458a-7412-9215-cdfb862f6c09"
  agent_name: "se-wei"
  thread_id: "019e352c-458a-7412-9215-cdfb862f6c09"
  spawned_at: "2026-05-17T17:17:29+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T17:17:29+08:00"
  evidence: "用户回报主线程已通过 spawn_agent 真实并行调度 meta-se；agent_id=019e352c-458a-7412-9215-cdfb862f6c09，nickname=se-wei，状态 completed。meta-se 已完成 CR-005 HLD/ADR/Story Backlog/Development Plan 修订并新增 CR005-S01..S06 Story 卡片。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 Tushare + Backtrader 方案与计划修订

## 任务

请以 `meta-se` 身份完成 CR-005 的方案层和计划层修订，不实现代码。

必须处理：

1. 将 Backtrader 并入 CR-005，而不是新建 CR-006。Backtrader 是当前主项目的可选回测后端，不是独立项目，也不是默认主框架。
2. Tushare 只进入本地数据湖写入链路：raw / manifest / canonical / quality / catalog / gold。不得把 Tushare API 直接接入 `engine/data_loader.py`、`engine/backtest.py`、实验十或实验十二。
3. Backtrader 只消费本地 canonical/gold + quality gate，不直接联网、不读取 `TUSHARE_TOKEN`、不导入 `market_data.connectors`。
4. 更新 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`。必要时新增 `process/stories/CR005-*.md` Story 卡片，但不得输出 LLD 或代码。
5. 建议 Story 组至少覆盖 CR005-S01..S06，其中 CR005-S06 为 Backtrader optional backend。请根据依赖 DAG 调整 Wave，不得让 Backtrader 早于本地 canonical/gold 数据契约稳定。

## 最小上下文

- `process/STATE.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- 代码事实：
  - `market_data/contracts.py`
  - `market_data/config.py`
  - `market_data/source_registry.py`
  - `market_data/connectors/tushare.py`
  - `market_data/readers.py`
  - `engine/backtest.py`
  - `engine/data_loader.py`
  - `pyproject.toml`

## 禁止事项

- 不得实现真实 Tushare 调用。
- 不得新增 Backtrader 代码或修改 `pyproject.toml` / `uv.lock`。
- 不得写真实行情数据、token、凭据、`data/**` 大文件或联网默认测试。
- 不得推进 CP5 或授权 meta-dev 实现。

## 完成后回填

主线程通过 `spawn_agent` 调度后，请回填本文件 frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`spawned_at`、`completed_at` 和结果摘要，并同步 `process/STATE.md.agent_lifecycle.active_agents`。
