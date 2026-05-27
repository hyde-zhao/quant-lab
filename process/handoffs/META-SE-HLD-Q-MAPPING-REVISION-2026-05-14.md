---
handoff_type: "revision-dispatch"
from_agent: "meta-po"
to_agent: "meta-se"
from_phase: "solution-design"
to_phase: "solution-design"
status: "hld_revision_required"
created_at: "2026-05-14"
created_by: "meta-po"
source_artifacts:
  - "process/STATE.md"
  - "process/HLD.md"
  - "checkpoints/CHECKPOINT-HLD.md"
blocked: false
allowed_outputs:
  - "process/HLD.md"
forbidden_outputs:
  - "process/ARCHITECTURE-DECISION.md"
  - "process/STORY-BACKLOG.md"
  - "process/DEVELOPMENT-PLAN.yaml"
  - "process/stories/STORY-*.md"
  - "process/stories/STORY-*-LLD.md"
  - "delivery/**"
---

# meta-se HLD 修订交接说明

## 编排结论

当前仍保持 `solution-design` 阶段。`process/HLD.md` 尚未通过人工确认，不得进入 `story-planning`。

本次不是需求变更，不创建 CR；这是 HLD 人工确认前的出口文档一致性修订。`process/HLD.md` §7 已完整列出 Q-004 至 Q-019，但 §20 只列出 HLD-Q1 至 HLD-Q6，且 `checkpoints/CHECKPOINT-HLD.md` 只列出 HLD-Q1 至 HLD-Q9。HLD 正文和检查点在人工确认前必须完整覆盖 Q-004 至 Q-019。

## meta-se 必读上下文

| 文件 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、门控状态和禁止越界范围 |
| `process/HLD.md` | 本次唯一允许修订的正式设计产物 |
| `checkpoints/CHECKPOINT-HLD.md` | 当前检查点已标记为待刷新，供了解不一致来源 |

## 修订任务

你是 `meta-se`。请只修订 `process/HLD.md`，范围限定为 HLD 人工确认前的待确认问题一致性修复：

1. 修改 `process/HLD.md` §20「待确认问题」，使其完整覆盖 Q-004 至 Q-019。
2. 可以选择以下两种实现方式之一：
   - 直接把 §20 的问题 ID 改为 Q-004 至 Q-019，并逐项列出问题描述、优先级、当前 HLD 默认、影响范围、负责人和目标答复时间。
   - 保留 HLD-Q 编号，但必须增加 HLD-Q 到 Q-004 至 Q-019 的完整映射表，且每个 Q-004 至 Q-019 都只能映射到清晰、可确认的 HLD 决策项。
3. §20 的覆盖口径必须与 §7「关键设计决策：Q-004 至 Q-019」一致，不得遗漏、合并到无法独立确认、或改变 Q-004 至 Q-019 的语义。
4. 在 `process/HLD.md` 头部修订记录追加一行，说明本次只修订 §20 的待确认问题覆盖和映射。
5. 保持 `process/HLD.md` frontmatter 为 `status: ready-for-review`、`confirmed: false`。修订完成后交回 `meta-po` 刷新 HLD 检查点。

## Q-004 至 Q-019 最小覆盖清单

| 原问题 ID | §20 必须可确认的决策点 |
|---|---|
| Q-004 | 默认复权口径为 `adjustment_policy=qfq` 前复权，且同一次回测、扫描、候选筛选和聚宽对照不得混用复权口径 |
| Q-005 | 默认成交假设为 T 日收盘后生成信号，T+1 收盘价成交，成本和收益归属按 HLD §7 决策执行 |
| Q-006 | 第一版 `index_members.parquet` 使用固定当前沪深 300 快照，明确非 PIT 股票池披露 |
| Q-007 | 历史窗口不足、端点价格缺失、成交价缺失、无成交、停牌或未知交易状态的分层处理策略 |
| Q-008 | 最小 price schema、`adjustment_policy` 记录位置，以及 `available_at` 缺失时的日线收盘价推导规则 |
| Q-009 | 涨跌停字段第一版不强制进入 schema，但必须进入报告 metadata 限制项并作为 P1 增强 |
| Q-010 | 未来函数校验覆盖数据加载层、信号层、股票池层和报告审计层，事件层第一版禁用 |
| Q-011 | 财报披露日、财报/公告事件和 ST 事件字段第一版 Out of Scope，后续必须事件级 `available_at` |
| Q-012 | 数据准备默认限速参数：`request_interval_seconds=2`、`batch_size=50`、`max_concurrency=1` |
| Q-013 | 默认重试和退避：`max_retries=3`、`backoff_policy=exponential_jitter`、基础等待 2 秒、最大单次等待 60 秒 |
| Q-014 | `data/manifests/data_prep_manifest.jsonl` 是 checkpoint 事实源，批次状态枚举完整 |
| Q-015 | 默认 `recent_trade_days_backfill=5`，并明确价格、复权相关日线、固定成分股快照和交易日历的回补范围 |
| Q-016 | raw 缓存第一版长期保留，不自动清理，按 `source/interface/date/batch_id` 组织 |
| Q-017 | manifest 使用 JSONL，含 `schema_version`，质量报告通过 `manifest_run_id` 关联 |
| Q-018 | `quality_status` 为 `pass/warn/fail`，并明确 schema 缺失、覆盖缺口、重复键、异常价格和缺失率阈值 |
| Q-019 | 同时披露交易日新鲜度和自然日新鲜度，字段和计算口径与 HLD §7 保持一致 |

## 禁止事项

- 不得生成 ADR、Story、开发计划、LLD、代码或 `delivery/**` 文件。
- 不得推进到 `story-planning`。
- 不得重写需求、使用场景或变更 Q-004 至 Q-019 的既有语义。
- 不得把多个 Q 项合并成用户无法逐项确认的单一问题。

## 完成后交回

修订完成后，停止在 `solution-design` 阶段并交回 `meta-po`。由 `meta-po` 重新刷新 `checkpoints/CHECKPOINT-HLD.md`，确保检查点完整列出或映射 Q-004 至 Q-019，再重新发起 HLD 人工确认。
