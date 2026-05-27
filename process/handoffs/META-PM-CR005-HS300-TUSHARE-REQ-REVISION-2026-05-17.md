---
handoff_id: "META-PM-CR005-HS300-TUSHARE-REQ-REVISION-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-pm"
status: "completed"
created_at: "2026-05-17T18:33:09+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-HS300-REQ-REVISION"
wave_id: "CR005-ROUND3-REVISION"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-pm"
  agent_path: ".codex/agents/meta-pm.toml"
  tool_name: "spawn_agent"
  agent_id: "019e3584-ec41-7c32-bbf9-ffe4175d47f9"
  agent_name: "pm-feng"
  thread_id: "019e3584-ec41-7c32-bbf9-ffe4175d47f9"
  spawned_at: "2026-05-17T19:02:35+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T19:02:35+08:00"
  evidence: "用户回报主线程已通过 spawn_agent 真实并行调度 meta-pm；agent_id=019e3584-ec41-7c32-bbf9-ffe4175d47f9，nickname=pm-feng，status completed then closed。meta-pm 已按本 handoff 修订 USE-CASES、REQUIREMENTS 和 CR-005，新增 UC-07、REQ-059..REQ-070，并补齐 BenchmarkResult、remediation_job_spec、Tushare 写湖/backfill job、consumer no-network/no-connector、proxy_baseline 隔离、Backtrader optional backend 边界、AC-018/019 和需求映射。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 第三轮 hs300 / Tushare 需求基线修订

## 任务

请以 `meta-pm` 身份修订 CR-005 相关需求与场景基线，不实现代码。

必须处理第三轮评审的 product lane 阻断项：

1. 增量更新 `process/USE-CASES.md`，补齐本地 `hs300_index` benchmark 缺失后的只读消费与数据准备补齐场景。
2. 增量更新 `process/REQUIREMENTS.md`，补齐正式需求与验收：`hs300_index` 本地基准、Tushare 写湖补齐作业、structured `unavailable/required_missing`、`next_action` / `remediation_job_spec`、benchmark 口径、coverage / quality / gap explanation、consumer no-network/no-connector、Backtrader optional backend 边界。
3. 更新 CR-005 文档处理决策，明确 `USE-CASES.md` / `REQUIREMENTS.md` 是本轮受影响正式文档，采用增量更新并保留旧基线。
4. 明确“数据层调用 Tushare”只指 `market_data` 写湖 / 数据准备层显式调用，不指 `engine/data_loader.py`、实验入口、benchmark resolver 或 Backtrader 自动联网。
5. 将 CR005-AC-001..014 与新增需求条目建立可追溯映射，并补齐数据准确性 / 可用性 AC。

## 最小上下文

- `process/STATE.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-SUMMARY.md`
- `process/checks/REVIEW-CR005-HS300-TUSHARE-META-PM.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `process/USE-CASES.md`
- `process/REQUIREMENTS.md`
- `process/HLD.md` §22
- `process/STORY-BACKLOG.md`

## 禁止事项

- 不得实现代码、修改 `pyproject.toml` / `uv.lock`、写真实数据或 token。
- 不得进入 CP5。
- 不得删除旧需求 / 旧场景基线；必须通过修订记录和 CR 映射保持追溯。

## 完成后

请回填本文件 frontmatter 的 dispatch 证据，并在结果中列出修改文件、需求 ID / 场景 ID、仍需 meta-se 消费的决策项。

## 完成结果

- 状态：completed then closed。
- 修改文件：
  - `process/USE-CASES.md`
  - `process/REQUIREMENTS.md`
  - `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- 关键结果：新增 UC-07；新增 REQ-059..REQ-070；补齐 `BenchmarkResult`、`remediation_job_spec`、Tushare 写湖/backfill job、consumer no-network/no-connector、`proxy_baseline` 隔离、Backtrader optional backend 边界；CR-005 新增 AC-018/019 和正式需求映射。
