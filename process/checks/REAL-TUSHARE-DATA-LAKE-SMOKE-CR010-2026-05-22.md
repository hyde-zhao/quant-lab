---
checkpoint_id: "REAL-SMOKE-CR010"
checkpoint_name: "CR-010 真实 Tushare 小窗口数据湖 smoke"
type: "supplemental_real_runtime_check"
status: "FAIL"
owner: "meta-qa"
created_at: "2026-05-22T15:59:29+08:00"
checked_at: "2026-05-22T15:59:29+08:00"
target:
  phase: "story-execution"
  change_id: "CR-010"
  artifacts:
    - "process/STATE.md"
    - "process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md"
    - "process/HLD-DATA-LAKE.md"
    - "market_data/cli.py"
manual_checkpoint: ""
---

# REAL-SMOKE-CR010 真实 Tushare 小窗口数据湖 smoke 检查结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 当前变更为 CR-010 | PASS | `process/STATE.md` active_change=`CR-010` | 当前阶段为 `story-execution`。 |
| HLD-DATA-LAKE 已确认 | PASS | `process/HLD-DATA-LAKE.md` frontmatter `confirmed=true` | Companion HLD 要求小窗口真实回补先 dry-run，再真实执行并记录结果。 |
| 验证环境可进入 | PASS | `process/VALIDATION-ENV.yaml` `approval.confirmed=true` | 该文件仍含早期 W0 禁网边界；本次检查按当前用户对 CR-010 的显式授权执行。 |
| 真实执行授权存在 | PASS | `process/STATE.md` 与 CR-010 “真实执行授权更新” | 用户已授权真实联网、真实 Tushare 抓取、真实写湖和读取 `.env`；旧 `data/**` 对比暂缓。 |
| `.env` 可加载且不回显 | PASS | smoke 脚本配置探测 | `.env` 存在；`MARKET_DATA_LAKE_ROOT` 与 `TUSHARE_TOKEN` 均已配置；未输出任何值。 |
| lake root 安全边界 | PASS | smoke 脚本 guard | `MARKET_DATA_LAKE_ROOT` 未指向当前仓库 `data/**`；报告统一使用 `<configured-lake-root>`。 |

## 当前 CLI 合同确认

| 对象 | 当前合同 | 本次处理 |
|---|---|---|
| `tushare-first-acquire` | 支持 `prices`、`hs300_index`、`trade_calendar`、`index_weights`；真实执行需 `--dry-run false --enable-real-source` 和凭据环境变量 | 对 `trade_calendar`、`hs300_index`、`prices` 执行 dry-run + 真实抓取；对 `adj_factor` 执行 fail-fast 检查。 |
| `normalize` | 从 manifest/raw 生成 canonical parquet | 对 `trade_calendar`、`hs300_index` 执行成功；`prices` 因缺 `adj_factor` 失败。 |
| `validate` | 生成 quality candidate，并写入 unpublished catalog entry | 对 `trade_calendar`、`hs300_index` 执行成功。 |
| `publish` | 只发布非 fail quality entry | 对 `trade_calendar`、`hs300_index` 发布成功。 |
| `read` | 只读 published catalog current truth | 对 `trade_calendar`、`hs300_index` 读取成功。 |
| `replay` | `hs300_index` replay 当前按 legacy `hs300-backfill` 参数重算 idempotency；非 hs300 dataset 可按 manifest/raw 返回 ready-for-offline-replay | 本次 `hs300_index` replay 暴露 `replay_missing`。 |
| `prices-long-horizon-plan` | 规划 `prices.daily` 与 `prices.adj_factor`，但真实执行只允许 dry-run | dry-run PASS；`--dry-run false` 按当前合同 fail-fast。 |

## Smoke 配置

