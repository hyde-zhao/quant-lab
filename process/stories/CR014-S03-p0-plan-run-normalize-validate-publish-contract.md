---
story_id: "CR014-S03-p0-plan-run-normalize-validate-publish-contract"
title: "P0 dataset plan/run/normalize/validate/publish 合同"
status: "verified"
priority: "P0"
wave: "CR014-W2-PIPELINE"
depends_on:
  - "CR014-S01-a-share-universe-lifecycle-contract"
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T08:26:45+08:00"
change_id: "CR-014"
---

# CR014-S03：P0 dataset plan/run/normalize/validate/publish 合同

## Story 摘要

定义 P0 dataset 的 plan -> run -> normalize/replay -> validate -> publish -> read/query 合同。CP5 + 用户显式授权后，Provider Adapter / Run Gate 才能写 raw、manifest 与 run metadata；Normalize / Replay 只生成 candidate；Validate 不自动 publish。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.7.1；ADR-048、ADR-051、ADR-052；REQ-090、REQ-091、REQ-092、REQ-094。

**未来实现候选文件**：`market_data/cli.py`、`market_data/runtime.py`、`market_data/normalization.py`、`market_data/validation.py`、`tests/test_cr014_p0_pipeline_contract.py`。

**开发合同**：

| 阶段 | 谁写入 | 写入层 | CP5 前行为 | 输出 |
|---|---|---|---|---|
| plan | planner | 无真实 lake 写入 | dry-run / plan only | dataset plan、permission counters |
| run | Provider Adapter / Run Gate | raw、manifest、run metadata | provider_fetch=0、lake_write=0、credential_read=0 | raw run candidate，需 CP5+用户授权 |
| normalize | normalizer | canonical/gold/quality candidate | 只定义 candidate 合同 | candidate manifest |
| replay | replay runner | canonical/gold/quality candidate | 不触发 provider、不读凭据、不写 raw | replay evidence |
| validate | validator | quality/readiness/parity candidate | 不 publish | validation result |
| publish | Explicit Publish Gate | catalog current pointer | 不允许 | pointer update result |

**P0 dataset 最小集合**：prices、adj_factor、hs300_index、trade_calendar、index_members、index_weights、stock_basic，外加 lifecycle/code-change 合同输入。

## validation_context

**验证方式**：状态机 contract test 与 permission counter test；不联网、不改依赖、不真实写湖。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| CP5 前 run | fail-closed 或 dry-run，真实操作计数均为 0 |
| normalize/replay | 只输出 candidate，不更新 current pointer |
| validate PASS | publish_count=0 |
| publish gate 未授权 | current_pointer_changes=0 |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | run/normalize/replay/validate/publish 每阶段输入输出 100% 定义 | LLD 静态检查 |
| AC-02 | CP5 前 provider_fetch=0、lake_write=0、credential_read=0、duckdb_dependency_change=0 | 门控检查 |
| AC-03 | Normalize / Replay 更新 current pointer 次数为 0 | contract test |
| AC-04 | Validate PASS 自动 publish 次数为 0 | contract test |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S01、CR014-S02 |
| 下游依赖 | CR014-S04、CR014-S05、CR014-S06 |
| 主所有权 | `market_data/cli.py`、`market_data/runtime.py`、`market_data/normalization.py`、`market_data/validation.py` |
| 共享文件 | `market_data/contracts.py`、`market_data/manifest.py`、`market_data/catalog.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、`pyproject.toml`、`uv.lock`、真实 provider fetch、真实 lake write、credential read |

## LLD 输入

- 上游 S01 lifecycle 与 S02 publish gate 合同。
- HLD-DATA-LAKE §17 写入时序与读写边界。
- ADR-051 的真实执行授权与 claim boundary。
- CP5 前所有真实操作计数为 0。
