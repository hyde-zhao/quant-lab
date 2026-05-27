---
artifact: "CR-005 hs300_index missing benchmark + Tushare data-layer remediation review summary"
round: 3
status: final
decision: revise
blocking_count: 10
required_count: 9
optional_count: 4
created_at: "2026-05-17T18:33:09+08:00"
owner: "meta-po"
change_id: "CR-005"
governance_mode: "review-gated"
---

# Review Summary

## 1. 输入清单

- findings_files:
  - `process/checks/REVIEW-CR005-HS300-TUSHARE-META-PM.md`
  - `process/checks/REVIEW-CR005-HS300-TUSHARE-META-SE.md`
  - `process/checks/REVIEW-CR005-HS300-TUSHARE-META-DEV.md`
  - `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA.md`

## 2. 严重度汇总

| Severity | Count | Owner |
|----------|-------|-------|
| 严重 | 10 | `meta-pm` / `meta-se` / `meta-dev` / `meta-qa` |
| 一般 | 9 | `meta-pm` / `meta-se` / `meta-dev` / `meta-qa` |
| 轻微 | 4 | `meta-pm` / `meta-se` / `meta-dev` |

补充观察项：`meta-pm` 与 `meta-dev` 各有 1 项 observation，均不单独阻断，但支持当前修订决策。

## 3. 决策

- decision: `revise`
- rationale: 第三轮四条评审 lane 均认为当前 CR-005 大方向正确，但不能继续沿用第二轮 CP3/CP4 pending 人工稿直接请求用户批准。阻断点集中在需求基线未吸收 CR-005、`hs300_index required_missing` 到 Tushare 数据层 backfill 的两步契约未机器化、`BenchmarkResult` / structured status 未冻结、`hs300_index` 数据准确性 quality gate 不足，以及 CP5 前测试清单缺 hs300 专项覆盖。
- next_checkpoint: `CP3/CP4 re-run after revision`

当前门控结论：

- CP3：`changes_requested`，现有 `checkpoints/CP3-CR005-HLD-REVIEW.md` 应标记为 `superseded-awaiting-revision`。
- CP4：`changes_requested`，现有 `checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md` 应标记为 `superseded-awaiting-revision`。
- CP5：`blocked-before-cp5`。不得进入 LLD 批次确认、不得实现代码、不得新增依赖、不得写真实数据或 token。

## 4. 后续动作

1. 路由 `meta-pm` 修订 `process/USE-CASES.md`、`process/REQUIREMENTS.md` 与 CR-005 文档处理决策，补齐 `hs300_index`、Tushare 写湖补齐、structured `unavailable/required_missing`、Backtrader optional backend 和数据准确性 / 可用性需求追溯。
2. 路由 `meta-se` 修订 CR-005、HLD §22、ADR-015 / ADR-017、Story Backlog、Development Plan、CR005-S01/S02/S03/S04/S05/S06 相关 `dev_gate` 和 CP3/CP4 审查稿输入，明确两步契约：消费层只返回 typed status + remediation/backfill spec；数据层仅在用户显式执行 `market_data` Tushare fetch/backfill job 时联网写湖。
3. 修订必须补齐 `BenchmarkResult` typed schema、`next_action` / `remediation_job_spec`、`hs300_index` backfill job spec、source registry / CLI/job 所有权、quality gate、accuracy AC、trade calendar coverage denominator、manifest / idempotency / resume、Backtrader unavailable 行为和 CP5 前测试清单。
4. 修订完成后由 `meta-po` 重跑 CP3/CP4 自动预检并重新生成人工审查稿；只有 CP3/CP4 人工确认通过后，才允许组织 CR-005 CP5 LLD 批次设计。

## 聚合 Findings

| 来源 | 结论 | 阻断 / 必改摘要 | 处理路由 |
|---|---|---|---|
| `meta-pm` | `revise-and-resubmit` | `USE-CASES.md` / `REQUIREMENTS.md` 未增量吸收 CR-005；缺 `hs300_index` next action、数据准确性 AC、market_data 写湖术语澄清。 | `meta-pm` 主责；`meta-se` 消费需求变更。 |
| `meta-se` | `changes_requested` | `required_missing` 未映射为显式 Tushare `hs300_index` fetch/backfill job spec；available 路径准确性契约不足；CR005-S04/S06 dev_gate 不足。 | `meta-se` 主责；必要时 `meta-qa` 复核。 |
| `meta-dev` | `do-not-enter-CP5` | 缺 `hs300_index` backfill CLI/job/source registry 契约；Data Loader / benchmark resolver structured result 未冻结；缺 raw->canonical mapping、coverage、manifest/resume。 | `meta-se` 方案修订；后续 CP5 前再交 `meta-dev`。 |
| `meta-qa` | `BLOCKED before CP5` | `unavailable/required_missing` payload 缺可操作 next_action；缺 Tushare fetch/backfill 验收链；缺 hs300 quality gate；旧路径回退需排除 proxy；缺 CP5 前 hs300 测试清单。 | `meta-se` + `meta-qa` 质量门修订。 |

## 必须保持的边界

- 消费层缺 `hs300_index` 时只返回 structured `unavailable` / `required_missing`，可携带 `next_action` 或 `remediation_job_spec`，但不得自动执行 fetch/backfill。
- 只有用户显式执行 `market_data` 写湖 / 数据准备层的 Tushare fetch/backfill job，才允许联网并写入 raw / manifest / canonical / quality / catalog / gold。
- `engine/data_loader.py`、实验入口、benchmark resolver、Backtrader adapter 都属于 read-only consumer，不得导入 connector/runtime/storage，不得读取 `TUSHARE_TOKEN`，不得静默代理为 hs300。
- 旧等权买入持有或同股票池代理如保留，只能命名为 `proxy_baseline`，不得填充 `hs300_index` benchmark 字段或声明为 hs300 相对收益。
