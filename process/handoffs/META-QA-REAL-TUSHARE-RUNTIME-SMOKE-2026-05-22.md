---
handoff_id: "META-QA-REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "CR-007+CR-008"
batch_id: "REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22"
scope: "runtime-real-data-smoke"
status: "completed"
created_at: "2026-05-22T06:35:47+08:00"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4caf-6244-7c22-b9d7-c785cf3c5cac"
  thread_id: "019e4caf-6244-7c22-b9d7-c785cf3c5cac"
  spawned_at: "2026-05-22T06:37:09+08:00"
  completed_at: "2026-05-22T06:44:03+08:00"
  evidence: "spawn_agent"
completion:
  completed_at: "2026-05-22T06:44:03+08:00"
  result: "FAIL"
  check_result: "process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md"
  summary: "真实 backfill 与 normalize 成功；validate 返回 quality_status=fail / dataset_status=duplicate_key；read 因 quality_failed 不可读；revalidate/replay 子命令当前 CLI 不支持。"
artifacts:
  expected_check_result: "process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md"
---

# META-QA 真实 Tushare 运行态烟测交接

## 目标

在用户明确授权后，真实执行 Tushare 小窗口抓取 / 回补，并继续执行 normalize、validate/read、revalidate/replay 可用性核验，判断当前真实数据链路是否可用、数据是否正确。

## 授权边界

| 项 | 约束 |
|---|---|
| 真实数据源 | 已授权真实调用 Tushare。 |
| 真实写入 | 已授权写入 `.env` / `MARKET_DATA_LAKE_ROOT` 指向的外部 lake root；不得把真实湖仓数据写入仓库内 `data/**`。 |
| 凭据 | 不得读取、打印、复制或写入 `.env` 内容；仅允许通过 `uv run --env-file .env` 由运行时加载。 |
| 输出脱敏 | 记录到检查结果时必须脱敏 token、真实 lake root 绝对路径、NAS/用户私有路径；可写为 `<redacted-lake-root>`。 |
| 范围 | 使用小窗口烟测，不执行全历史或大规模回补。 |

## 测试窗口

| 字段 | 值 |
|---|---|
| dataset | `hs300_index` |
| index_code | `399300.SZ` |
| start_date | `2024-01-02` |
| end_date | `2024-01-05` |
| open_trade_dates | `2024-01-02,2024-01-03,2024-01-04,2024-01-05` |
| run_id | `run-hs300-real-qa-20260522` |
| batch_id | `qa-real-20260522` |

## 必须执行的命令序列

所有命令使用同一前缀：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli
```

1. CLI 能力核验：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli --help
```

2. `hs300-backfill` dry-run：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522 --dry-run true
```

3. 真实 Tushare fetch / backfill：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522 --dry-run false --enable-real-source
```

4. normalize：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize --dataset hs300_index --run-id run-hs300-real-qa-20260522
```

5. validate：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05
```

6. read 抽样核验：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli read --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --columns trade_date,index_code,close --limit 10
```

7. revalidate / replay 可用性核验：

- 在 `--help` 输出中确认是否存在 `revalidate` 与 `replay` 子命令。
- 若不存在，检查结果中写为 `N/A / unsupported by current CLI`，不得伪造通过。
- 作为 replay-like/idempotency 烟测，可在首次真实 backfill 成功后，使用完全相同的 `run_id` 与 `batch_id` 再次执行第 3 条命令；期望结果为已有成功 manifest 触发 skip，且不新增真实抓取尝试。若实现输出不能直接证明未联网，则只记录 `status=skipped` 与 `attempts=0`，不要扩大结论。

## 检查结果文件要求

写入 `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`，必须包含：

1. Entry Criteria、Checklist、Exit Criteria、Deliverables 四段结构。
2. Agent Dispatch Evidence，记录本 handoff 的 `agent_id` / `thread_id` / `tool_name` / `spawned_at` / `completed_at`。
3. 每条命令的退出码和脱敏后的关键输出摘要。
4. 数据正确性结论：
   - fetch/backfill 是否成功；
   - normalize 是否生成标准化输出；
   - validate 是否 PASS；
   - read 抽样是否包含 4 个交易日、`index_code=399300.SZ`、`close` 非空且为正数；
   - revalidate/replay 当前是否为真实 CLI 能力，或只是 resume/idempotency 近似核验。
5. 若命令因网络、Tushare 权限、配额或凭据缺失失败，结论必须写成 `BLOCKED` 或 `FAIL`，并保留可复现命令，不得改写为 PASS。

## 结果摘要

| 项 | 结果 |
|---|---|
| 检查结果文件 | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` |
| 总结论 | `FAIL` |
| fetch/backfill | 真实执行成功，`results[0].status=success`；第二次相同 run_id/batch_id 执行返回 `status=skipped`，仅作为 replay-like/idempotency 近似核验。 |
| normalize | 成功，`row_count=4`。 |
| validate | 命令退出码 0 且 `ok=true`，但 `quality_status=fail`、`dataset_status=duplicate_key`。 |
| read 抽样 | 退出码 3，`dataset=hs300_index 不可读: quality_failed`，未能核验 4 个交易日和 `close` 正值。 |
| revalidate/replay | top-level `--help` 不包含 `revalidate` / `replay`，记录为 `N/A / unsupported by current CLI`。 |
