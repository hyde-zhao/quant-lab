---
handoff_id: "META-QA-CR018-S01-CP7-VERIFY-2026-05-29"
from: "meta-po"
to: "meta-qa"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S01-production-current-truth-definition-and-dataset-groups"
wave_id: "CR018-W1-SCOPE-CONTRACT"
status: "completed-closed"
created_at: "2026-05-29T08:45:06+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7133-1e11-7041-aace-fbe30de97fea"
  thread_id: "019e7133-1e11-7041-aace-fbe30de97fea"
  agent_name: "qa-zhang"
  spawned_at: "2026-05-29T08:47:19+08:00"
  completed_at: "2026-05-29T08:49:29+08:00"
  closed_at: "2026-05-29T08:53:20+08:00"
---

# META-QA Handoff: CR018-S01 CP7 Verification

## Mission

验证 `CR018-S01-production-current-truth-definition-and-dataset-groups` 的 CP7。

S01 已由 meta-dev/dev-you 完成受控离线实现，CP6 为 PASS。验证必须保持离线 / fixture / dry-run；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups.md` |
| LLD | `process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups-LLD.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md` |
| Implementation | `market_data/release_scope.py`、`market_data/dataset_groups.py`、`market_data/catalog.py`、`tests/test_cr018_release_scope_dataset_groups.py` |

## Verification Scope

必须验证：

1. `release_scope` 固定 `2015-01-05..latest_closed_trade_date` scoped release。
2. pre-2015 / since-inception claim 输出 `blocked/future_backfill`，allowed count 为 0。
3. P0 dataset group `required_for_publish=True`，P1 不阻断 core release，但阻断 neutralized / pure-alpha / capacity / scale_up 等声明。
4. 未登记 dataset 阻断 readiness，unknown dataset pass count 为 0。
5. `catalog.py` 新增 helper 只返回 metadata，不写 catalog，不 publish current pointer。
6. README / USER-MANUAL 不得声明当前 truth 已 publish。
7. 真实操作计数保持 0，未改依赖锁文件。

## Required Commands

至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_release_scope_dataset_groups.py tests/test_cr014_catalog_publish_gate.py
```

并运行：

```bash
git diff --check -- market_data/release_scope.py market_data/dataset_groups.py market_data/catalog.py tests/test_cr018_release_scope_dataset_groups.py README.md docs/USER-MANUAL.md process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups.md process/checks/CP6-CR018-S01-production-current-truth-definition-and-dataset-groups-CODING-DONE.md DEV-LOG.md
```

可按风险增加相关回归，但不得联网，不得真实写 lake，不得读取凭据。

## Output Required

写入 CP7：

`process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md`

CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试命令和结果、真实操作计数、结论。

完成后回复：

- CP7 路径。
- 测试命令和结果。
- 是否 PASS。
- 是否发现缺陷。
- 真实操作计数是否保持 0。
