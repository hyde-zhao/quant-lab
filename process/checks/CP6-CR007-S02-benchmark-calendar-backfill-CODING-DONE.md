# CP6 编码完成检查：CR007-S02-benchmark-calendar-backfill

## 元信息

| 字段 | 值 |
|---|---|
| workflow_id | local_backtest |
| change_id | CR-007 |
| story_id | CR007-S02-benchmark-calendar-backfill |
| wave_id | CR007-DEV-W2 |
| agent_role | meta-dev |
| agent_name | dev-zhang |
| check_type | CP6-CODING-DONE |
| generated_at | 2026-05-21T07:09:00+08:00 |
| conclusion | PASS |

## Entry Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| Story 已进入 dev_ready | PASS | 用户明确说明 CR007-S02 已进入 dev_ready；handoff 为 `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md`。 |
| LLD 已确认且允许实现 | PASS | `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md` 已作为本轮实现依据；CP5 implementability 文件已在 handoff 强输入中指定。 |
| S01 前置门控完成 | PASS | 已读取 `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md` 与 `process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md`，S01 CP6/CP7 均为 PASS。 |
| 禁止实现范围已确认 | PASS | 未修改 `experiments/run_experiment_13.py`、`engine/**`、`data/**`、`reports/**`、`.env`、`delivery/**`。 |
| CR008 并行边界已纳入 | PASS | S02 仅完成 benchmark/calendar 数据生产侧 dry-run、normalize、validate、catalog、reader/resolver 合同；未推进实验报告字段或文档。 |

## Checklist

| 检查项 | 结果 | 说明 |
|---|---|---|
| `benchmark-calendar-backfill` dry-run 组合入口 | PASS | `market_data/cli.py` 新增 `BenchmarkCalendarPlanSpec`、`build_benchmark_calendar_backfill_plan`、`cmd_benchmark_calendar_backfill` 与 parser；默认 `network_calls=0`、`writes=0`。 |
| 同区间 `trade_calendar` 与 `hs300_index` 规划 | PASS | dry-run payload 同时生成 `trade_calendar.daily` 与 `hs300_index.daily` 的 dataset plan，包含同一 `start_date/end_date`、`exchange`、`index_code`、relative target paths 和 resume policy。 |
| `trade_calendar` normalize 合同 | PASS | 复用既有 normalization 合同；新增测试通过 raw manifest 离线标准化 `trade_calendar` 4 行 calendar fixture。 |
| `trade_calendar` validate/catalog/read 合同 | PASS | `market_data/cli.py` 新增 `trade_calendar` validate 分支并写入 catalog；`market_data/readers.py` 支持 `exchange` filter。 |
| benchmark coverage 分母 | PASS | `validate_hs300_index` 和 resolver 使用 `trade_calendar.is_open=true` 后的 open dates；新增 `DENOMINATOR_MODE_BENCHMARK=trade_calendar_open_dates`。 |
| 禁止自然日 denominator 声明 benchmark 通过 | PASS | dry-run coverage gate 明确 `natural_day_denominator_allowed=false`；S02 测试断言 HS300 denominator 为 open calendar count 2，而不是自然日 4。 |
| resolver 向后兼容 | PASS | `resolve_hs300_benchmark` 仅新增 keyword-only 参数 `price_trade_dates` 和 metadata 字段 `denominator_mode` / `price_overlap`；未删除 CR005 已验证字段。 |
| resolver 同区间重叠门控 | PASS | 当传入 `price_trade_dates` 且与 HS300 benchmark 无同区间覆盖时，resolver 返回 `required_missing/unavailable`，`missing_reason=price_benchmark_overlap_missing`，不返回 available。 |
| reader/resolver import 边界 | PASS | `market_data/readers.py` 与 `market_data/benchmarks.py` 未导入 connector/runtime/storage，不触发 fetch/backfill；新增 AST 测试覆盖。 |
| 默认零联网零写入 | PASS | dry-run 入口默认 `network_calls=0`、`writes=0`；resolver/readers 只读 catalog/canonical fixture。 |
| 旧数据与旧报告隔离 | PASS | 测试全部使用 `tmp_path`；未读取、列出、迁移、复制、比对、删除旧 `data/**`，未读取或覆盖旧 `reports/data_quality_report.csv`。 |
| 凭据隔离 | PASS | 未读取 `.env`，未打印或记录 Tushare token/NAS 凭据；测试验证 payload 不泄漏 monkeypatch token 值。 |
| S03 并行限制 | PASS | 本 CP6 前未启动 S03；S02 触及 `validation/readers/benchmarks/cli`，S03 应等待 S02 CP6 PASS 后再处理共享文件冲突。 |

