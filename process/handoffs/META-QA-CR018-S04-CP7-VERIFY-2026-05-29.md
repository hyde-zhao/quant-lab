---
handoff_id: "META-QA-CR018-S04-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S04-industry-market-cap-liquidity-and-exposure-data"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T09:12:49+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e714b-56ab-7532-9051-0952cadb1da3"
  thread_id: "019e714b-56ab-7532-9051-0952cadb1da3"
  agent_name: "qa-shi"
  spawned_at: "2026-05-29T09:13:46+08:00"
  completed_at: "2026-05-29T09:16:15+08:00"
  closed_at: "2026-05-29T09:19:23+08:00"
---

# META-QA Handoff: CR018-S04 CP7 Verification

## Mission

独立验证 `CR018-S04-industry-market-cap-liquidity-and-exposure-data` 的 CP6 交付是否满足 LLD、Story 和 CP5 已批准边界。

本验证只允许离线 / fixture / dry-run 检查；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S04-industry-market-cap-liquidity-and-exposure-data.md` |
| LLD | `process/stories/CR018-S04-industry-market-cap-liquidity-and-exposure-data-LLD.md` |
| CP6 | `process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR018-S04-IMPLEMENT-2026-05-29.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |

## Verification Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| required-read | `market_data/readers.py` | 验证 P1 availability metadata helper 只消费显式 metadata，未扫描未发布 lake。 |
| required-read | `engine/research_dataset.py` | 验证 P1 claim boundary 不阻断 core release，但阻断中性化 / capacity / scale_up 等声明。 |
| required-read | `tests/test_cr018_p1_auxiliary_claim_boundary.py` | 验证 fixture-only 合同覆盖缺失 / 完整 metadata 和真实操作计数。 |
| write | `process/checks/CP7-CR018-S04-industry-market-cap-liquidity-and-exposure-data-VERIFICATION-DONE.md` | 仅写 CP7 验证结果。 |

禁止修改业务代码、Story、STATE、STORY-STATUS、DEVELOPMENT-PLAN、`pyproject.toml`、`uv.lock`、`.env`、真实 lake、provider connector、catalog current pointer 或 QMT 入口。

## Required Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_p1_auxiliary_claim_boundary.py tests/test_cr018_release_scope_dataset_groups.py
```

建议额外运行：

```bash
git diff --check -- tests/test_cr018_p1_auxiliary_claim_boundary.py market_data/readers.py engine/research_dataset.py process/checks/CP6-CR018-S04-industry-market-cap-liquidity-and-exposure-data-CODING-DONE.md
```

## CP7 Output Requirements

CP7 文件必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果、真实操作计数和结论。

验证通过时结论写 `PASS`；发现阻断项时结论写 `FAIL`，并列出可回修的最小问题。
