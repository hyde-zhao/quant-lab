---
handoff_id: "META-QA-CR009-REAL-TUSHARE-RUNTIME-RESMOKE-2026-05-22"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest"
change_id: "CR-009"
linked_baseline: "process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md"
batch_id: "CR009-REAL-RESMOKE"
scope: "runtime-real-data-resmoke"
status: "completed"
created_at: "2026-05-22T07:53:31+08:00"
authorization:
  authorized_by: "user"
  authorized_at: "2026-05-22T07:53:31+08:00"
  authorization_text: "授权真实复验"
dispatch:
  mode: "spawn_agent"
  tool_name: "spawn_agent"
  agent_id: "019e4cf7-4f22-7030-974c-85f92218d0ad"
  agent_name: "qa-kong"
  thread_id: "019e4cf7-4f22-7030-974c-85f92218d0ad"
  spawned_at: "2026-05-22T07:55:40+08:00"
  completed_at: "2026-05-22T07:57:32+08:00"
result:
  check_result: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md"
  status: "FAIL"
  summary: "validate/read/revalidate 已恢复 PASS；replay 按 handoff 指定参数执行时因缺少必填 --lake-root 被 argparse 拒绝，阻断 CR-009 关闭。"
---

# META-QA CR-009 真实 Tushare 运行态复验交接

## 目标

在用户明确授权后，真实执行 CR-009 修复后的 Tushare 小窗口复验，确认原失败基线中的 `hs300_index duplicate_key` / `quality_failed` 是否被关闭，并核验新增 `revalidate` / `replay` CLI 能力。

## 授权边界

| 项 | 约束 |
|---|---|
| 授权原文 | `授权真实复验` |
| 真实数据源 | 已授权真实调用 Tushare，仅限本文件定义的小窗口。 |
| 真实写入 | 已授权写入 `.env` / `MARKET_DATA_LAKE_ROOT` 指向的外部 lake root；不得写仓库内真实 `data/**`。 |
| 凭据 | 不得读取、打印、复制或写入 `.env` 内容；仅允许通过 `uv run --env-file .env` 由运行时加载。 |
| 输出脱敏 | 写入检查结果前必须脱敏 token、真实 lake root 绝对路径、NAS 路径和用户私有路径；统一写为 `<redacted-lake-root>` 或 `<redacted-path>`。 |
| 基线保留 | 不得覆盖 `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md`，复验结果写入新文件。 |

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

所有命令使用同一前缀，不得改为裸 Python 或 pip：

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli
```

1. CLI 能力核验：`--help`，确认 `revalidate` 与 `replay` 已出现。
2. `hs300-backfill` dry-run：使用本文件测试窗口，`--dry-run true`。
3. 真实 Tushare fetch / backfill：使用本文件测试窗口，`--dry-run false --enable-real-source`。
4. `normalize --dataset hs300_index --run-id run-hs300-real-qa-20260522`。
5. `validate --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --open-trade-dates 2024-01-02,2024-01-03,2024-01-04,2024-01-05`。
6. `read --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --columns trade_date,index_code,close --limit 10`。
7. `revalidate`：使用与第 5 条相同参数。
8. `replay --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522`。

## 预期结果

| 检查项 | 通过条件 |
|---|---|
| CLI 能力 | `--help` 包含 `revalidate` 和 `replay`。 |
| backfill dry-run | `ok=true`、`network_calls=0`、`writes=0`。 |
| 真实 backfill | 允许已有 success manifest 触发 `status=skipped`；若执行 fetch，则必须在小窗口内成功。 |
| normalize | `ok=true`，本 run 可生成或复用 canonical 输出。 |
| validate | `quality_status=pass`、`dataset_status=available`，coverage 为 4/4。 |
| read | 返回 4 个交易日样本，`index_code=399300.SZ`，`close` 非空且为正数。 |
| revalidate | 与 validate 同口径 PASS，且输出 `command=revalidate`、`network_calls=0`、`canonical_writes=0`。 |
| replay | 已有 success manifest 时返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`；缺失 manifest 时应写 FAIL/BLOCKED，不得伪造通过。 |

## 检查结果文件要求

写入 `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md`，必须包含：

1. Entry Criteria、Agent Dispatch Evidence、Checklist、Exit Criteria、Deliverables。
2. 每条命令的退出码和脱敏后的关键输出摘要。
3. 数据正确性结论：fetch/backfill、normalize、validate、read、revalidate、replay。
4. 若命令因网络、Tushare 权限、配额、凭据或 lake 权限失败，结论必须写成 `BLOCKED` 或 `FAIL`，并保留脱敏后的可复现命令摘要。
5. 不得记录 `.env` 内容、token、真实 lake root、NAS 路径或用户私有路径。

## 禁止范围

- 不得读取、打印、复制、写入 `.env` 内容。
- 不得在检查结果中出现 token、真实 lake root 绝对路径、NAS 路径或用户私有路径。
- 不得覆盖原始 FAIL 报告。
- 不得修改实现代码；若复验失败，写入 FAIL/BLOCKED 报告并说明复现口径。