## Exit Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| 允许范围内代码实现完成 | PASS | 修改仅限允许的 market_data 文件、S02 测试文件、CP6 文件和 handoff completion 草稿。 |
| 必跑测试通过 | PASS | 两条用户指定 pytest 命令均通过。 |
| 追加离线回归通过 | PASS | 触及 shared reader/resolver/validation 后追加相关离线回归，15 项通过。 |
| 无真实联网或真实湖写入 | PASS | 未执行真实 Tushare 抓取、未写 `<configured-lake-root>`、未执行 lake 大规模读写。 |
| CP6 可交给 CP7 | PASS | 本文件记录 CP6 PASS；后续可由 meta-po 调度 meta-qa 执行 S02 CP7。 |

## Deliverables

| 产物 | 状态 | 说明 |
|---|---|---|
| `market_data/cli.py` | DONE | 新增 benchmark/calendar dry-run 规划入口；接入 `trade_calendar` validate/read；使用 `INTERFACE_TRADE_CALENDAR_DAILY` exact contract。 |
| `market_data/validation.py` | DONE | 新增 benchmark 与 calendar denominator mode；HS300 gap reason 支持 `calendar_missing`；generic validation 支持 exchange filter。 |
| `market_data/readers.py` | DONE | `read_dataset` 支持 `exchange` filter。 |
| `market_data/benchmarks.py` | DONE | resolver 增加 `price_trade_dates` 可选 keyword；coverage metadata 增加 denominator/price overlap；无同区间覆盖时不返回 available。 |
| `tests/test_cr007_benchmark_calendar_backfill.py` | DONE | 新增 5 个离线测试，覆盖 dry-run、normalize/validate/catalog/read、open denominator、resolver overlap、import boundary。 |
| `process/checks/CP6-CR007-S02-benchmark-calendar-backfill-CODING-DONE.md` | DONE | 本 CP6 检查文件。 |
| handoff completion 草稿 | DONE | 已回写 `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md` 的 dispatch/completion 草稿字段。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| dispatch.mode | resume_agent + send_input |
| platform | codex |
| agent_role | meta-dev |
| agent_name | dev-zhang |
| agent_id | 019e45c2-383c-7cc1-a732-ee1b7652e423 |
| thread_id | 019e45c2-383c-7cc1-a732-ee1b7652e423 |
| tool_name | resume_agent/send_input |
| resumed_at | 2026-05-21T07:09:00+08:00 |
| completed_at | 2026-05-21T07:09:00+08:00 |
| evidence_source | 用户 handoff 指定本次由主线程 resume_agent + send_input 恢复该 agent_id/thread_id 执行。 |
| inline_fallback | false |

## 测试结果

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr007_benchmark_calendar_backfill.py` | PASS：5 passed in 1.13s |
| `uv run --python 3.11 pytest -q tests/test_market_data_cli_comparison.py::test_hs300_index_cli_normalize_validate_and_read` | PASS：1 passed in 0.40s |
| `uv run --python 3.11 pytest -q tests/test_market_data_hs300_benchmark.py tests/test_market_data_multidataset_quality_readers.py` | PASS：15 passed in 0.94s |

## 安全确认

| 禁止项 | 结果 |
|---|---|
| 真实 Tushare 抓取 | 未执行 |
| 真实联网 backfill | 未执行 |
| `<configured-lake-root>` 写入 | 未执行 |
| 旧 `data/**` 读取/列出/迁移/复制/比对/删除/使用 | 未执行 |
| 旧 `reports/data_quality_report.csv` 读取/打开/覆盖/作为 truth 或 fixture | 未执行 |
| `.env`、Tushare token、NAS 凭据读取/打印/记录 | 未执行 |
| `experiments/run_experiment_13.py` / `engine/**` / `delivery/**` 修改 | 未执行 |

## 偏离 LLD 说明

无功能性偏离。实现保持 S02 数据生产侧范围；因 CR008 已纳入并行设计，未推进实验报告字段、运行报告文档或 S04 文件。

## 结论

CP6 PASS。CR007-S02 已完成离线编码与本地验证，可进入 S02 CP7；S03 可在 meta-po 确认本 CP6 PASS 后再启动，避免共享文件并行冲突。
