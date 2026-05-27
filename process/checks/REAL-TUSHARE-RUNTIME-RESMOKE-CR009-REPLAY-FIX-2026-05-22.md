---
check_id: "REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22"
workflow_id: "local_backtest"
change_id: "CR-009"
issue_id: "ISSUE-002"
scope: "real-replay-resmoke"
dataset: "hs300_index"
index_code: "399300.SZ"
start_date: "2024-01-02"
end_date: "2024-01-05"
run_id: "run-hs300-real-qa-20260522"
batch_id: "qa-real-20260522"
executed_at: "2026-05-22T08:09:37+08:00"
result: "PASS"
---

# CR-009 replay lake-root 合同修复真实复验结果

## Entry Criteria

| 准则 | 状态 | 证据 | 说明 |
|---|---|---|---|
| QA handoff 已读取 | PASS | `process/handoffs/META-QA-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFY-2026-05-22.md` | 指定复验目标为 `ISSUE-002` 的 replay lake-root 合同修复。 |
| 用户已授权真实复验 | PASS | handoff `authorization_text=授权真实复验` | 本轮允许使用 `uv run --env-file .env` 由运行时加载凭据。 |
| 复验范围未扩大 | PASS | Executed Command | 只执行 handoff 指定的 `replay` 小窗口命令；未执行新的 fetch/backfill。 |
| 不额外添加 `--lake-root` | PASS | Executed Command | 命令未传 `--lake-root`，用于验证 `MARKET_DATA_LAKE_ROOT` fallback 合同。 |
| 安全边界可执行 | PASS | 执行过程 + 本报告 | 未读取、打印、复制或写入 `.env` 内容；报告未记录 token、真实 lake root 绝对路径、NAS 路径或用户私有路径。 |

## Agent Dispatch Evidence

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `spawn_agent` |
| agent_id | `019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7` |
| thread_id | `019e4d02-d57a-7bc1-a4d9-a54c21d3b3e7` |
| agent_name | `qa-hua` |
| handoff | `process/handoffs/META-QA-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFY-2026-05-22.md` |
| spawned_at | `2026-05-22T08:08:16+08:00` |
| completed_at | `2026-05-22T08:09:37+08:00` |
| note | meta-po 已回填 handoff、STATE 和 CR。 |

## Executed Command

执行命令如下。命令使用统一前缀，未追加 `--lake-root`，未读取或打印 `.env` 内容。

```bash
UV_CACHE_DIR=/tmp/uv-cache-local-backtest uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli replay --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522
```

| 项 | 值 |
|---|---|
| 退出码 | `0` |
| stdout 脱敏摘要 | `ok=true`、`command=replay`、`dataset=hs300_index`、`source=tushare`、`interface=hs300_index.daily`、`run_id=run-hs300-real-qa-20260522`、`batch_id=qa-real-20260522`、`status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`、`raw_path=raw/tushare/hs300_index.daily/20240102/qa-real-20260522.jsonl` |
| stderr 脱敏摘要 | 空 |

## Data Correctness

| 判断项 | 结论 | 说明 |
|---|---|---|
| replay 命令是否被 argparse 接受 | PASS | 未传 `--lake-root` 时退出码为 0，不再出现“缺少必填 `--lake-root`”错误。 |
| 是否命中已有 success manifest 的 replay 路径 | PASS | 输出 `status=skipped`。 |
| attempts 是否为 0 | PASS | 输出 `attempts=0`。 |
| network_calls 是否为 0 | PASS | 输出 `network_calls=0`，未触发真实网络调用。 |
| writes 是否为 0 | PASS | 输出 `writes=0`，未写入新的真实数据文件。 |
| replay 范围是否保持小窗口 | PASS | dataset=`hs300_index`，index_code=`399300.SZ`，日期范围为 `2024-01-02` 到 `2024-01-05`，run/batch 与 handoff 一致。 |
| 输出是否安全脱敏 | PASS | 本报告未包含 token、真实 lake root 绝对路径、NAS 路径或用户私有路径；仅记录相对 raw path。 |

## Exit Criteria

| 准则 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 真实 replay 退出码为 0 | PASS | Executed Command | 命令成功完成。 |
| replay 输出 `status=skipped` | PASS | stdout 脱敏摘要 | 已存在 success manifest 时安全跳过。 |
| replay 输出 `attempts=0` | PASS | stdout 脱敏摘要 | 未尝试真实 source。 |
| replay 输出 `network_calls=0` | PASS | stdout 脱敏摘要 | 零网络调用。 |
| replay 输出 `writes=0` | PASS | stdout 脱敏摘要 | 零写入。 |
| 不扩大真实范围 | PASS | Executed Command | 未执行新的 fetch/backfill，未追加非授权参数。 |
| 安全边界满足 | PASS | 本报告 | 未泄露凭据、真实 lake root 或私有路径。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| 真实 replay 修复复验报告 | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md` | PASS | 本文件。 |
| CP7 验证完成检查结果 | `process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md` | PASS | 记录离线回归与真实 replay 总体验证结论。 |
| 原始真实复验 FAIL 报告 | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | PRESERVED | 未覆盖、未修改。 |

## Conclusion

**结论：PASS**

CR-009 / ISSUE-002 的 replay lake-root 合同修复已通过真实小窗口复验。`replay` 在未显式传入 `--lake-root` 的情况下可通过运行时环境解析 lake root，并在已有 success manifest 时返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。本轮未执行新的 fetch/backfill，未读取或打印 `.env`，未记录 token、真实 lake root 绝对路径、NAS 路径或用户私有路径。
