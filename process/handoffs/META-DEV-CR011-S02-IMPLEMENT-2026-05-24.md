---
handoff_id: "META-DEV-CR011-S02-IMPLEMENT-2026-05-24"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-you"
change_id: "CR-011"
story_id: "CR011-S02-pit-universe-and-stock-lifecycle-completion"
wave_id: "CR011-DATA-BATCH-A-DEV-W2"
status: "dispatched"
created_at: "2026-05-24T10:56:27+08:00"
updated_at: "2026-05-24T10:57:37+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e57ea-7a5d-7361-9695-c8e8dcec78eb"
  thread_id: "019e57ea-7a5d-7361-9695-c8e8dcec78eb"
  tool_name: "spawn_agent"
  spawned_at: "2026-05-24T10:57:37+08:00"
  resumed_at: ""
  completed_at: ""
  closed_at: ""
  result: "running"
---

# META-DEV CR011-S02 实现交接

## 任务

按确认版 LLD 实现 `CR011-S02-pit-universe-and-stock-lifecycle-completion`：补齐 PIT 股票池、as-of 可得性、股票生命周期 gate 与 fixed snapshot 降级合同，使 `production_strict` 不再把 `index_weights` 或 `stock_basic` 当前快照当作 PIT membership 证明。

## 输入

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR011-S02-pit-universe-and-stock-lifecycle-completion.md` | dev-ready |
| LLD | `process/stories/CR011-S02-pit-universe-and-stock-lifecycle-completion-LLD.md` | confirmed |
| CP5 | `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md` | approved |
| 上游 S01 | `process/checks/CP7-CR011-S01-real-benchmark-and-policy-consumption-VERIFICATION-DONE.md` | PASS / verified |
| 上游 CR010-S04 | `process/STORY-STATUS.md` | verified |
| 上游 CR010-S06 | `process/checks/CP7-CR010-REMAINING-BATCHES-META-QA-VERIFICATION-2026-05-22.md` | meta-qa CP7 PASS |
| 上游 CR008-S05 | `process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md` | PASS / verified |

## 允许写入范围

- `market_data/readers.py`
- `engine/research_dataset.py`
- `tests/test_cr011_pit_universe_lifecycle.py`
- `process/checks/CP6-CR011-S02-pit-universe-and-stock-lifecycle-completion-CODING-DONE.md`
- `process/stories/CR011-S02-pit-universe-and-stock-lifecycle-completion.md` 的实现状态字段

## 禁止范围

- 不实现 `CR011-S03` 至 `CR011-S08`。
- 不修改 `engine/universe.py`；若必须修改，停止并向 meta-po 报告扩大范围需求。
- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`。
- 不真实联网，不真实 Tushare 抓取，不写真实 lake。
- 不读取、打印或记录 `.env`、token、密码、私钥、cookie、session 或其他凭据。
- 不读取、列出、迁移、复制、删除旧 `data/**`。
- 不覆盖 `reports/experiment_17_21/factor_strategy_report.md`。
- 不写 `delivery/**`。

## 实现要求

- 消费 LLD 第 4、6、7、8、10、13 节；真实 PIT source/interface 未冻结时必须 fail-fast，输出 `required_missing` / `source_unresolved`，不得伪造 available。
- `production_strict` 必须同时满足 PIT membership、`is_pit_universe=true`、`pit_status=pass|pit_available`、`as_of_join_violation_count=0` 和 lifecycle pass。
- fixed snapshot / explicit symbols 只能进入 exploratory，并写非空 `survivorship_bias_note`。
- `index_weights` 或 `stock_basic` 单独存在时不得证明 PIT；对应 blocked claim 必须机器可解析。
- CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables 和 Agent Dispatch Evidence。若工具面暂未暴露 agent id，可先引用本 handoff，meta-po 会在回收时补齐真实 id。

## 建议验证

- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile market_data/readers.py engine/research_dataset.py tests/test_cr011_pit_universe_lifecycle.py`
- `UV_CACHE_DIR=/tmp/uv-cache-local-backtest PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr011_pit_universe_lifecycle.py`
- 相关回归优先覆盖 CR008 PIT/universe、CR008 metadata、CR010 contracts、S01 benchmark policy 测试。
