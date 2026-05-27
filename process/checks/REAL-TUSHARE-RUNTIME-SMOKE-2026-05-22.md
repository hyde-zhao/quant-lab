---
check_id: "REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22"
workflow_id: "local_backtest"
change_id: "CR-007+CR-008"
scope: "runtime-real-data-smoke"
dataset: "hs300_index"
index_code: "399300.SZ"
start_date: "2024-01-02"
end_date: "2024-01-05"
run_id: "run-hs300-real-qa-20260522"
batch_id: "qa-real-20260522"
executed_at: "2026-05-22T06:44:03+08:00"
result: "FAIL"
---

# 真实 Tushare 运行态 QA 烟测结果

## Entry Criteria

| 准则 | 状态 | 证据 |
|---|---|---|
| 已读取 handoff | PASS | 已读取 `process/handoffs/META-QA-REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`。 |
| 用户授权真实 Tushare 执行 | PASS | handoff 与用户消息均授权真实 fetch/backfill、normalize、validate、read。 |
| 凭据处理合规 | PASS | 未读取、打印或记录 `.env` 内容；仅通过 `uv run --env-file .env` 由运行时加载。 |
| 范围收敛 | PASS | 仅执行 `hs300_index` 小窗口：`399300.SZ`，`2024-01-02` 到 `2024-01-05`。 |
| 输出脱敏 | PASS | 报告中真实 lake root、token、私有路径均不落明文；lake root 统一写为 `<redacted-lake-root>`。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_id | `019e4caf-6244-7c22-b9d7-c785cf3c5cac` |
| thread_id | `019e4caf-6244-7c22-b9d7-c785cf3c5cac` |
| spawned_at | `2026-05-22T06:37:09+08:00` |
| completed_at | `2026-05-22T06:44:03+08:00` |
| evidence | `spawn_agent` |

## Checklist

| 检查项 | 状态 | 说明 |
|---|---|---|
| CLI `--help` 可执行 | PASS | 退出码 0；当前子命令包括 `plan, fetch, hs300-backfill, tushare-first-acquire, prices-long-horizon-plan, benchmark-calendar-backfill, normalize, validate, read, compare`。 |
| `hs300-backfill` dry-run | PASS | 退出码 0；`ok=true`、`network_calls=0`、`writes=0`。 |
| 真实 Tushare fetch/backfill | PASS | 首次真实成功执行退出码 0；`ok=true`、`network_calls=1`、结果项 `status=success`。 |
| normalize | PASS | 退出码 0；`ok=true`、`row_count=4`，生成 canonical 输出。 |
| validate | FAIL | 退出码 0 且 `ok=true`，但质量结论为 `quality_status=fail`、`dataset_status=duplicate_key`，不得记为 PASS。 |
| read 抽样 | FAIL | 退出码 3；当前 CLI 返回 `dataset=hs300_index 不可读: quality_failed`，未输出样本行。 |
| revalidate 子命令能力 | N/A | top-level `--help` 中不存在 `revalidate`，记录为 `N/A / unsupported by current CLI`。 |
| replay 子命令能力 | N/A | top-level `--help` 中不存在 `replay`，记录为 `N/A / unsupported by current CLI`。 |
| replay-like/idempotency 近似核验 | LIMITED | 使用完全相同 `run_id` / `batch_id` 第二次执行真实 backfill，退出码 0，结果项 `status=skipped`；输出未提供 `attempts=0`，且仍显示 `network_calls=1`，因此不能扩大为真正 replay PASS 或未联网证明。 |

## Executed Commands

所有命令均使用 `UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli ...`，未读取或打印 `.env`。

