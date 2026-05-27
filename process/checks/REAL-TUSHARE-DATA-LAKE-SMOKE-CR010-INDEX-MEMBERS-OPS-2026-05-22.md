---
check_id: "REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22"
workflow_id: "local_backtest"
change_id: "CR-010"
scope: "index-members-current-truth-and-ops-smoke"
executed_at: "2026-05-22T21:11:43+08:00"
result: "PARTIAL_WITH_OPS_PASS"
lake_root: "<configured-lake-root>"
backup_root: "<configured-backup-root>"
restore_root: "<configured-restore-root>"
old_data_comparison: "deferred"
---

# CR-010 index_members current truth 与 backup/restore smoke 结果

## Entry Criteria

| 准则 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 用户已授权真实联网、真实 Tushare 抓取、真实写 lake 和读取 `.env` | PASS | `process/STATE.md` CR-010 授权记录 | 本轮只记录 root label，不记录真实路径或凭据值。 |
| 旧 `data/**` 对比继续暂缓 | PASS | 用户授权记录为 deferred | 本轮未读取、列出、迁移、复制、比对或删除旧 `data/**`。 |
| `index_members` 不允许由 `index_weights`、`stock_basic` 或 `security_master` 替代 | PASS | CR-010 计划约束；本文件 Checklist | 本轮只做真实接口探测和失败候选记录，不发布替代数据。 |
| backup/restore smoke 只针对已发布 release/run | PASS | scope：`dataset=prices`，`run_id=cr010-main-smoke-20260522T161025-prices-adj` | 该 run 在 catalog coverage 中为 published current truth。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | 复核 Tushare `index_member` 小窗口 0 行原因 | PASS | `index_member` 对 `399300.SZ` / `000300.SH`，无日期、2024-01 窗口、`is_new=Y/N` 和 2024 全年组合均返回 0 行；字段为 `index_code, con_code, in_date, out_date, is_new` | 当前真实接口可调用但不返回 HS300 成分，不能发布为 current truth。 |
| 2 | 确认不使用 `index_weights` 替代 `index_members` | PASS | 同轮探测中 `index_weight` 对 `399300.SZ` / `000300.SH` 的 2024-01 窗口均返回 600 行 | `index_weight` 仍只作为权重数据，不生成或发布 `index_members`。 |
| 3 | 扩大窗口真实 smoke | PASS | `tushare-first-acquire index_members` 2024-01-01..2024-01-31：`network_calls=1`、raw 写入成功；normalize `row_count=0`；validate `quality_status=fail`、`dataset_status=required_missing`、`coverage_ratio=0.0` | 只保留 candidate_unpublished 失败证据，不执行 publish。 |
| 4 | P0 current truth 复检 | FAIL | coverage：7 个 P0 dataset 中 6 个 published，`index_members` 为 `candidate_unpublished` / `quality_status=fail` / `readiness_status=pit_incomplete` | `current_truth_complete=false`。 |
| 5 | `production_strict` 复检 | FAIL | `report-readiness --realism-mode production_strict` 返回 `status=fail` | 阻断包含 `index_members`、`index_weights` PIT、`prices/stock_basic` warn，以及 W3 `trade_status/prices_limit/events` missing。 |
| 6 | W3 fail-fast 语义 | PASS | `trade_status`、`prices_limit`、`events` 在 readiness 中保持 missing / required_missing 阻断；`events_available_at_missing` 存在 | 未伪造 W3 source/interface 或 `available_at`。 |
| 7 | backup plan/run/verify/report | PASS | release `cr010-ops-smoke-20260522`，file_count=4，bytes=78,772；backup run 首次 `copied=4`，二次 `skip=4`，verify `same=4`，report `computed=4` | 报告仅含 root label、相对路径、file count、bytes、checksum 状态。 |
| 8 | restore plan/drill | PASS | restore plan `would_restore=4`；restore-drill `read.status=available`、`revalidate.status=pass`、`replay.network_calls=0`、`auto_execute=false` | drill 使用临时 restore root，不覆盖 hot lake。 |
| 9 | restore root 持久 smoke | PASS | restore-run 到 configured restore root：`restored=4`；read `row_count=3`；revalidate `network_calls=0`；replay `network_calls=0`、`writes=0`、`status=ready_for_offline_replay` | 恢复副本可读，replay 不联网。 |
| 10 | restore root collision fail-fast | PASS | 将 `restore-root` 指向 lake root 时，restore-plan 返回 `restore_root_conflict` | 未执行恢复或覆盖。 |

