---
check_id: "REAL-TUSHARE-CR014-S09-YTD-VERIFY-2026-05-28"
type: "real_run_verification"
status: "PASS_PARTIAL_SCOPE_CONFIGURED_LAKE_BLOCKED"
owner: "meta-po"
created_at: "2026-05-28T22:04:05+08:00"
checked_at: "2026-05-28T22:04:05+08:00"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
authorization_id: "USER-APPROVED-ENV-TUSHARE-YTD-2026-05-28"
date_range: "2026-01-01..2026-05-28"
lake_root: "/tmp/local-backtest-cr014-s09-ytd-lake-20260528"
configured_lake_root: "<redacted-env-lake-root>"
configured_lake_root_fingerprint: "23cef1647d28"
source: "tushare"
credential_source_policy: "uv --env-file .env; token value not printed, persisted, documented, or stored"
publish_current_pointer: false
duckdb_dependency_change: 0
duckdb_files_created: 0
---

# REAL Tushare CR014-S09 2026 YTD Verification

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 用户授权读取 `.env` | PASS | 用户要求“你可以读取.env中的内容，进行验证” | 只通过 `uv --env-file .env` 注入运行时环境；未打印 token 值。 |
| 日期窗口明确 | PASS | 用户要求“读取 2026 年初至今的数据” | 本次窗口按当前日期执行为 `2026-01-01..2026-05-28`。 |
| S09 CP6 / CP7 已通过 | PASS | `process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md`；`process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md` | 代码合同已验证；真实运行仍由本次用户授权触发。 |
| `.env` token 可用 | PASS | 运行时预检 | `TUSHARE_TOKEN` 存在且长度大于 10；未记录实际值。 |
| `.env` 配置 lake root 可写 | BLOCKED | 运行时预检 | 配置 lake root 对当前运行用户返回 `PermissionError`；未写入该路径，未记录明文路径。 |
| 受控验证 lake root 可写 | PASS | `/tmp/local-backtest-cr014-s09-ytd-lake-20260528` | 为避免权限阻塞真实抓取验证，本次写入隔离的临时验证湖。 |
| publish 边界明确 | PASS | 本次命令范围 | 只写 raw 和 manifest；不执行 normalize / validate / publish，不更新 current pointer。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | `.env` 作为凭据来源 | PASS | `uv run --env-file .env --group tushare ...` | token 只在进程环境中使用。 |
| 2 | 配置 lake root 预检 | BLOCKED | `lake_root_access_error=PermissionError` | 这是文件系统权限问题，不是 provider/token 失败；需要修复挂载目录权限后才能写配置湖。 |
| 3 | `stock_basic` 全交易所快照真实抓取 | PASS | `stock_basic.snapshot` raw + manifest | `exchange=""`、`list_status=L`，返回 5524 行。 |
| 4 | `trade_calendar` 真实抓取 | PASS | `trade_calendar.daily` raw + manifest | SSE，`2026-01-01..2026-05-28`，返回 148 行。 |
| 5 | 沪深300指数日行情真实抓取 | PASS | `hs300_index.daily` raw + manifest | `399300.SZ`，返回 94 行。 |
| 6 | `prices` 样本 1 真实抓取 | PASS | `prices.daily` raw + manifest | `000001.SZ`，返回 94 行。 |
| 7 | `adj_factor` 样本 1 真实抓取 | PASS | `prices.adj_factor` raw + manifest | `000001.SZ`，返回 94 行。 |
| 8 | `prices` 样本 2 真实抓取 | PASS | `prices.daily` raw + manifest | `600000.SH`，返回 94 行。 |
| 9 | `adj_factor` 样本 2 真实抓取 | PASS | `prices.adj_factor` raw + manifest | `600000.SH`，返回 94 行。 |
| 10 | manifest 追加 | PASS | `manifest/market_data_manifest.jsonl` | 本次 run 写入 7 条 manifest 记录，状态均为 `success`。 |
| 11 | raw 行数与 manifest 行数一致 | PASS | 二次核验脚本 | 7 个 batch 的 `manifest.raw_row_count` 均等于 raw 实际数据行数。 |
| 12 | current pointer 未发布 | PASS | 未执行 `publish` | raw/manifest 仍是审计证据，不是 current truth。 |
| 13 | DuckDB 未参与写入 | PASS | 命令范围 | 未创建 `.duckdb`，未引入 DuckDB 写路径。 |
| 14 | 全 A prices/adj_factor 批量完成度 | PASS_PARTIAL_SCOPE | 当前 CLI 能力 | 已验证 symbol 级真实写湖；全 A 长周期真实批量 runner 仍未实现。 |

