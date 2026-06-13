---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-02"
---

# Feature Tasks: market-data-lake

| Task ID | 任务 | 输入 | 输出 | 文件范围 | 验证 |
|---|---|---|---|---|---|
| FEAT-02-T01 | 维护 dataset schema / lake layout 索引 | HLD-DATA-LAKE、ADR、Story LLD | schema / layout current index | `market_data/contracts.py`、`market_data/lake_layout.py`、docs | contract tests |
| FEAT-02-T02 | 维护 publish gate / current pointer 规则 | catalog publish ADR | publish / rollback 合同 | `market_data/catalog.py`、`market_data/publish.py` | publish gate tests |
| FEAT-02-T03 | 维护 quality / readiness / claims | readiness 规则 | allowed / blocked claim schema | `market_data/readiness.py`、`market_data/claims.py` | readiness / claim tests |
| FEAT-02-T04 | 维护 replay / retention / rollback | run / manifest / release summary | replay 和 retention 合同 | `market_data/replay.py`、`market_data/retention.py` | replay / retention tests |
| FEAT-02-T05 | 维护 consumer forbidden dependency guardrail | dependency map | forbidden import 检查 | tests / docs | consumer boundary tests |

## 后续触发条件

- 新增真实 provider 或 dataset。
- 修改 catalog current pointer / publish / rollback 语义。
- 修改 DuckDB、Parquet、external lake root 或 retention 策略。
- 数据湖 publish 后解除 QMT 后置 gate。

