---
check_id: "REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22"
workflow_id: "local_backtest"
change_id: "CR-009"
scope: "runtime-real-data-resmoke"
dataset: "hs300_index"
index_code: "399300.SZ"
start_date: "2024-01-02"
end_date: "2024-01-05"
run_id: "run-hs300-real-qa-20260522"
batch_id: "qa-real-20260522"
executed_at: "2026-05-22T07:57:32+08:00"
result: "FAIL"
---

# CR-009 真实 Tushare 运行态复验结果

## Entry Criteria

| 准则 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 已读取真实复验 handoff | PASS | `process/handoffs/META-QA-CR009-REAL-TUSHARE-RUNTIME-RESMOKE-2026-05-22.md` | handoff 指定本次小窗口、命令序列、脱敏边界和输出文件。 |
| 用户已授权真实复验 | PASS | handoff `authorization_text=授权真实复验` | 本轮允许 `uv run --env-file .env` 由运行时加载凭据，并允许在授权 lake root 小窗口复验。 |
| 原 FAIL 基线已保留 | PASS | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | 本轮未覆盖原始 FAIL 报告，结果写入新文件。 |
| CR-009 已批准且 CP6/CP7 离线通过 | PASS | CR、CP6、CP7 | `CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md` 与 `CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md` 均为 `PASS`。 |
| `VALIDATION-ENV.yaml` 已确认 | PASS | `process/VALIDATION-ENV.yaml` | `approval.confirmed=true`。其中历史 STORY-001 的禁止网络范围与本次 CR-009 用户最新授权不一致，本轮以用户最新授权和 CR-009 handoff 为复验边界。 |
| 凭据与路径安全边界 | PASS | 本轮命令与本报告 | 未读取、打印、复制或写入 `.env` 内容；报告中 lake root 和私有路径均脱敏为 `<redacted-lake-root>` / `<redacted-path>`。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_id | `019e4cf7-4f22-7030-974c-85f92218d0ad` |
| thread_id | `019e4cf7-4f22-7030-974c-85f92218d0ad` |
| agent_name | `qa-kong` |
| spawned_at | `2026-05-22T07:55:40+08:00` |
| completed_at | 本文件 `executed_at=2026-05-22T07:57:32+08:00`；handoff/STATE/CR 完成字段按用户约束不由本轮回填。 |
| evidence | `process/handoffs/META-QA-CR009-REAL-TUSHARE-RUNTIME-RESMOKE-2026-05-22.md` |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | CLI help 包含 `revalidate` / `replay` | PASS | 命令 #1 退出码 0 | top-level help 子命令列表包含 `validate,revalidate,replay,read`。 |
| 2 | `hs300-backfill` dry-run 无网络无写入 | PASS | 命令 #2 退出码 0 | `ok=true`、`dry_run=true`、`network_calls=0`、`writes=0`。 |
| 3 | 真实 `hs300-backfill` 小窗口可复验 | PASS | 命令 #3 退出码 0 | 已存在 success manifest，返回 `results[0].status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。 |
| 4 | `normalize` 可生成/复用 canonical 输出 | PASS | 命令 #4 退出码 0 | `ok=true`、`row_count=4`，canonical 路径已脱敏。 |
| 5 | `validate` 质量门通过 | PASS | 命令 #5 退出码 0 | `quality_status=pass`、`dataset_status=available`，coverage 为 4/4。 |
| 6 | `read` 抽样可读且数据正确 | PASS | 命令 #6 退出码 0 | 返回 4 行；全部 `index_code=399300.SZ`；`close` 均为非空正数。 |
| 7 | `revalidate` 复验质量门通过且无网络/canonical 写入 | PASS | 命令 #7 退出码 0 | `command=revalidate`、`quality_status=pass`、`dataset_status=available`、`network_calls=0`、`canonical_writes=0`。 |
| 8 | `replay` 已有 success manifest 时应 skipped 且无网络/写入 | FAIL | 命令 #8 退出码 2 | 按 handoff 与用户指定参数执行时，CLI 报错缺少必填 `--lake-root`，未能进入 skipped/attempts=0/network_calls=0/writes=0 判定。未追加参数重试。 |
| 9 | 输出脱敏 | PASS | 本报告 | 未记录 token、`.env` 内容、真实 lake root 绝对路径、NAS 路径或用户私有路径。 |
| 10 | 禁止范围未越界 | PASS | git 写入范围 | 本轮只新增本检查结果文件；未修改实现代码、测试代码、原 FAIL 基线、handoff、STATE 或 CR。 |

## Executed Commands

