---
check_id: "REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22"
workflow_id: "local_backtest"
change_id: "CR-010"
scope: "real-tushare-data-lake-resmoke"
executed_at: "2026-05-22T16:12:35+08:00"
result: "PARTIAL"
lake_root: "<configured-lake-root>"
old_data_comparison: "deferred"
---

# CR-010 真实 Tushare 数据湖补跑结果

## Entry Criteria

| 准则 | 状态 | 证据 |
|---|---|---|
| 用户授权真实联网、Tushare 抓取、真实写湖和读取 `.env` | PASS | 用户于 `2026-05-22T15:54:10+08:00` 授权；STATE 已记录。 |
| 凭据与路径脱敏 | PASS | 命令输出和本报告仅使用 `<configured-lake-root>`；未写入 token、`.env` 内容或真实私有路径。 |
| 旧 `data/**` 对比暂缓 | PASS | 未读取、列出、迁移、复制、比对或删除旧 `data/**`。 |
| 子 agent 调度已发生 | PASS | meta-dev `019e4ead-0d29-7752-aa44-15016debb903` 完成 B/C 门控复核；meta-qa `019e4ead-3bd8-7341-bb4c-045482fd4a38` 完成首次真实 smoke。 |
| 主线程可进行阻断修复 | PASS | 首次 smoke 发现 replay、adj_factor 真实入口、raw 路径碰撞和 current-run 读取隔离问题；修复范围限定在 CR010-DL-BATCH-A 数据湖链路。 |

## Agent Dispatch Evidence

| 角色 | mode | agent_id | 结果 |
|---|---|---|---|
| meta-dev/dev-lv | `spawn_agent` | `019e4ead-0d29-7752-aa44-15016debb903` | B/C 批次因 S06-S12 Story/LLD/CP5 未满足而未越权实现；离线全量 `245 passed`。 |
| meta-qa/qa-he | `spawn_agent` | `019e4ead-3bd8-7341-bb4c-045482fd4a38` | 首次真实 smoke 为 FAIL，定位到 replay 匹配、adj_factor 入口和 prices qfq normalize 阻断。 |
| main thread | `direct-remediation-after-subagent-findings` | n/a | 修复 A 批次真实链路阻断并补跑真实 smoke；未触发旧 `data/**`。 |

## Remediation

| 修复项 | 状态 | 文件 |
|---|---|---|
| `tushare-first-acquire` P0 allowlist 补齐 `adj_factor/index_members/stock_basic` | DONE | `market_data/cli.py` |
| `validate/read` 按 `run_id` 或 catalog current canonical 隔离读取，避免跨历史 run 混读 | DONE | `market_data/cli.py`、`market_data/readers.py` |
| `replay` 改为按 manifest `run_id/batch_id/dataset/interface` 匹配，兼容 `tushare-first-acquire` 参数 | DONE | `market_data/cli.py` |
| raw 写入路径加入 `run_id=<run_id>`，避免不同 run 复用 `b1` 覆盖 raw 并破坏旧 manifest checksum | DONE | `market_data/lake_layout.py`、`market_data/storage.py`、`market_data/runtime.py` |
| `revalidate` 保持同一 run 的 published current truth，不降级为 candidate_unpublished | DONE | `market_data/cli.py` |
| `index_weights` 缺真实 `available_at` 时标准化为 `pit_incomplete/readiness=pit_incomplete`，不伪造 PIT available | DONE | `market_data/contracts.py`、`market_data/normalization.py` |

## Checklist

| Dataset | 真实抓取 / 写湖 | normalize | validate | publish/read | replay/revalidate | 结论 |
|---|---|---|---|---|---|---|
| `trade_calendar` | PASS，`network_calls=1` | PASS，3 行 | PASS，3/3，`quality_status=pass` | PASS，published/read 3 行 | PASS，revalidate 0 network，replay 0 network | PASS |
| `hs300_index` | PASS，`network_calls=1` | PASS，3 行 | PASS，3/3，`quality_status=pass` | PASS，published/read 3 行 | PASS，revalidate 0 network，replay `status=skipped` | PASS |
| `adj_factor` | PASS，`network_calls=1` | PASS，3 行 | PASS，3/3，`quality_status=pass` | PASS，published/read 3 行 | PASS，revalidate/replay 0 network | PASS |
| `prices` | PASS，`network_calls=1` | PASS，3 行，已用同 run `adj_factor` join | WARN，3/3，`warn_non_pit_universe` | PASS with `--allow-warn`，read 3 行 | PASS，revalidate/replay 0 network | WARN |
| `index_weights` | PASS，`network_calls=1` | PASS，300 行 | WARN，`pit_incomplete` | PASS with `--allow-warn`，read 300 行 | 未单独补 replay | WARN |
| `stock_basic` | PASS，`network_calls=1` | PASS，2314 行 | WARN，`non_pit_snapshot` | PASS with `--allow-warn`，read 2314 行 | 不适用 | WARN |
| `index_members` | PASS，`network_calls=1` | PASS，0 行 | FAIL，`required_missing` | 未发布 | 不适用 | FAIL |

