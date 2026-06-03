---
handoff_id: "META-DEV-CR018-S03-IMPLEMENT-2026-05-29"
from: "meta-po"
to: "meta-dev"
workflow_id: "local_backtest-cr018"
change_id: "CR-018"
story_id: "CR018-S03-real-benchmark-index-components-weights-backfill"
wave_id: "CR018-W2-P0-P1-READINESS"
status: "completed-closed"
created_at: "2026-05-29T08:53:20+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e713c-10d0-76f2-a55b-01aace3cc4d5"
  thread_id: "019e713c-10d0-76f2-a55b-01aace3cc4d5"
  agent_name: "dev-qin"
  spawned_at: "2026-05-29T08:57:20+08:00"
  completed_at: "2026-05-29T09:05:58+08:00"
  closed_at: "2026-05-29T09:10:00+08:00"
---

# META-DEV Handoff: CR018-S03 Implementation

## Mission

实现 `CR018-S03-real-benchmark-index-components-weights-backfill` 的离线合同能力。

S01 已 verified，CP5 已 approved。本 Story 只允许受控离线 / fixture / dry-run 实现；严禁读取 `.env`、打印或保存 token、真实 provider fetch、真实 lake 写入、catalog current pointer publish、DuckDB 依赖变更或任何 QMT 操作。

## Required Inputs

| 类型 | 路径 |
|---|---|
| Story | `process/stories/CR018-S03-real-benchmark-index-components-weights-backfill.md` |
| LLD | `process/stories/CR018-S03-real-benchmark-index-components-weights-backfill-LLD.md` |
| CP5 auto | `process/checks/CP5-CR018-S03-real-benchmark-index-components-weights-backfill-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A-LLD-BATCH.md` |
| S01 evidence | `process/checks/CP7-CR018-S01-production-current-truth-definition-and-dataset-groups-VERIFICATION-DONE.md` |

## Write Scope

| 类型 | 路径 | 规则 |
|---|---|---|
| primary | `market_data/benchmarks.py` | 创建 benchmark group registry、dataset type、readiness contract、proxy / real boundary helper。 |
| primary | `tests/test_cr018_benchmark_group_readiness.py` | 创建 fixture-only 合同测试。 |
| shared | `market_data/contracts.py` | 只允许 additive benchmark readiness schema / constants。 |
| shared | `market_data/validation.py` | 只允许 additive benchmark group validation helper。 |

禁止修改：`engine/research_dataset.py`、`market_data/readers.py`、S04 primary 测试、`pyproject.toml`、`uv.lock`、`.env`、凭据、provider connector、真实 lake 数据、catalog current pointer、QMT 入口。

## Required Implementation

1. 定义四类 benchmark symbolic id：HS300、ZZ500、ZZ1000、CSI_ALL_SHARE。
2. 定义三类 dataset type：prices、components、weights。
3. 提供 4 x 3 readiness requirements，全部 `required_for_publish=True`。
4. 缺任一 benchmark 或 dataset type 时，production excess-return / index-enhancement / tracking-error claim allowed count 必须为 0。
5. 当前成分快照不得通过 PIT components 校验；weights 不得替代 membership。
6. proxy benchmark 不得写入 real benchmark 字段，proxy-as-real count 必须为 0。
7. provider_fetch、lake_write、credential_read、current_pointer_publish 计数必须保持 0。

## Required Verification

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_release_scope_dataset_groups.py
```

## CP6 Output

写入：

`process/checks/CP6-CR018-S03-real-benchmark-index-components-weights-backfill-CODING-DONE.md`

CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试结果和真实操作计数。

完成后回复修改文件、测试结果、CP6 路径和真实操作计数。