| # | 命令摘要 | 退出码 | 脱敏关键输出 |
|---|---|---:|---|
| 1 | `--help` | 0 | 子命令列表不包含 `revalidate` / `replay`。 |
| 2 | `hs300-backfill --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522 --dry-run true` | 0 | `ok=true`；`dry_run=true`；`lake_root=<redacted-lake-root>`；`network_calls=0`；`writes=0`；目标路径为 `raw/tushare/hs300_index.daily/20240102/qa-real-20260522.jsonl`、`canonical/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet`、`gold/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet`。 |
| 3a | `hs300-backfill ... --dry-run false --enable-real-source`（此前权限状态下默认沙箱尝试） | 3 | `ok=false`；`error_type=execution_error`；`error_message=manifest 写入失败: <redacted-lake-root>/manifest/market_data_manifest.jsonl`。随后按用户授权在具备外部 lake root 写入权限的环境重跑。 |
| 3b | `hs300-backfill ... --dry-run false --enable-real-source`（真实 backfill 成功执行） | 0 | `ok=true`；`dry_run=false`；`network_calls=1`；`results[0].status=success`；`raw_path=raw/tushare/hs300_index.daily/20240102/qa-real-20260522.jsonl`；`quality_path=quality/hs300_index/run-hs300-real-qa-20260522/quality.csv`。 |
| 4 | `normalize --dataset hs300_index --run-id run-hs300-real-qa-20260522` | 0 | `ok=true`；`row_count=4`；`canonical_paths=[<redacted-lake-root>/canonical/hs300_index/1.0/run_id=run-hs300-real-qa-20260522/part-qa-real-20260522.parquet]`。 |
| 5 | `validate --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05` | 0 | `ok=true`；coverage `actual_rows=4`、`expected_rows=4`、`missing_rate=0.0`；但 `quality_status=fail`、`dataset_status=duplicate_key`、`thresholds.max_duplicate_keys=0`。 |
| 6 | `read --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --columns trade_date,index_code,close --limit 10` | 3 | `ok=false`；`error_type=execution_error`；`error_message=dataset=hs300_index 不可读: quality_failed`。 |
| 7 | `hs300-backfill ... --dry-run false --enable-real-source`（第二次相同 run_id/batch_id，replay-like/idempotency 近似核验） | 0 | `ok=true`；`results[0].status=skipped`；`network_calls=1`；未输出 `attempts=0`，不能证明未联网或等同于正式 replay。 |

## Data Correctness

| 判断项 | 结论 | 说明 |
|---|---|---|
| fetch/backfill 是否成功 | PASS | 真实 backfill 成功，结果项 `status=success`，同一 run 后续重复执行返回 `status=skipped`。 |
| normalize 是否生成标准化输出 | PASS | normalize 输出 `row_count=4`，canonical 文件路径指向本次 `run_id`。 |
| validate 是否 PASS | FAIL | 命令退出码为 0 且 coverage 满足 4/4，但质量状态为 `fail`，数据集状态为 `duplicate_key`。 |
| read 抽样是否包含 4 个交易日 | FAIL | read 被 `quality_failed` 阻止，未输出样本行；不能确认抽样包含 4 个交易日。 |
| read 抽样是否全部为 `index_code=399300.SZ` | FAIL | read 未输出样本行；不能确认。 |
| read 抽样 `close` 是否非空且为正数 | FAIL | read 未输出样本行；不能确认。 |
| revalidate/replay 是否为当前真实 CLI 能力 | N/A | 当前 CLI top-level `--help` 不支持 `revalidate` / `replay` 子命令。重复 backfill 仅是 idempotency 近似核验。 |

## Exit Criteria

| 准则 | 状态 | 证据 |
|---|---|---|
| 必须命令均已执行或按 CLI 能力判定 N/A | PASS | help、dry-run、真实 backfill、normalize、validate、read、重复 backfill 均已执行；revalidate/replay 因当前 CLI 不支持记录为 N/A。 |
| 真实数据链路可用 | PARTIAL | fetch/backfill 与 normalize 可用；validate/read 在质量门处失败。 |
| 数据正确性可确认 | FAIL | validate 质量状态失败，read 无法输出样本，不能确认 close 非空且为正数。 |
| 结果文件已生成 | PASS | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`。 |
| handoff 完成字段已回填 | PASS | `process/handoffs/META-QA-REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`。 |

## Deliverables

| 交付物 | 状态 | 路径 |
|---|---|---|
| 真实 Tushare 运行态 QA 烟测检查结果 | DONE | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` |
| handoff dispatch/completion 字段与结果摘要 | DONE | `process/handoffs/META-QA-REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` |

## Conclusion

**结论：FAIL**

真实 Tushare fetch/backfill 与 normalize 已完成，且小窗口 coverage 显示 `actual_rows=4` / `expected_rows=4`。但 validate 输出 `quality_status=fail`、`dataset_status=duplicate_key`，read 抽样被 `quality_failed` 阻止，无法确认 4 个交易日样本、`index_code=399300.SZ` 和 `close` 非空为正数。因此本次真实运行态烟测不能通过。