| 项 | 值 |
|---|---|
| 执行时间 | 2026-05-22T15:58:57+08:00 |
| 日期窗口 | 2024-01-02 至 2024-01-04 |
| 开市日期输入 | 2024-01-02, 2024-01-03, 2024-01-04 |
| 指数 | 399300.SZ |
| 股票 | 000001.SZ |
| 交易所 | SSE |
| lake root | `<configured-lake-root>` |
| run_id 前缀 | `cr010-smoke-20260522T155857` |
| 命令执行入口 | `uv run --python 3.11 python -m market_data.cli ...` |
| 旧 `data/**` | 未读取、未列出、未迁移、未复制、未比对、未删除 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | `trade_calendar` 小窗口真实全链路 | PASS | dry-run PASS；real acquire `network_calls=1` 且 batch `success`；normalize/read 均 3 行；validate `quality_status=pass`、coverage 3/3；publish `published` | 可作为本次真实写湖正向证据。 |
| 2 | `hs300_index` 小窗口真实抓取到 publish/read | PASS | dry-run PASS；real acquire `network_calls=1` 且 batch `success`；normalize/read 均 3 行；validate `quality_status=pass`、`denominator_mode=trade_calendar_open_dates`、coverage 3/3；publish `published` | 数据生产和只读消费主路径通过。 |
| 3 | `hs300_index` replay 不触发 provider | FAIL | `replay` 退出码 2，`error_type=replay_missing`，消息为缺少同一 run_id/batch_id/index_code/start/end 的 success manifest | replay 与 `tushare-first-acquire` 的 manifest idempotency 参数不一致；真实全链路未通过。 |
| 4 | `prices` 小窗口真实抓取 | PASS | dry-run PASS；real acquire `network_calls=1` 且 batch `success` | raw + manifest 写湖成功。 |
| 5 | `prices` normalize/validate/publish/read | FAIL | `normalize` 退出码 3，`error_type=execution_error`，`schema_mismatch: missing adj_factor` | `tushare-first-acquire prices` 默认 `adjustment_policy=qfq`，但当前真实 daily raw 未携带 `adj_factor`，且缺少可执行 `adj_factor` 配套回补。 |
| 6 | `adj_factor` 真实 Tushare-first 支持 | FAIL | `tushare-first-acquire --dataset adj_factor` 退出码 2，`error_type=unknown_dataset` | 当前 CLI 不支持 `adj_factor` 作为 Tushare-first dataset。 |
| 7 | `adj_factor` 规划与真实执行边界 | PASS | `prices-long-horizon-plan --dry-run true` PASS；`--dry-run false` 退出码 2，`error_type=source_disabled` | 当前仅可规划，不可真实执行；fail-fast 行为明确。 |
| 8 | readiness 汇总不伪造完整通过 | PASS | coverage 报告 `published_count=3`、`missing_required_count=1`、`current_truth_complete=false`；production exploratory=`warn`，production_strict=`fail` | 报告未声称 P0 数据湖完整。注意其中 `prices` published 来自既有 catalog entry，不是本次 smoke 产物。 |
| 9 | 安全边界 | PASS | 脚本汇总 `real_network_attempted=true`、`real_lake_write_attempted=true`、`old_data_operations_executed=false`、`credential_values_printed=false`、`private_paths_printed=false` | 本报告不包含 token、密码、私有路径或 `.env` 内容。 |

## 命令证据

