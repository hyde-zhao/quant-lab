---
issue_id: "ISSUE-002"
title: "replay 子命令未复用 MARKET_DATA_LAKE_ROOT，导致真实复验命令合同失败"
category: "impl-bug"
severity: "BLOCKING"
status: "resolved"
created_at: "2026-05-22T08:00:33+08:00"
created_by: "issue-drafter"
source_run_exec: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md"
linked_change_request: "CR-009"
owner: "meta-dev"
routed_by: "meta-po"
routed_at: "2026-05-22T08:00:33+08:00"
route_decision: "fix-within-cr009"
resolved_at: "2026-05-22T08:12:50+08:00"
resolution: "fixed-and-real-replay-resmoke-pass"
resolution_evidence: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md"
---

# ISSUE: replay 子命令未复用 MARKET_DATA_LAKE_ROOT

## 问题描述

CR-009 真实 Tushare 小窗口复验中，`hs300-backfill`、`normalize`、`validate`、`read`、`revalidate` 均已通过，但 `replay` 按 handoff 指定命令执行时退出码为 2。CLI 报错缺少必填 `--lake-root`，导致无法验证已有 success manifest 时 `replay` 是否返回 `skipped` 且无网络 / 无写入。

## 观察到的实际结果

- 现象：`python -m market_data.cli replay ...` 未传 `--lake-root` 时直接由 argparse 拒绝。
- 影响对象：`market_data/cli.py` 的 `replay` 子命令、CR-009 真实复验闭环。
- 复现条件：使用 `uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli replay --dataset hs300_index --index-code 399300.SZ --start-date 2024-01-02 --end-date 2024-01-05 --run-id run-hs300-real-qa-20260522 --batch-id qa-real-20260522`。

## 期望结果

- 应有行为：`replay` 与 `validate` / `revalidate` / `read` 一样，在 `--lake-root` 未显式传入时可从 `MARKET_DATA_LAKE_ROOT` 解析 lake root。
- 验收依据：CR-009 handoff 指定的 `replay` 命令无需额外 `--lake-root` 参数即可执行；已有 success manifest 时输出 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。

## 证据

| 证据类型 | 位置 / 引用 | 说明 |
|---|---|---|
| RUN-EXEC | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | 第 8 条命令退出码 2，错误为缺少必填 `--lake-root`。 |
| 代码定位 | `market_data/cli.py` | `replay.add_argument("--lake-root", required=True)` 与其他命令的可选 lake root 解析口径不一致。 |
| 离线验证 | `process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md` | 离线 replay 测试显式传入 `--lake-root`，未覆盖 env fallback 合同。 |

## 初步根因分析

- 假设：`replay` 子命令 parser 仍把 `--lake-root` 设为 required，导致它不能走 `_resolve_lake_root(args)` 的环境变量 fallback。
- 支撑证据：真实复验第 8 条在 argparse 阶段失败；`validate`、`revalidate`、`read` 均未强制 `--lake-root` 并已在同一环境下通过。
- 待确认项：修复后需要补充离线测试覆盖 `MARKET_DATA_LAKE_ROOT` fallback，并重新执行真实小窗口 replay 复验。

## 受影响产物

| 文件 / 对象 | 影响说明 |
|---|---|
| `market_data/cli.py` | 需要调整 `replay` 子命令 `--lake-root` 参数合同。 |
| `tests/test_market_data_cli_comparison.py` | 需要补充未传 `--lake-root`、通过 env fallback 执行 replay 的回归用例。 |
| `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md` | 当前真实复验 FAIL 基线。 |

## 路由结论

| 项 | 结论 |
|---|---|
| 分类 | `impl-bug` |
| 严重度 | `BLOCKING`，阻断 CR-009 关闭，但不否定 validate/read/revalidate 已恢复。 |
| 责任角色 | `meta-dev` |
| 是否升级 CR | 不新建 CR；纳入既有 `CR-009` 修复闭环。 |
| 后续验证 | meta-dev 修复后由 meta-qa 执行离线回归和真实 replay 小窗口复验。 |

## 建议后续动作

1. 修改 `market_data/cli.py`，使 `replay --lake-root` 与 `validate` / `revalidate` 一致：参数可选，由 `_resolve_lake_root(args)` 支持 `MARKET_DATA_LAKE_ROOT` fallback。
2. 补充 `tests/test_market_data_cli_comparison.py` 覆盖 `replay` 未传 `--lake-root` 但设置 `MARKET_DATA_LAKE_ROOT` 的成功路径。
3. 执行最小回归：CR-009 定向测试、相关 runtime storage 测试、compileall。
4. 重新执行真实 `replay` 小窗口复验并写入新的结果文件，不覆盖本次 FAIL 结果。

## 处理结果

| 项 | 结论 |
|---|---|
| 解决状态 | `resolved` |
| 解决时间 | `2026-05-22T08:12:50+08:00` |
| 修复证据 | `process/checks/CP6-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-CODING-DONE.md` |
| 验证证据 | `process/checks/CP7-CR009-REPLAY-LAKE-ROOT-CONTRACT-FIX-VERIFICATION-DONE.md` |
| 真实复验证据 | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md` |
| 结论 | `replay` 未传 `--lake-root` 时已可通过运行时 `MARKET_DATA_LAKE_ROOT` 解析 lake root；真实 replay 返回 `status=skipped`、`attempts=0`、`network_calls=0`、`writes=0`。 |
