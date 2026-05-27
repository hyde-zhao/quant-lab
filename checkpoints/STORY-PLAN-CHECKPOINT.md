---
checkpoint_id: "STORY-PLAN-2026-05-14"
checkpoint_type: "story-plan-confirmation"
status: "confirmed"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-14"
current_phase: "story-execution"
source_adr: "process/ARCHITECTURE-DECISION.md"
source_story_backlog: "process/STORY-BACKLOG.md"
source_development_plan: "process/DEVELOPMENT-PLAN.yaml"
story_count: 13
wave_count: 5
created_by: "meta-po"
updated_at: "2026-05-14"
---

# Story Plan 检查点

本检查点用于确认 `story-planning` 阶段产物是否可作为后续 Story LLD 设计输入。用户已明确确认通过：13 个 Story、5 个 Wave、SP-Q1 至 SP-Q3 默认规划均作为后续 Story LLD 输入。当前允许推进到 `story-execution` 的 LLD 起草环节，但仍不得实现代码，不得写 `delivery/**`。

## 复核结论

| 检查项 | 结论 | 依据 |
|---|---|---|
| 允许产物存在 | 通过 | 已存在 `process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` |
| Story 卡片完整性 | 通过 | `process/stories/STORY-001` 至 `STORY-013` 共 13 张卡片均存在；`STORY-001` 已推进为 `approved`，其余保持 `draft` |
| Wave 数量 | 通过 | `process/STORY-BACKLOG.md` 与 `process/DEVELOPMENT-PLAN.yaml` 均记录 5 个 Wave |
| DAG 校验 | 通过 | `process/DEVELOPMENT-PLAN.yaml` 中 `dag_validation_result.conclusion=PASS`，无 cycle、无 invalid reference |
| 阻塞项 | 通过 | Backlog 中 `BLK-001` 为 CLOSED；SP-Q1 至 SP-Q3 为待确认问题，不阻断发起检查点 |
| 门控状态 | 通过 | `process/STATE.md` 推进为 `current_phase=story-execution`，`story_plan_status=confirmed`，`story_plan_confirmed=true` |
| 禁止范围 | 通过 | Story Plan 确认只允许进入 LLD 起草；仍不得实现代码、安装脚本或 `delivery/**` 文件 |

## 13 Story 摘要

| Story ID | 标题 | 优先级 | Wave | 依赖 | 当前状态 |
|---|---|---|---|---|---|
| STORY-001 | 工程基线与数据契约骨架 | P0 | W0 | 无 | approved |
| STORY-002 | 数据准备节流重试与 manifest | P0 | W0 | STORY-001 | draft |
| STORY-003 | 标准化 parquet 与数据质量报告 | P0 | W0 | STORY-001, STORY-002 | draft |
| STORY-004 | 离线 Data Loader 与合同校验 | P0 | W1 | STORY-003 | draft |
| STORY-005 | 动量信号与组合成交引擎 | P0 | W1 | STORY-004 | draft |
| STORY-006 | 指标、单次回测报告与 metadata | P0 | W1 | STORY-005 | draft |
| STORY-007 | 60 组参数扫描报告 | P0 | W2 | STORY-006 | draft |
| STORY-008 | 候选报告与聚宽人工验证模板 | P0 | W2 | STORY-007 | draft |
| STORY-009 | PIT 股票池 Provider 增强契约 | P1 | W3 | STORY-008 | draft |
| STORY-010 | 交易状态与不可交易约束 | P1 | W3 | STORY-009 | draft |
| STORY-011 | 涨跌停与事件 available_at 增强 | P1 | W3 | STORY-009 | draft |
| STORY-012 | 偏差审计报告 | P1 | W3 | STORY-010, STORY-011 | draft |
| STORY-013 | 策略扩展接口与 RSI/MACD 示例 | P2 | W4 | STORY-008 | draft |

## 5 Wave 摘要

| Wave | HLD 阶段 | Story | 串并行策略 | 退出目标 |
|---|---|---|---|---|
| W0 | M0 - 数据准备与缓存可追溯 | STORY-001, STORY-002, STORY-003 | 串行 | 三类 parquet、manifest、quality report 契约完成，支持后续 M1 离线读取 |
| W1 | M1 - 本地动量最小回测器 | STORY-004, STORY-005, STORY-006 | 串行 | 默认回测输出净值、指标和 metadata |
| W2 | M2 - 参数扫描与候选报告 | STORY-007, STORY-008 | 串行 | 60 行扫描 CSV 和不超过 4 组候选 CSV |
| W3 | M3 - 真实性增强 | STORY-009, STORY-010, STORY-011, STORY-012 | 串行规划 | PIT、交易状态、涨跌停 / 事件时点和偏差审计形成可增量交付路径 |
| W4 | M4 - 策略扩展 | STORY-013 | 单 Story 串行 | RSI/MACD 等策略接口复用数据加载、组合和指标层 |

## 待确认问题

| ID | 问题 | 默认规划 | 状态 |
|---|---|---|---|
| SP-Q1 | 是否确认 13 个 Story、5 个 Wave 的拆解粒度 | 作为本轮 Story 计划提交确认 | RESOLVED：用户确认通过 |
| SP-Q2 | 是否确认 M3/M4 进入 Backlog 但不阻塞 M0-M2 第一版本地主路径 | M3/M4 保持 P1/P2 draft Story | RESOLVED：用户确认通过 |
| SP-Q3 | 是否确认本轮不生成安装规格和安装脚本 | 遵循交接文件允许输出范围 | RESOLVED：用户确认通过 |

## 确认结果

用户已选择：确认通过。Story 计划合理，开始 Story LLD 设计。

## 门控声明

Story Plan 确认通过后：

- 允许推进到 `story-execution`。
- 首个可执行 Story 为 W0 / `STORY-001`，状态可推进为 `approved` 并分派 `meta-dev` 起草 LLD。
- `STORY-001` 的 LLD 输出后必须进入 Story LLD 人工确认检查点，确认前不得实现。
- `STORY-002`、`STORY-003` 依赖前置 Story，当前不并行起草 LLD。
- 不得实现代码。
- 不得写入 `delivery/**`。
