---
story_id: "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
title: "Parquet layout / manifest / catalog current pointer / publish gate"
status: "verified"
priority: "P0"
wave: "CR014-W1-CONTRACTS"
depends_on:
  - "CR014-S01-a-share-universe-lifecycle-contract"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T07:59:48+08:00"
change_id: "CR-014"
---

# CR014-S02：Parquet layout / manifest / catalog current pointer / publish gate

## Story 摘要

冻结 CR-014 Parquet lake 分区、manifest、catalog current pointer 与 Explicit Publish Gate 的事实源合同。DuckDB 只能读取 catalog 指针或受控 candidate audit path，Validate / parity PASS 不得自动更新 current pointer。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.5、§17.7.1；ADR-048、ADR-052；REQ-090、REQ-091。

**未来实现候选文件**：`market_data/lake_layout.py`、`market_data/manifest.py`、`market_data/catalog.py`、`market_data/publish.py`、`tests/test_cr014_catalog_publish_gate.py`。

**开发合同**：

| 对象 | 输入契约 | 输出契约 | 失败路径 |
|---|---|---|---|
| Parquet layout | dataset、partition keys、run_id、candidate/published state | Hive-style 分区路径与 deterministic file naming | 分区键缺失时不生成 publish candidate |
| manifest | run metadata、source、schema hash、row count、quality status | append-only manifest record | manifest 不完整时 candidate 不可 publish |
| catalog current pointer | dataset、as_of、published run id、manifest refs | reader/DuckDB 可见 current truth | pointer 只由 Explicit Publish Gate 更新 |
| publish gate | quality/readiness/parity evidence、approval token | atomic pointer update result | Validate/parity PASS 不自动 publish |

**调用方向**：S03 使用 layout/manifest/catalog；S04 只读 catalog；S05/S07 消费 current pointer 与 blocked claims。

## validation_context

**验证方式**：fixture catalog / manifest contract test；不写真实 lake，不读取旧 `data/**`。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| candidate validate PASS | current pointer 变化次数为 0 |
| publish gate 明确批准 | current pointer 变化次数为 1 |
| DuckDB read-only | 只能读取 pointer 指向路径或 candidate audit path |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | catalog pointer 必填字段 100% 进入合同 | 静态检查 |
| AC-02 | Validate / parity PASS 自动更新 pointer 次数为 0 | 单元测试 |
| AC-03 | candidate path 与 published current truth 明确分离 | contract test |
| AC-04 | CP5 前 provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 | CP4/CP5 门控检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S01 |
| 下游依赖 | CR014-S03、CR014-S04、CR014-S05、CR014-S06 |
| 主所有权 | `market_data/lake_layout.py`、`market_data/manifest.py`、`market_data/catalog.py`、`market_data/publish.py` |
| 共享文件 | `market_data/contracts.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、`pyproject.toml`、`uv.lock`、真实 lake current pointer 更新 |

## LLD 输入

- HLD-DATA-LAKE §17 Parquet lake / catalog / publish gate。
- ADR-048、ADR-052。
- 上游 S01 lifecycle denominator 合同。
- CP5 前 `implementation_allowed=false`，且 current pointer 更新授权为 0。
