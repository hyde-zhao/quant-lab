---
handoff_id: "META-DEV-CR018-S04-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S04-industry-market-cap-liquidity-and-exposure-data"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-close-unavailable"
created_at: "2026-05-29T08:53:20+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e713c-4439-7ed1-acbf-ab5f4b77c2fc"
  thread_id: "019e713c-4439-7ed1-acbf-ab5f4b77c2fc"
  agent_name: "dev-xu"
  spawned_at: "2026-05-29T08:57:20+08:00"
  completed_at: "2026-05-29T09:03:36+08:00"
  closed_at: ""
  close_attempt: "close_agent returned not_found at 2026-05-29T09:09:46+08:00; no closed_at fabricated."
---

# META-DEV Handoff: CR018-S04 Implementation

## Mission

实现 `CR018-S04-industry-market-cap-liquidity-and-exposure-data` 的 P1 auxiliary availability 与 claim boundary 合同。

S01 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S04-industry-market-cap-liquidity-and-exposure-data.md` |
| LLD | `process/stories/CR018-S04-industry-market-cap-liquidity-and-exposure-data-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S04-industry-market-cap-liquidity-and-exposure-data-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S01 evidence | `process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `tests/test_cr018_p1_auxiliary_claim_boundary.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/readers.py` | 只允许 additive P1 availability metadata helper；不得扫描未发布 lake。 |
| shared | `engine/research_dataset.py` | 只允许 additive P1 claim boundary helper；不得改变现有研究主路径默认语义。 |

禁止修改：`market_data/contracts.py`、`market_data/validation.py`、`market_data/benchmarks.py`、S03 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据、provider connector、真实 lake 数据、catalog current pointer、QMT 入口。

## Required Implementation

1. P1 availability metadata 必须覆盖 industry、market_cap、float_market_cap、beta/style、ADV、turnover、liquidity、capacity、impact_cost 等字段族。
2. P1 缺失不阻断 P0 core current truth readiness。
3. P1 缺失时 industry neutral、market cap neutral、pure alpha、capacity、scale_up、capital amplification allowed count 必须为 0。
4. reader 不得扫描未发布 lake；只能消费调用方传入的 release / dataset availability metadata。
5. provider_fetch、lake_write、credential_read、QMT operation 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
