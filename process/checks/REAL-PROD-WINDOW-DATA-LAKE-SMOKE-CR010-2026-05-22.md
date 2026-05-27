# REAL PROD WINDOW DATA LAKE SMOKE - CR010 - 2026-05-22

## Entry Criteria

| 条件 | 状态 | 说明 |
|---|---|---|
| 目标窗口已确认 | PASS | 本轮只验收 `2025-02-11..2026-02-18`，标记为 `limited_pit_window`。 |
| 真实执行授权已存在 | PASS | 已授权真实联网、读取本机 `.env`、真实 Tushare/JQData 抓取和外置 lake 写入；凭据值不得打印或写入文档。 |
| 旧 `data/**` 操作限制 | PASS | 本轮未读取、列出、迁移、复制、比对或删除旧 `data/**`。 |
| 统一 run 前缀 | PASS | 新增真实 run 使用 `cr010-prod-window-20250211-20260218-*` 前缀。 |

## Checklist

| 项 | 结果 | 证据 |
|---|---|---|
| JQData `index_members` | PASS | 已发布 `published/pass/available/pit_available`，run_id=`run-jqdata-index-members-smoke-20260522`。 |
| JQData `index_weights` | PASS | 已发布 `published/pass/available/pit_available`，run_id=`cr010-prod-window-20250211-20260218-index-weights-smoke-v2`；canonical `trade_date` 为查询快照日，provider 权重日期写入 `effective_date`。 |
| JQData `stock_basic` | PASS | 已发布 `published/pass/available/pit_available`，run_id=`cr010-prod-window-20250211-20260218-stock-basic-smoke-v3`；未来上市/退市事实未提前暴露。 |
| JQData `trade_status` | PASS | 已发布 `published/pass/available`，row_count=75,300，run_id=`cr010-prod-window-20250211-20260218-trade-status-jqdata`。 |
| JQData `prices_limit` | PASS | 已发布 `published/pass/available`，row_count=75,300，run_id=`cr010-prod-window-20250211-20260218-prices-limit-jqdata`。 |
| JQData `events` | PASS | 已发布 `published/pass/available`，row_count=0；空事件表只在 source/interface 与 `available_at_rule` 冻结时允许通过，run_id=`cr010-prod-window-20250211-20260218-events-jqdata`。 |
| Tushare `trade_calendar` | PASS | 已发布 `published/pass/available`，row_count=373，run_id=`cr010-prod-window-20250211-20260218-trade-calendar-tushare`。 |
| Tushare `hs300_index` | PASS | 已发布 `published/pass/available`，row_count=251，run_id=`cr010-prod-window-20250211-20260218-hs300-index-tushare`。 |
| Tushare `adj_factor` | PASS | 已发布 `published/pass/available`，row_count=74,957；使用 `trade_status` 可交易分母后 expected_rows=74,781、missing_rows=0、missing_rate=0.0。 |
| Tushare `prices` | PASS | 已发布 `published/pass/available`，row_count=74,781；使用 PIT universe 与 `trade_status` 可交易分母后 expected_rows=74,781、missing_rows=0、missing_rate=0.0。 |
| read / revalidate / replay | PASS | W3 与 P0 发布后均执行 read/revalidate/replay；revalidate/replay 保持 `network_calls=0`，replay 保持 `writes=0`、`auto_execute=false`。 |
| production readiness | PASS | `production_strict` status=`pass`，blockers=[]，allowed_claims=[`production_strict_research`]。 |
| exploratory readiness | PASS | `exploratory` status=`pass`，blockers=[]，allowed_claims=[`exploratory_analysis`, `fixture_regression`]。 |

## Exit Criteria

| 条件 | 状态 | 说明 |
|---|---|---|
| 目标数据集全部 published | PASS | readiness summary：dataset_count=10、published_count=10、missing_required_count=0、current_truth_complete=true。 |
| 已关闭旧 blocker | PASS | 不再出现 `index_weights` PIT incomplete、`stock_basic` non-PIT snapshot、W3 missing / required_missing 或 `prices` quality warn blocker。 |
| Claim 边界清晰 | PASS | 本轮允许 `production_strict_research`；`production_current_truth` 仍 blocked，因为本轮只覆盖账号权限内 limited window，不声明完整历史或持续生产真相。 |
| 敏感信息边界 | PASS | 记录只使用 run_id、相对路径语义和 `<configured-lake-root>`；未写入凭据、真实私有路径或旧 `data/**` proof。 |

## Deliverables

| 产物 | 状态 | 说明 |
|---|---|---|
| 代码 | DONE | JQData 多接口 adapter、W3 normalizer/validator/reader/catalog gate、PIT universe / trade_status denominator 验证逻辑已落地。 |
| 真实 lake 发布 | DONE | limited window 10 个目标数据集发布完成。 |
| 文档 | UPDATED | README、USER-MANUAL、CR-010 与 STATE 已从旧 blocker 结论更新为 limited window strict pass 结论。 |
| 后续限制 | OPEN | 完整历史 PIT universe、全市场长期覆盖和持续 production current truth 仍需账号权限或数据采购决策。 |
