---
story_id: "CR014-S04-duckdb-readonly-query-audit-parity-boundary"
title: "DuckDB read-only query/audit/parity 边界"
status: "verified"
priority: "P1"
wave: "CR014-W2-PIPELINE"
depends_on:
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
  - "CR014-S03-p0-plan-run-normalize-validate-publish-contract"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T08:38:59+08:00"
change_id: "CR-014"
---

# CR014-S04：DuckDB read-only query/audit/parity 边界

## Story 摘要

冻结 DuckDB 只读候选层的读取时机、读取对象和输出边界。DuckDB 可在 publish 后读取 catalog current pointer 指向的 Parquet，也可在受控 candidate audit 中只读 candidate path；DuckDB query/view/parity/report 不写事实源、不触发 publish、不替代 catalog。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.6、§17.7.1；ADR-049、ADR-052；REQ-093、REQ-094、REQ-096。

**未来实现候选文件**：`market_data/duckdb_query.py`、`market_data/audit.py`、`tests/test_cr014_duckdb_readonly_boundary.py`。

**开发合同**：

| 读取模式 | 输入 | 输出 | 禁止 |
|---|---|---|---|
| published current truth | catalog current pointer、Parquet path | query result、feature extraction result、audit evidence | 写 catalog、写 manifest、写 `.duckdb` 事实源 |
| candidate audit | controlled candidate path、manifest refs | parity evidence、readiness audit | 自动 publish、替代 Validate / Publish Gate |
| fallback | pandas/pyarrow reader | 等价 audit result | 依赖 DuckDB 才能运行核心数据湖 |

**调用方向**：S05/S07 可消费 DuckDB audit evidence；DuckDB 层不得调用 Provider Adapter / Run Gate / Publish Gate。

## validation_context

**验证方式**：后续 LLD 使用 fake Parquet path / fixture catalog 验证只读行为；本阶段不改 `pyproject.toml` 或 `uv.lock`。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| published read | 只读 current pointer 指向文件 |
| candidate audit | 只读受控 candidate path |
| parity PASS | publish_count=0、source_of_truth_update=0 |
| CP5 前 | duckdb_dependency_change=0 |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | DuckDB query/view/parity/report 反向成为事实源次数为 0 | contract test |
| AC-02 | DuckDB 不触发 Provider Adapter / Run Gate / Publish Gate | 静态检查 |
| AC-03 | CP5 前 `pyproject.toml` / `uv.lock` 修改次数为 0 | CP4/CP5 门控 |
| AC-04 | fallback pandas/pyarrow 策略进入 LLD 输入 | LLD 静态检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S02、CR014-S03 |
| 下游依赖 | CR014-S05、CR014-S07 |
| 主所有权 | `market_data/duckdb_query.py`、`market_data/audit.py` |
| 共享文件 | `market_data/catalog.py`、`market_data/validation.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、`pyproject.toml`、`uv.lock`、`*.duckdb` 事实源、publish side effect |

## LLD 输入

- HLD-DATA-LAKE §17 DuckDB read-only 候选评估。
- ADR-049 DuckDB 只读 query/audit 候选而非事实源。
- S02 catalog current pointer 与 S03 state machine。
- CP5 前 DuckDB dependency change = 0。