## Current Truth Snapshot

| Dataset | publish_status | quality_status | readiness_status | pit_status | 说明 |
|---|---|---|---|---|---|
| `prices` | published | warn | available | non_pit_disclosed | 小窗口可读；仍需披露 non-PIT universe limitation。 |
| `adj_factor` | published | pass | available | not_applicable | 小窗口 current truth。 |
| `hs300_index` | published | pass | available | non_pit_disclosed | 小窗口 current truth。 |
| `trade_calendar` | published | pass | available | not_applicable | 小窗口 current truth。 |
| `index_members` | candidate_unpublished | fail | pit_incomplete | pit_incomplete | Tushare `index_member` 当前对 HS300 探测为 0 行，未发布。 |
| `index_weights` | published | warn | pit_incomplete | pit_incomplete | 不替代 `index_members`。 |
| `stock_basic` | published | warn | non_pit_snapshot | non_pit_snapshot | 只作基础证券快照，不提供 PIT universe。 |

## Command Evidence

| 命令类别 | 状态 | 摘要 |
|---|---|---|
| Tushare 只读接口探测 | PASS | `index_member` 相关组合均 rows=0；`index_weight` 相关组合 rows=600，但未替代。 |
| `tushare-first-acquire index_members` | PASS | 2024-01 窗口真实 fetch 成功，`network_calls=1`。 |
| `normalize index_members` | PASS | `row_count=0`。 |
| `validate index_members` | FAIL_EXPECTED | `quality_status=fail`、`dataset_status=required_missing`、`coverage_ratio=0.0`。 |
| `report-readiness production_strict` | FAIL_EXPECTED | `status=fail`；remaining blockers 已列入 Checklist。 |
| `report-readiness exploratory` | WARN_EXPECTED | `status=warn`；allowed claims 仅 `exploratory_analysis`、`fixture_regression`。 |
| `backup-plan/run/verify/report` | PASS | file_count=4，bytes=78,772，checksum same/skip/report 行为符合预期。 |
| `restore-plan/drill/run/read/revalidate/replay` | PASS | restore drill 与 restore root smoke 均通过；replay `network_calls=0`。 |
| `restore-root == lake-root` | PASS | 返回 `restore_root_conflict`。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 真实 `index_members` current truth 可发布 | FAIL | validate 结果 `quality_status=fail`，catalog candidate_unpublished | 当前不能关闭 `index_members` 缺口。 |
| `current_truth_complete=true` | FAIL | P0 6/7 published；`index_members` 未发布 | CR-010 保持 open。 |
| `production_strict` 可放行 | FAIL | `production_strict.status=fail` | `index_members`、PIT、quality warn 与 W3 仍阻断。 |
| W3 缺口 fail-fast | PASS | W3 dataset missing / required_missing | 未伪造 available。 |
| backup/restore 运维 smoke | PASS | release `cr010-ops-smoke-20260522` | 备份、校验、报告、恢复、drill、read、revalidate、replay 均完成。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| index_members 与 ops smoke 记录 | `process/checks/REAL-TUSHARE-DATA-LAKE-SMOKE-CR010-INDEX-MEMBERS-OPS-2026-05-22.md` | DONE | 本文件。 |
| catalog candidate 失败证据 | configured lake `catalog` | DONE | `index_members` 保持 candidate_unpublished，不发布。 |
| backup release | configured backup root | DONE | `cr010-ops-smoke-20260522`。 |
| restore smoke 副本 | configured restore root | DONE | 仅用于恢复验证，不覆盖 hot lake。 |

## 结论

结论：`PARTIAL_WITH_OPS_PASS`。

`index_members` 当前仍不能作为真实 current truth 发布；Tushare `index_member` 可调用但对本轮 HS300 探测返回 0 行，`index_weight` 有数据但按 CR-010 约束不得替代 `index_members`。因此 `current_truth_complete=false`，`production_strict=fail`，CR-010 继续保持 open。

backup/restore 运维 smoke 已通过：同一已发布 `prices` run 的 backup plan/run/verify/report、restore plan/drill/run/read/revalidate/replay 均完成，报告脱敏，restore collision fail-fast 生效，replay `network_calls=0`。
