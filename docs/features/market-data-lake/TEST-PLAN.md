---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-02"
---

# Feature Test Plan: market-data-lake

## 测试目标

证明市场数据湖在默认状态下不触发真实操作，并且 candidate、quality/readiness、publish gate、rollback、只读消费和 claim boundary 行为可验证。

## 测试矩阵

| 测试域 | 关键场景 | 验证入口 |
|---|---|---|
| 数据湖分层 | raw / manifest / canonical / gold / quality / catalog 字段完整 | `tests/test_market_data_contracts.py`、`tests/test_cr014_p0_pipeline_contract.py` |
| Publish Gate | validate pass 不自动更新 current pointer | `tests/test_cr014_catalog_publish_gate.py` |
| 只读消费 | engine / experiments 不导入 connector/runtime/storage | `tests/test_cr010_consumer_boundary.py`、`tests/test_cr014_research_consumer_boundary.py` |
| Claim Boundary | P0 gate 失败时 blocked claims 完整 | `tests/test_cr014_readiness_claim_boundary.py`、`tests/test_cr018_*` |
| 复权视图 | raw / qfq / hfq / returns_adjusted 分离，QMT raw 执行价隔离 | `tests/test_cr017_*` |
| Replay / Retention | replay 不触发 provider / credential / current pointer 更新 | `tests/test_cr014_incremental_replay_retention.py` |
| DuckDB readonly | DuckDB 不成为事实源、不绕过 catalog | `tests/test_cr014_duckdb_readonly_boundary.py` |

## 手工验证

| 场景 | 条件 | 预期 |
|---|---|---|
| 真实补数授权前 | 无 authorization_id | provider_fetch、lake_write、catalog_publish、credential_read 均为 0 |
| 发布候选审查 | candidate 存在但未 publish | reader 返回 unavailable 或 candidate-only evidence，不作为 current truth |
| 回滚演练 | release summary 存在 rollback target | rollback 不删除历史证据，current pointer 可审计 |

## 未自动化风险

| 风险 | 当前处理 |
|---|---|
| 外部 provider 行为变化 | 后续真实 run 必须 run-scoped authorization + 脱敏 evidence |
| 大规模全 A 数据性能 | 需要独立 performance / storage CR，不在 CR-031 范围 |

