---
story_id: "CR014-S01-a-share-universe-lifecycle-contract"
title: "全 A universe / lifecycle / code-change 合同"
status: "verified"
priority: "P0"
wave: "CR014-W1-CONTRACTS"
depends_on: []
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T07:46:57+08:00"
change_id: "CR-014"
---

# CR014-S01：全 A universe / lifecycle / code-change 合同

## Story 摘要

冻结 CR-014 全 A since-inception current truth 的 universe denominator、证券生命周期、退市/摘牌、代码变更和最近已闭市交易日口径。该 Story 只定义合同和 LLD 输入，不抓 provider、不读凭据、不写 lake、不声明数据已覆盖。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.1、§17.7.1；`process/ARCHITECTURE-DECISION.md` ADR-050；`process/REQUIREMENTS.md` REQ-088、REQ-089、REQ-097。

**未来实现候选文件**：`market_data/contracts.py`、`market_data/lifecycle.py`、`market_data/calendar.py`、`tests/test_cr014_universe_lifecycle_contract.py`。

**开发合同**：

| 对象 | 输入契约 | 输出契约 | 失败路径 |
|---|---|---|---|
| universe denominator | as-of date、listed/delisted universe、code-change mapping | `security_id`、`symbol`、`exchange`、`list_date`、`delist_date`、`lifecycle_status`、`valid_from`、`valid_to`、`successor_id`、`predecessor_id` | lifecycle 缺字段时 fail-fast，full-A allowed claim=0 |
| closed trading day policy | calendar、当前日期、market close 判定 | `current_truth_as_of` | 无 calendar 或未闭市时不得发布 current truth |
| code-change contract | old/new code relation、effective date | stable security identity mapping | 同一日期多映射或断链时写 `required_missing` |

**调用方向**：后续 CR014-S02/S03/S05 只读本 Story 合同；本 Story 不调用 provider、catalog、DuckDB 或研究消费层。

## validation_context

**验证方式**：后续 LLD 应用 fixture 验证，不联网、不读凭据、不读取旧 `data/**`。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| lifecycle 字段完整 | 10 类必需字段 100% 存在 |
| 退市证券进入 denominator | 退市前日期可纳入，退市后状态可追溯 |
| 代码变更 | 同一证券身份可跨代码追踪 |
| 字段缺失 | `allowed_claims.full_a_since_inception=0` |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | lifecycle 必需字段 10 类 100% 进入合同 | Story/LLD 静态检查 |
| AC-02 | lifecycle 缺字段时 full-A allowed claim 输出次数为 0 | 单元测试或 contract test |
| AC-03 | 退市、摘牌、代码变更均有 `required_missing` / `blocked_claims` 输出路径 | 单元测试 |
| AC-04 | provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 | CP4/CP5 门控检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | 无 |
| 下游依赖 | CR014-S02、CR014-S03、CR014-S05 |
| 主所有权 | `market_data/contracts.py`、`market_data/lifecycle.py`、`market_data/calendar.py` |
| 共享文件 | `market_data/validation.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、`pyproject.toml`、`uv.lock`、任何 provider fetch / lake write / credential read |

## LLD 输入

- 当前 Story ID 与本文件。
- HLD-DATA-LAKE §17 的 full A current truth、lifecycle、write/read boundary。
- ADR-050 的 lifecycle / code-change 决策。
- CP5 前 `implementation_allowed=false`。
