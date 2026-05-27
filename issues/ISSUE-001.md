---
issue_id: "ISSUE-001"
title: "真实 hs300_index 烟测 validate/read 被 duplicate_key 与 quality_failed 阻断"
category: "impl-bug"
severity: "HIGH"
status: "resolved"
created_at: "2026-05-22T07:08:25+08:00"
created_by: "meta-po"
source_run_exec: "process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md"
linked_change_request: "CR-009"
resolved_at: "2026-05-22T08:12:50+08:00"
resolution: "fixed-and-real-smoke-pass"
resolution_evidence: "process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md"
---

# ISSUE: 真实 hs300_index 烟测 validate/read 被 duplicate_key 与 quality_failed 阻断

## 问题描述

真实 Tushare 运行态烟测中，`hs300-backfill` 与 `normalize` 已成功完成，但 `validate` 输出 `quality_status=fail`、`dataset_status=duplicate_key`，导致后续 `read` 被 `quality_failed` 阻断。同期 CLI 顶层命令缺少 `revalidate` 与 `replay`，无法以正式命令复验质量或验证已成功批次的无联网重放语义。

## 观察到的实际结果

- 现象：`validate` 返回质量失败，`read` 退出码 3 并报告 `dataset=hs300_index 不可读: quality_failed`。
- 影响对象：`hs300_index` 真实 benchmark 数据链路、catalog 质量门、read 抽样验收，以及真实运行态 QA 烟测闭环。
- 复现条件：对 `run-hs300-real-qa-20260522` 的 `hs300_index` 小窗口执行 normalize 后，再执行 validate/read。

## 期望结果

- 应有行为：指定 `--run-id` 复验时只校验该运行批次对应 canonical parquet，不被历史 run 的同键数据误判为重复；质量 PASS 后 `read` 可返回本 run 对应样本。
- 验收依据：`process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` 的失败项关闭；新增离线回归覆盖同日期多 run 场景、`revalidate` 子命令和 `replay` 无联网/无写入能力。

## 证据

| 证据类型 | 位置 / 引用 | 说明 |
|---|---|---|
| QA 烟测报告 | `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | 记录 validate duplicate_key、read quality_failed、revalidate/replay unsupported。 |
| handoff | `process/handoffs/META-QA-REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | 记录真实 `spawn_agent` QA 执行证据。 |

## 初步根因分析

- 假设：`validate --dataset hs300_index` 当前按 dataset 根目录读取所有 canonical parquet，没有按 `--run-id` 收敛输入；当历史 run 与本次 run 覆盖相同 `trade_date,index_code` 时，会跨 run 误判重复键。
- 支撑证据：`market_data/cli.py` 中 `_cmd_validate_hs300_index` 使用 `layout.canonical_dataset_root(args.dataset).rglob("*.parquet")`，未使用 `args.run_id` 过滤；`normalize` 本身已对单批次 `trade_date,index_code` 做 fail fast。
- 待确认项：通过离线 fixture 构造两个不同 run、相同日期的 `hs300_index` canonical 文件，验证 `--run-id` 过滤后质量 PASS。

## 受影响产物

| 文件 / 对象 | 影响说明 |
|---|---|
| `market_data/cli.py` | 需要为 validate/revalidate 增加 run_id 级 canonical 输入过滤，并补齐 replay 子命令。 |
| `tests/test_market_data_cli_comparison.py` 或 CR007 相关 CLI 测试 | 需要覆盖多 run 去重误判、revalidate、replay。 |
| `process/checks/REAL-TUSHARE-RUNTIME-SMOKE-2026-05-22.md` | 作为失败基线，修复后需追加新的复验结果文件，不直接覆盖原报告。 |

## 建议后续动作

1. 创建 `CR-009`，按运行态缺陷修复处理，不授权读取或打印 `.env` / token / 私有路径。
2. 由 `meta-dev` 实施最小代码修复并写入 CP6。
3. 由 `meta-qa` 执行离线回归；如用户后续授权，再执行真实 Tushare 小窗口复验并写入新的 QA 检查结果。

## 处理结果

| 项 | 结论 |
|---|---|
| 解决状态 | `resolved` |
| 解决时间 | `2026-05-22T08:12:50+08:00` |
| 修复证据 | `process/checks/CP6-CR009-RUNTIME-SMOKE-REMEDIATION-CODING-DONE.md`、`process/checks/CP7-CR009-RUNTIME-SMOKE-REMEDIATION-VERIFICATION-DONE.md` |
| 真实复验证据 | `process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-2026-05-22.md`、`process/checks/REAL-TUSHARE-RUNTIME-RESMOKE-CR009-REPLAY-FIX-2026-05-22.md` |
| 结论 | `validate` / `read` / `revalidate` 已真实小窗口 PASS；后续发现的 `replay --lake-root` 合同缺口已作为 `ISSUE-002` 修复并真实复验 PASS。 |