## Run Results

本次真实运行使用 run id：`run-cr014-s09-ytd-verify-20260528-140339`。

| Dataset / Scope | Interface | Batch ID | Status | Data Rows | Date Min | Date Max | Symbol Count |
|---|---|---|---|---:|---|---|---:|
| `stock_basic` all exchanges | `stock_basic.snapshot` | `stock-basic-all-L` | success | 5524 | 19901201 | 20260527 | 5524 |
| `trade_calendar` SSE | `trade_calendar.daily` | `trade-calendar-sse` | success | 148 | 20260101 | 20260528 | 0 |
| `hs300_index` | `hs300_index.daily` | `hs300-399300-SZ` | success | 94 | 20260105 | 20260528 | 1 |
| `prices` sample | `prices.daily` | `prices-000001-SZ` | success | 94 | 20260105 | 20260528 | 1 |
| `adj_factor` sample | `prices.adj_factor` | `adj-factor-000001-SZ` | success | 94 | 20260105 | 20260528 | 1 |
| `prices` sample | `prices.daily` | `prices-600000-SH` | success | 94 | 20260105 | 20260528 | 1 |
| `adj_factor` sample | `prices.adj_factor` | `adj-factor-600000-SH` | success | 94 | 20260105 | 20260528 | 1 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 真实 provider 调用成功 | PASS | 7 个 batch `status=success` | 覆盖基础数据、真实 benchmark、价格、复权因子样本。 |
| raw 文件存在 | PASS | 7 个 `raw_path_present=true` 且 `raw_exists=true` | 写入隔离验证湖 `/tmp/local-backtest-cr014-s09-ytd-lake-20260528`。 |
| manifest 记录存在 | PASS | `manifest_record_count=7` | manifest 状态集合为 `["success"]`。 |
| 行数一致性 | PASS | 二次核验 | 每个 raw 文件实际行数等于 manifest `raw_row_count`。 |
| 配置 lake root 写入 | BLOCKED | `.env` lake root 预检 | 当前运行用户无权限访问配置 lake root；需要修复挂载目录权限后重跑。 |
| current pointer 未变更 | PASS | 未执行 publish | 不污染 current truth。 |
| full-A prices/adj_factor | PASS_PARTIAL_SCOPE | 当前执行仅 2 个样本 symbol | 全 A 行情和复权因子需要新增真实批量 runner 或显式分批命令。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 真实 raw 验证湖 | `/tmp/local-backtest-cr014-s09-ytd-lake-20260528/raw/...` | PASS | 7 个 raw jsonl 文件。 |
| 真实 manifest | `/tmp/local-backtest-cr014-s09-ytd-lake-20260528/manifest/market_data_manifest.jsonl` | PASS | 本次 run 7 条记录。 |
| 本运行记录 | `process/checks/REAL-TUSHARE-CR014-S09-YTD-VERIFY-2026-05-28.md` | PASS | 当前文件。 |

## 结论

- 结论：`PASS_PARTIAL_SCOPE_CONFIGURED_LAKE_BLOCKED`
- 已验证：`.env` 中真实 Tushare token 可用于 provider 抓取；raw 写入、manifest 追加、checksum/row count 审计链路在受控验证湖中工作正常。
- 配置湖阻断：`.env` 配置的 lake root 当前对运行用户返回 `PermissionError`；本次没有写入该配置路径。修复目录权限后，可以用相同 run scope 重跑到配置湖。
- 未完成：全 A `prices` / `adj_factor` 长周期批量真实回补；当前已证明 symbol 级接口真实可写湖，但还不能声明全 A prices/adj_factor 完成。
- 未执行：normalize、validate、publish current pointer、DuckDB 写入、DuckDB 依赖引入、旧 `data/**` 迁移。
