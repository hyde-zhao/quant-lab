---
check_id: "REAL-TUSHARE-CR014-S09-YTD-SMOKE-2026-05-27"
type: "real_run_smoke"
status: "PASS_PARTIAL_SCOPE"
owner: "meta-po"
created_at: "2026-05-27T21:33:34+08:00"
checked_at: "2026-05-27T21:33:34+08:00"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
authorization_id: "CR014-S09-YTD-20260527-001"
date_range: "2026-01-01..2026-05-26"
lake_root: "/tmp/local-backtest-cr014-s09-ytd-lake"
source: "tushare"
credential_source_policy: "uv --env-file .env; token value not printed, persisted, or stored"
publish_current_pointer: false
duckdb_dependency_change: 0
duckdb_files_created: 0
---

# REAL Tushare CR014-S09 2026 YTD Smoke

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| S09 CP7 已通过 | PASS | `process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md` | CP7 验证的是代码合同，不自动授权真实 run。 |
| 用户授权读取 `.env` token | PASS | 用户回复“你可以读 .env 中的 token，执行真实的抓取” | 使用 `uv --env-file .env` 注入运行时环境；未打印、未落盘 token 值。 |
| 日期窗口明确 | PASS | 用户要求“2026 年开始至今”；S09 默认 pilot | 当前执行窗口为 `2026-01-01..2026-05-26`，未把 2026-05-27 当前日作为已闭市日。 |
| lake root 明确 | PASS | 命令参数 | `/tmp/local-backtest-cr014-s09-ytd-lake`，不使用旧 repo `data/**` 或 `reports/**`。 |
| publish 边界明确 | PASS | 命令范围与 S09 决策 | 本次只写 raw/manifest，不 publish current pointer。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | S09 plan 生成 | PASS | `s09-plan` 输出 `status=planned` | 计划窗口为月度拆分；run gate 仍显示 `real_run_authorized=false`，因此未用 S09 合同 CLI 直接执行。 |
| 2 | 受控真实抓取命令可用 | PASS | `tushare-first-acquire --dry-run true` | `stock_basic`、`trade_calendar`、`hs300_index` dry-run 均通过。 |
| 3 | `.env` token 只在运行时读取 | PASS | `uv run --env-file .env --group tushare ...` | 未在输出、文档或 memory 中记录 token 值。 |
| 4 | `stock_basic` SSE 快照抓取 | PASS | raw 文件行数 | 首次默认 `exchange=SSE`，保留为子集证据。 |
| 5 | `stock_basic` 全交易所快照抓取 | PASS | raw 文件行数 | 追加 `--exchange ''`，得到全交易所上市清单快照。 |
| 6 | `trade_calendar` 抓取 | PASS | raw 文件行数 | `2026-01-01..2026-05-26`，SSE calendar。 |
| 7 | `hs300_index` 抓取 | PASS | raw 文件行数 | `399300.SZ` index daily。 |
| 8 | `prices` 行情小样本抓取 | PASS | raw 文件行数 | 仅 `000001.SZ`；用于验证行情链路，不代表全 A prices 完成。 |
| 9 | `adj_factor` 小样本抓取 | PASS | raw 文件行数 | 仅 `000001.SZ`；用于验证复权因子链路，不代表全 A adj_factor 完成。 |
| 10 | current pointer 未发布 | PASS | 本次未运行 `publish` | `catalog current pointer` 未更新。 |
| 11 | DuckDB 未引入 | PASS | `.duckdb` scan 无输出 | 未创建 `.duckdb`，未打开/写入 DuckDB。 |
| 12 | 仓库缓存无残留 | PASS | `.venv` / `__pycache__` scan 无输出 | 运行使用 `/tmp` venv 与 `PYTHONDONTWRITEBYTECODE=1`。 |

## Run Results

| Dataset / Scope | Interface | Run ID | Status | Network Calls | Raw Lines | Data Rows | 说明 |
|---|---|---|---|---:|---:|---:|---|
| `stock_basic` SSE | `stock_basic.snapshot` | `CR014-S09-YTD-20260527-001-stock-basic` | success | 1 | 2316 | 2315 | CLI 默认 `exchange=SSE`。 |
| `stock_basic` all exchanges | `stock_basic.snapshot` | `CR014-S09-YTD-20260527-001-stock-basic-all` | success | 1 | 5525 | 5524 | 使用 `--exchange ''` 补抓全交易所上市清单。 |
| `trade_calendar` | `trade_calendar.daily` | `CR014-S09-YTD-20260527-001-trade-calendar` | success | 1 | 147 | 146 | 2026 YTD calendar。 |
| `hs300_index` | `hs300_index.daily` | `CR014-S09-YTD-20260527-001-hs300-index` | success | 1 | 93 | 92 | `399300.SZ`。 |
| `prices` sample | `prices.daily` | `CR014-S09-YTD-20260527-001-prices-000001-SZ` | success | 1 | 93 | 92 | 仅 `000001.SZ`。 |
| `adj_factor` sample | `prices.adj_factor` | `CR014-S09-YTD-20260527-001-adj-factor-000001-SZ` | success | 1 | 93 | 92 | 仅 `000001.SZ`。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 临时 lake raw 文件存在 | PASS | `find /tmp/local-backtest-cr014-s09-ytd-lake -maxdepth 8 -type f -print` | 6 个 raw 文件 + 1 个 manifest 文件。 |
| Manifest 追加成功 | PASS | `wc -l .../manifest/market_data_manifest.jsonl` | manifest 共 6 行，对应 6 次真实抓取。 |
| 真实网络调用有审计 | PASS | 命令 JSON 输出 | 6 次命令均 `network_calls=1` 且 status success。 |
| 未 publish current pointer | PASS | 未执行 publish 命令 | 本次 raw/manifest 仍不是 current truth。 |
| 未创建 DuckDB 文件 | PASS | `find /tmp/local-backtest-cr014-s09-ytd-lake -name '*.duckdb' -print` 无输出 | DuckDB 仍未参与写入。 |
| full-A prices 未完成 | PASS_PARTIAL_SCOPE | `prices` / `adj_factor` 仅跑 `000001.SZ` | 全 A 行情需要 symbol batching runner 或显式分批授权。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 真实 raw lake | `/tmp/local-backtest-cr014-s09-ytd-lake/raw/...` | PASS | 临时 lake root，非旧 repo `data/**`。 |
| 真实 manifest | `/tmp/local-backtest-cr014-s09-ytd-lake/manifest/market_data_manifest.jsonl` | PASS | 6 行。 |
| 本运行记录 | `process/checks/REAL-TUSHARE-CR014-S09-YTD-SMOKE-2026-05-27.md` | PASS | 当前文件。 |

## 结论

- 结论：`PASS_PARTIAL_SCOPE`
- 已完成：2026 YTD 真实 Tushare smoke，覆盖 `stock_basic` 全交易所、`trade_calendar`、`hs300_index`、`prices(000001.SZ)`、`adj_factor(000001.SZ)`。
- 未完成：全 A `prices` / `adj_factor` 批量行情回补；当前 CLI 的 long-horizon prices 入口仍是 plan-only，真实全 A 行情需要新增/批准 symbol batching runner 或显式分批命令。
- 未授权 / 未执行：publish current pointer、normalize/validate 自动发布、retention execute、DuckDB open/write/dependency。