## Catalog Coverage

外置 lake 当前 P0 coverage 摘要：

| Dataset | publish_status | quality_status | readiness_status | pit_status | coverage_ratio |
|---|---|---|---|---|---:|
| `prices` | published | warn | available | non_pit_disclosed | 1.0 |
| `adj_factor` | published | pass | available | not_applicable | 1.0 |
| `hs300_index` | published | pass | available | non_pit_disclosed | 1.0 |
| `trade_calendar` | published | pass | available | not_applicable | 1.0 |
| `index_members` | candidate_unpublished | fail | pit_incomplete | pit_incomplete | 0.0 |
| `index_weights` | published | warn | pit_incomplete | pit_incomplete | 100.0 |
| `stock_basic` | published | warn | non_pit_snapshot | non_pit_snapshot | 771.3333333333334 |

Summary：`published_count=6`、`candidate_unpublished_count=1`、`missing_required_count=0`、`current_truth_complete=false`。

## Readiness Result

| 模式 | 状态 | 说明 |
|---|---|---|
| `production_strict` | FAIL | 阻断 claim：`production_current_truth`、`quality_pass_research`、`pit_universe_research`；原因包括 `index_members` 缺失、`prices/index_weights/stock_basic` warn / PIT 不完整。 |
| `exploratory` | WARN | 允许 claim：`exploratory_analysis`、`fixture_regression`；必须披露 PIT 与 quality limitations。 |

## Verification Commands

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 python -m py_compile market_data/lake_layout.py market_data/storage.py market_data/runtime.py market_data/cli.py market_data/readers.py market_data/contracts.py market_data/normalization.py tests/test_cr010_data_lake_publish_and_contracts.py tests/test_market_data_runtime_storage.py tests/test_market_data_contracts.py tests/test_market_data_tushare_datasets.py tests/test_market_data_multidataset_quality_readers.py` | PASS |
| `uv run --python 3.11 pytest -q` | PASS，`249 passed in 7.62s` |

## Exit Criteria

| 准则 | 状态 | 说明 |
|---|---|---|
| 真实联网、真实 Tushare、真实写 lake 已执行 | PASS | 覆盖 `trade_calendar/hs300_index/prices/adj_factor/index_members/index_weights/stock_basic`。 |
| P0 current truth 全部 complete | FAIL | `index_members` 真实接口返回空数据，仍为未发布失败候选。 |
| 不把旧 `data/**` 当 current truth | PASS | 未触发旧数据读取/比对；catalog coverage 仅来自外置 lake catalog。 |
| production_strict 可放行 | FAIL | PIT universe 与 quality pass 条件仍不满足。 |
| exploratory 可披露使用 | WARN | 6/7 P0 dataset 已 published；必须保留 `index_members` 缺失、非 PIT snapshot 和 warn 数据集限制。 |

## Deliverables

| 交付物 | 状态 | 路径 |
|---|---|---|
| 真实 Tushare 数据湖补跑记录 | DONE | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-RESMOKE-2026-05-22.md` |
| 真实链路阻断修复 | DONE | `market_data/cli.py`、`market_data/readers.py`、`market_data/lake_layout.py`、`market_data/storage.py`、`market_data/runtime.py`、`market_data/contracts.py`、`market_data/normalization.py` |
| 回归测试 | DONE | 全量 `249 passed` |

## Conclusion

结论：`PARTIAL`。

CR-010 真实小窗口链路已从首次 FAIL 推进到 6/7 个 P0 dataset published：`trade_calendar`、`hs300_index`、`adj_factor` 为 pass，`prices`、`index_weights`、`stock_basic` 为带限制的 warn。`index_members` 真实接口本窗口返回空数据，仍不能发布；因此 production_strict 继续 fail，exploratory 可带限制使用。