所有命令均使用统一前缀：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli
```

未读取或打印 `.env` 内容。以下为脱敏后的关键输出摘要。

| # | 命令摘要 | 退出码 | 脱敏关键输出 |
|---|---|---:|---|
| 1 | `--help` | 0 | 子命令列表包含 `normalize,validate,revalidate,replay,read`。 |
| 2 | `hs300-backfill --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522 --dry-run true` | 0 | `ok=true`；`dry_run=true`；`lake_root=<redacted-lake-root>`；`network_calls=0`；`writes=0`；目标相对路径包括 `raw/tushare/hs300_index.daily/20240102/qa-real-20260522.jsonl`、`canonical/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet`、`gold/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet`。 |
| 3 | `hs300-backfill --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522 --dry-run false --enable-real-source` | 0 | `ok=true`；`dry_run=false`；`network_calls=0`；`writes=0`；`results[0].status=skipped`；`results[0].attempts=0`；`raw_path=raw/tushare/hs300_index.daily/20240102/qa-real-20260522.jsonl`。 |
| 4 | `normalize --dataset hs300_index --run-id run-hs300-real-qa-20260522` | 0 | `ok=true`；`row_count=4`；`canonical_paths=[<redacted-lake-root>/canonical/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet]`。 |
| 5 | `validate --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05` | 0 | `ok=true`；`quality_status=pass`；`dataset_status=available`；coverage `actual_rows=4`、`expected_rows=4`、`missing_rate=0.0`、`open_trade_dates_count=4`；`thresholds.max_duplicate_keys=0`；质量输出路径已脱敏为 `<redacted-lake-root>/quality/...`。 |
| 6 | `read --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --columns trade_date,index_code,close --limit 10` | 0 | `ok=true`；`row_count=4`；样本为 `2024-01-02 close=3386.3522`、`2024-01-03 close=3378.2971`、`2024-01-04 close=3347.0519`、`2024-01-05 close=3329.1114`；全部 `index_code=399300.SZ`。 |
| 7 | `revalidate --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05` | 0 | `ok=true`；`command=revalidate`；`quality_status=pass`；`dataset_status=available`；coverage 4/4；`network_calls=0`；`canonical_writes=0`；`quality_writes=2`；`catalog_writes=1`；质量输出路径已脱敏。 |
| 8 | `replay --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522` | 2 | stderr 显示 `python -m market_data.cli replay: error: the following arguments are required: --lake-root`。未追加 `--lake-root`，未扩大范围重试。 |

## Data Correctness

| 判断项 | 结论 | 说明 |
|---|---|---|
| help 是否包含 `revalidate` / `replay` | PASS | top-level help 已列出两个子命令。 |
| fetch/backfill 是否成功或安全跳过 | PASS | 本次相同 `run_id` / `batch_id` 已存在 success manifest，真实 backfill 返回 skipped，且 `attempts=0`、`network_calls=0`、`writes=0`。 |
| normalize 是否可用 | PASS | `row_count=4`，canonical 输出指向本次 `run_id`。 |
| validate 是否 PASS | PASS | `quality_status=pass`、`dataset_status=available`，coverage 为 4/4，duplicate key 阈值仍为 0。 |
| read 是否返回 4 个交易日 | PASS | 返回 `2024-01-02`、`2024-01-03`、`2024-01-04`、`2024-01-05` 共 4 行。 |
| read 是否全部为目标指数 | PASS | 4 行 `index_code` 均为 `399300.SZ`。 |
| read 的 `close` 是否非空正数 | PASS | 4 个 `close` 分别为 3386.3522、3378.2971、3347.0519、3329.1114，均为正数。 |
| revalidate 是否 PASS 且零网络 / 零 canonical 写入 | PASS | `quality_status=pass`、`network_calls=0`、`canonical_writes=0`。 |
| replay 是否满足已有 success manifest 的 skipped 口径 | FAIL | 指定命令未能执行到 replay 逻辑，因缺少必填 `--lake-root` 直接退出 2；无法证明 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。 |

## Exit Criteria

| 准则 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 必须命令序列均已按给定参数执行 | PASS | 命令 #1-#8 | 第 8 条失败后未扩大范围重试。 |
| 数据链路质量门关闭原失败 | PASS | validate/read/revalidate 输出 | 原 FAIL 基线中的 `duplicate_key` / `quality_failed` 在 validate/read/revalidate 链路上已关闭。 |
| replay CLI 复验口径满足 | FAIL | 命令 #8 | `replay` 对本次指定命令仍要求 `--lake-root`，与 handoff/用户指定命令序列不一致。 |
| 安全边界满足 | PASS | 本报告和执行过程 | 未读取 `.env` 内容；报告脱敏；未记录真实 lake root 或私有路径。 |
| 结果文件已生成 | PASS | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | 本文件。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CR-009 真实 Tushare 小窗口复验结果 | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | DONE | 本文件，结论为 `FAIL`。 |
| 原 FAIL 基线 | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | PRESERVED | 未覆盖、未修改。 |
| handoff / STATE / CR 回填 | 由 meta-po 处理 | NOT_MODIFIED | 用户限定本轮只写本检查结果文件。 |

## Conclusion

**结论：FAIL**

CR-009 修复后的真实小窗口链路在 backfill skipped、normalize、validate、read、revalidate 上均通过：`validate` 已为 `quality_status=pass` / `dataset_status=available`，`read` 返回 4 行目标指数样本且 `close` 均为正数，`revalidate` 为零网络和零 canonical 写入。

但第 8 条 `replay` 按用户指定参数执行时退出码为 2，错误为缺少必填 `--lake-root`。因此本轮不能按通过口径确认 `replay` 在已有 success manifest 时返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。该问题是新的复验阻塞项，应由 meta-po 回填 handoff/STATE/CR 后路由后续修复或决策。