| Dataset | 步骤 | 命令 | 结果 |
|---|---|---|---|
| `trade_calendar` | dry-run | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset trade_calendar --start-date 2024-01-02 --end-date 2024-01-04 --exchange SSE --run-id cr010-smoke-20260522T155857-trade-calendar --batch-id b1 --dry-run true` | PASS，`network_calls=0`，`writes=0` |
| `trade_calendar` | real acquire | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset trade_calendar --start-date 2024-01-02 --end-date 2024-01-04 --exchange SSE --run-id cr010-smoke-20260522T155857-trade-calendar --batch-id b1 --dry-run false --enable-real-source` | PASS，`network_calls=1`，batch `success` |
| `trade_calendar` | normalize | `uv run --python 3.11 python -m market_data.cli normalize --lake-root <configured-lake-root> --dataset trade_calendar --run-id cr010-smoke-20260522T155857-trade-calendar` | PASS，`row_count=3` |
| `trade_calendar` | validate | `uv run --python 3.11 python -m market_data.cli validate --lake-root <configured-lake-root> --dataset trade_calendar --start-date 2024-01-02 --end-date 2024-01-04 --exchange SSE --run-id cr010-smoke-20260522T155857-trade-calendar` | PASS，`quality_status=pass`，coverage 3/3 |
| `trade_calendar` | publish/read | `uv run --python 3.11 python -m market_data.cli publish/read ... --dataset trade_calendar ...` | PASS，publish `published`，read `row_count=3` |
| `hs300_index` | dry-run | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset hs300_index --start-date 2024-01-02 --end-date 2024-01-04 --index-code 399300.SZ --run-id cr010-smoke-20260522T155857-hs300-index --batch-id b1 --dry-run true` | PASS，`network_calls=0`，`writes=0` |
| `hs300_index` | real acquire | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset hs300_index --start-date 2024-01-02 --end-date 2024-01-04 --index-code 399300.SZ --run-id cr010-smoke-20260522T155857-hs300-index --batch-id b1 --dry-run false --enable-real-source` | PASS，`network_calls=1`，batch `success` |
| `hs300_index` | normalize | `uv run --python 3.11 python -m market_data.cli normalize --lake-root <configured-lake-root> --dataset hs300_index --run-id cr010-smoke-20260522T155857-hs300-index` | PASS，`row_count=3` |
| `hs300_index` | validate | `uv run --python 3.11 python -m market_data.cli validate --lake-root <configured-lake-root> --dataset hs300_index --start-date 2024-01-02 --end-date 2024-01-04 --index-code 399300.SZ --run-id cr010-smoke-20260522T155857-hs300-index --open-trade-dates 2024-01-02,2024-01-03,2024-01-04` | PASS，`quality_status=pass`，`denominator_mode=trade_calendar_open_dates`，coverage 3/3 |
| `hs300_index` | publish/read | `uv run --python 3.11 python -m market_data.cli publish/read ... --dataset hs300_index ...` | PASS，publish `published`，read `row_count=3` |
| `hs300_index` | replay | `uv run --python 3.11 python -m market_data.cli replay --lake-root <configured-lake-root> --dataset hs300_index --start-date 2024-01-02 --end-date 2024-01-04 --index-code 399300.SZ --run-id cr010-smoke-20260522T155857-hs300-index --batch-id b1` | FAIL，退出码 2，`error_type=replay_missing` |
| `prices` | dry-run | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset prices --start-date 2024-01-02 --end-date 2024-01-04 --symbol 000001.SZ --run-id cr010-smoke-20260522T155857-prices --batch-id b1 --dry-run true` | PASS，`network_calls=0`，`writes=0` |
| `prices` | real acquire | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset prices --start-date 2024-01-02 --end-date 2024-01-04 --symbol 000001.SZ --run-id cr010-smoke-20260522T155857-prices --batch-id b1 --dry-run false --enable-real-source` | PASS，`network_calls=1`，batch `success` |
| `prices` | normalize | `uv run --python 3.11 python -m market_data.cli normalize --lake-root <configured-lake-root> --dataset prices --run-id cr010-smoke-20260522T155857-prices` | FAIL，退出码 3，`schema_mismatch: missing adj_factor` |
| `adj_factor` | Tushare-first fail-fast | `uv run --python 3.11 python -m market_data.cli tushare-first-acquire --lake-root <configured-lake-root> --dataset adj_factor --start-date 2024-01-02 --end-date 2024-01-04 --symbol 000001.SZ --run-id cr010-smoke-20260522T155857-adj-factor --batch-id b1 --dry-run true` | FAIL，退出码 2，`error_type=unknown_dataset` |
| `adj_factor` | planner dry-run | `uv run --python 3.11 python -m market_data.cli prices-long-horizon-plan --lake-root <configured-lake-root> --start-date 2024-01-02 --end-date 2024-01-04 --symbols 000001.SZ --run-id cr010-smoke-20260522T155857-prices-planner --slice-days 3 --symbol-batch-size 1 --dry-run true` | PASS，`network_calls=0`，`writes=0` |
| `adj_factor` | planner real fail-fast | `uv run --python 3.11 python -m market_data.cli prices-long-horizon-plan --lake-root <configured-lake-root> --start-date 2024-01-02 --end-date 2024-01-04 --symbols 000001.SZ --run-id cr010-smoke-20260522T155857-prices-planner --slice-days 3 --symbol-batch-size 1 --dry-run false` | FAIL，退出码 2，`error_type=source_disabled` |
| readiness | coverage | `uv run --python 3.11 python -m market_data.cli report-readiness --lake-root <configured-lake-root> --report coverage --datasets trade_calendar,hs300_index,prices,adj_factor` | PASS，`published_count=3`，`missing_required_count=1`，`current_truth_complete=false` |
| readiness | production exploratory | `uv run --python 3.11 python -m market_data.cli report-readiness --lake-root <configured-lake-root> --report production --datasets trade_calendar,hs300_index,prices,adj_factor --realism-mode exploratory` | PASS，报告状态 `warn`，blocked claims 包含 `complete_p0_data_lake` |
| readiness | production strict | `uv run --python 3.11 python -m market_data.cli report-readiness --lake-root <configured-lake-root> --report production --datasets trade_calendar,hs300_index,prices,adj_factor --realism-mode production_strict` | PASS，报告状态 `fail` |

