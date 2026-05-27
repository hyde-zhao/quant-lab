---
story_id: "CR014-S06-incremental-refresh-replay-retention-contract"
title: "incremental refresh / replay / retention 合同"
status: "verified"
priority: "P0"
wave: "CR014-W3-AUDIT-OPS"
depends_on:
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
  - "CR014-S03-p0-plan-run-normalize-validate-publish-contract"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T08:56:04+08:00"
change_id: "CR-014"
---

# CR014-S06：incremental refresh / replay / retention 合同

## Story 摘要

定义增量刷新、最近 N 个交易日回补、replay、resume_conflict、candidate retention 和 current pointer 不污染策略。Replay 不触发 provider、不读凭据、不写 raw、不改 current pointer。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.7.1、§17.8；ADR-051、ADR-052；REQ-092、REQ-094。

**未来实现候选文件**：`market_data/incremental.py`、`market_data/replay.py`、`market_data/retention.py`、`tests/test_cr014_incremental_replay_retention.py`。

**开发合同**：

| 对象 | 输入 | 输出 | 禁止 |
|---|---|---|---|
| incremental planner | published current pointer、trading calendar、dataset policy | refresh plan、affected partitions | CP5 前真实 fetch |
| replay runner | raw/manifest refs、candidate config | canonical/gold/quality candidate、audit evidence | provider call、credential read、raw write、pointer update |
| retention | candidate age、publish status、audit refs | retain/archive/delete recommendation | CP5 前删除或迁移旧数据 |
| resume conflict | run id、manifest refs、partition lock | structured conflict result | silent overwrite |

## validation_context

**验证方式**：fixture manifest / candidate path contract test；不访问真实 lake，不删除文件。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| replay | `provider_fetches=0`、`credential_reads=0`、`raw_writes=0`、`current_pointer_changes=0` |
| resume conflict | 输出 structured conflict，不覆盖 candidate |
| retention dry-run | 只输出 recommendation，不删除 |
| incremental plan | 明确 affected partitions 与 permission counters |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | replay 四类禁止计数均为 0 | 单元测试 |
| AC-02 | resume_conflict 有结构化输出 | 单元测试 |
| AC-03 | candidate retention 不自动删除旧数据或 published truth | contract test |
| AC-04 | CP5 前 lake_write=0、credential_read=0、provider_fetch=0 | 门控检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S02、CR014-S03 |
| 下游依赖 | CR014-S07 |
| 主所有权 | `market_data/incremental.py`、`market_data/replay.py`、`market_data/retention.py` |
| 共享文件 | `market_data/runtime.py`、`market_data/catalog.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、真实 lake 删除/迁移/写入、raw 写入、current pointer 更新 |

## LLD 输入

- S02 catalog/publish gate 与 S03 pipeline state。
- HLD-DATA-LAKE §17 incremental / replay / retention。
- ADR-051 / ADR-052。
- CP5 前 replay 与 retention 均为 candidate/dry-run 合同。