## 关键发现

| ID | 严重性 | 发现 | 影响 |
|---|---|---|---|
| CR010-SMOKE-001 | HIGH | `hs300_index` 使用 `tushare-first-acquire` 真实抓取、normalize、validate、publish、read 均成功，但 `replay` 无法命中同一 success manifest。 | HLD 要求小窗口 `plan/run/normalize/validate/publish/read/revalidate/replay` 全链路 PASS；当前 replay 阻断 CR-010 小窗口完整通过。 |
| CR010-SMOKE-002 | HIGH | `prices` 真实 daily 抓取成功，但 normalize 因 `schema_mismatch: missing adj_factor` 失败。 | `prices` 无法从本次真实 raw 推进到 canonical/quality/catalog/read；短期 HS300 成分股票价格湖仍不可用。 |
| CR010-SMOKE-003 | HIGH | `adj_factor` 没有可真实执行的 Tushare-first CLI 入口；`prices-long-horizon-plan` 只支持 dry-run。 | `prices` qfq 合同缺少真实配套因子生产路径，导致 `prices` normalize 主路径断裂。 |
| CR010-SMOKE-004 | MEDIUM | readiness coverage 中的 `prices` published entry 来自既有 catalog（run_id=`cr006-momentum-symbols-realrun`），不是本次 CR-010 smoke 产物。 | readiness 汇总不能作为本次 `prices` 通过证据；需要 run-id/date-range 可追溯的 smoke 隔离策略。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 小窗口真实联网执行完成 | PASS | `trade_calendar`、`hs300_index`、`prices` real acquire 均 `network_calls=1` | 已发生真实 Tushare 请求。 |
| 小窗口真实写湖完成 | PASS | real acquire batch `success`；`trade_calendar`/`hs300_index` canonical、quality、catalog、read 均有结果 | 写入范围仅为 `<configured-lake-root>`。 |
| 优先 dataset 全部通过 | FAIL | `prices` normalize 失败；`adj_factor` unsupported；`hs300_index` replay 失败 | 不满足 CR-010 小窗口完整 smoke 放行条件。 |
| 未泄露凭据或私有路径 | PASS | 报告仅使用 `<configured-lake-root>`；未打印 `.env` 内容 | Tushare token、密码、私有路径均未写入报告。 |
| 旧 `data/**` 对比暂缓 | PASS | readiness payload `old_data_operations` 为 0；执行命令未引用 repo `data/**` | 未读旧数据。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| REAL-SMOKE 检查记录 | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-2026-05-22.md` | PASS | 本文件。 |
| 真实 smoke 结论 | 本文件 “结论” | FAIL | 真实网络和写湖已执行，但全链路未通过。 |
| 后续修复建议 | 本文件 “下一步” | PASS | 提供可执行整改方向。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| mode | `direct-main-thread` |
| agent_role | `meta-qa` |
| tool_name | `functions.exec_command` / `functions.apply_patch` |
| limitation | 当前会话由用户直接指定 “你是 meta-qa”，未使用平台子 agent 调度工具。 |

## 结论

- 结论：`FAIL`
- 阻断项：
  - `hs300_index` replay 对 `tushare-first-acquire` 真实 manifest 不兼容，返回 `replay_missing`。
  - `prices` normalize 缺 `adj_factor`，无法进入 validate/publish/read。
  - `adj_factor` 当前没有可真实执行的 CLI 抓取入口。
- 豁免项：无。
- 下一步：
  - 修正 `replay` 对 `tushare-first-acquire hs300_index` 的 manifest 匹配逻辑，或实现按 run_id/batch_id/dataset/interface 查找 success manifest 的 generic replay。
  - 为 `adj_factor` 增加真实 Tushare-first CLI 入口，映射 `prices.adj_factor`，并与 `prices.daily` normalize join。
  - 明确 `prices` 真实 daily 的 adjustment policy：若默认 qfq，则必须强制配套因子；若允许未复权 smoke，则 CLI/contract 需显式声明并避免伪装为 qfq。
  - 为 smoke readiness 增加 run_id/date-range 隔离或报告字段，避免既有 catalog current truth 被误读为本次 smoke 通过证据。
