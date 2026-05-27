---
checkpoint_id: "CP5"
checkpoint_name: "CR014-S09 分时段真实抓取与 raw/manifest 写湖 LLD 人工确认"
type: "rolling_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-27T10:57:32+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-27T11:10:21+08:00"
auto_check_result: "process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md"
target:
  phase: "story-planning"
  change_id: "CR-014"
  batch_id: "CR014-REAL-RUN-BATCH-B"
  story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
  artifacts:
    - "process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md"
    - "process/stories/CR014-S09-windowed-real-fetch-lake-write-run-LLD.md"
    - "process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md"
---

# CP5 CR014-S09 LLD 人工确认

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md` | PASS | 0 | S09 LLD 已创建，14 节完整；用户已同意 CP5；`real_run_authorized=false` 继续保持，真实操作计数均为 0。 |

## Decision Brief

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`。理由：S09 LLD 已把真实抓取 / raw / manifest / run metadata 写湖拆成独立 BATCH-B，自动预检 PASS；approve 后只允许进入 S09 代码实现与 fake provider / tmp_path 验证，不会立即执行真实抓取或写湖。 |
| 备选方案 | `修改: <具体修改点>`：保留 S09 在 LLD review，按修改点调整窗口、dataset、授权字段或文件影响范围；`reject`：不批准 S09 实现，停留在 planned / LLD review，不进入代码实现或真实 run。 |
| 影响维度 | 用户价值：为“2026 年初至今数据测试”建立可审计的窗口、授权和 raw/manifest 写湖路径；实现复杂度：需要新增 `windowed_run` 合同层并复用 runtime / manifest / lake layout / CLI；可验证性：先 fake provider / tmp_path，再真实 smoke；维护成本：增加窗口、resume、rollback、permission counters；平台兼容：继续使用 uv、Parquet lake、manifest、catalog；安全 / 权限：approve 只放行实现，不放行真实 provider fetch / lake write / credential read / publish；交付影响：S09 实现完成后还需 CP6 / CP7 和 per-run authorization 才能拉 2026 YTD 真实数据。 |
| 优劣分析 | `approve` 的优势是可以立刻进入 S09 受控实现，代价是需要后续再次确认真实 run 授权字段。`修改:` 的优势是先收敛窗口或 dataset 细节，代价是延后实现。`reject` 的优势是完全避免真实数据链路风险，代价是无法推进 2026 YTD 数据测试。 |
| 风险与回退 | 主要风险是把 CP5 approve 误解为真实执行授权、把 raw/manifest 写入误解为 publish、或让 DuckDB / retention / old data 操作混入 S09。回退策略：CP5 未通过时回到 LLD；实现失败时回到 CP6 回修；真实 run 前字段缺失时 fail-closed，provider/lake/credential 计数为 0。 |
| 用户需决策事项 | 是否批准 S09 LLD 进入实现：回复 `approve`、`修改: <具体修改点>` 或 `reject`。本 CP5 不要求、也不接受最终真实 run 授权；真实 2026 YTD 数据测试仍需 S09 实现 CP6/CP7 后再提供 per-run `authorization_id` 和完整授权字段。 |

## CP5 Pilot Window Options

| 选项 | 推荐 | 接受影响 | 不接受影响 | 优点 | 缺点 |
|---|---|---|---|---|---|
| 2026 年初至最近已闭市交易日 `2026-01-01..2026-05-26` | 推荐 | 实现和后续真实 smoke 以 2026 YTD 为默认窗口；不包含尚未闭市的 2026-05-27 当天 | 需改用备选窗口，文档 / run spec 需同步 | 精准匹配“2026年第一天至今”的测试意图，范围小于一年，副作用更可控 | 只覆盖 2026 YTD，不能验证跨完整一年或自然年归档 |
| 最新完整一年 `2025-05-27..2026-05-26` | 备选 A | 覆盖最近完整一年行情和接口状态 | 真实副作用和 provider 调用范围更大 | 更接近完整一年压力测试 | 不符合用户最新“2026 年第一天至今”的缩小范围 |
| 一月 smoke `2026-04-27..2026-05-26` | 备选 B | 先以最小真实副作用验证 provider/schema/lake 写入路径 | 仍需后续再做一年窗口 | 风险和耗时最低，适合首次真实链路试跑 | 不能代表一年数据量和跨月/跨季缺口 |

## Future Per-Run Authorization Fields

这些字段不需要在本 CP5 中填完；它们在 S09 实现通过 CP6/CP7 后、真实拉取 2026 YTD 数据前必须逐项确认。缺任一字段时真实执行必须 fail-closed。

| 字段 | 推荐默认 | 备选 | 接受影响 | 不接受影响 |
|---|---|---|---|---|
| `authorization_id` | `CR014-S09-PILOT-YYYYMMDD-001` | 用户指定内部审批号 | run 可审计和撤销 | 不提供则 provider_fetch/lake_write/credential_read 均保持 0 |
| dataset 清单 | 先用 S09 实现支持的 P0 dataset 分批；真实前再按代码能力确认 | 只跑低风险 dataset，如 `trade_calendar` + `hs300_index`；或全 P0 | 2026 YTD 测试可覆盖目标链路 | 不确认 dataset 则无法真实执行 |
| date range | `2026-01-01..2026-05-26` | 最近完整一年或一月 smoke | 与 CP5 推荐窗口一致 | 不确认范围则无法真实执行 |
| source/interface allowlist | exact source/interface，以实现后的 plan 输出为准 | 只允许单一 provider/interface | 防止 provider/interface 漂移 | 不确认 allowlist 则无法真实执行 |
| lake root | 显式 `MARKET_DATA_LAKE_ROOT` 或显式路径 | 临时 smoke lake root | 防止写入旧 `data/**` | 不确认 lake root 则无法写湖 |
| window policy | `month` 或 provider-safe chunk | `quarter` / trading-day chunk | 分时段可恢复、可限速 | 不确认窗口策略则无法真实执行 |
| resume policy | `skip_success + retry_failed + conflict_fail_closed` | 全部重跑 / 全部跳过 | 防止重复抓取和覆盖成功窗口 | 不确认 resume 则失败恢复不可审计 |
| rollback policy | 默认只生成 rollback plan，不自动删除 | 用户额外授权归档/删除 | 防止误删 raw/manifest | 不确认 rollback 则只能 fail-closed 或保留 candidate |
| credential source policy | 只从环境变量读取，只记录 env var 名称，不记录值 | 用户指定凭据管理器 | 凭据不进入日志/文档/manifest | 不确认凭据策略则不能读凭据 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| S01..S08 已 verified | 通过 | `process/STORY-STATUS.md`、S01..S08 CP7 文件 | 用户已同意进入 S09 实现。 |
| S09 Story 已进入 LLD review | 通过 | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md` | 用户已同意。 |
| S09 LLD 已创建 | 通过 | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run-LLD.md` | 用户已同意。 |
| CP5 自动预检通过 | 通过 | `process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md` | 用户已同意。 |
| 真实执行仍关闭 | 通过 | Story / LLD / CP5 frontmatter | CP5 approve 只释放实现；`real_run_authorized=false`，真实操作计数为 0。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 S09 LLD 作为实现输入 | 通过 | S09 LLD 14 节 | 用户回复“同意”。 |
| 2 | 是否接受 approve 后只进入代码实现与 fake provider / tmp_path 验证，不执行真实 run | 通过 | Decision Brief、LLD §10 / §14 | 用户回复“同意”。 |
| 3 | 是否接受默认 pilot window 为 `2026-01-01..2026-05-26` | 通过 | CP5 Pilot Window Options | 用户已将窗口修改为 2026 年第一天至今并回复“同意”。 |
| 4 | 是否接受真实 run 授权字段后置到 S09 CP6/CP7 之后逐项确认 | 通过 | Future Per-Run Authorization Fields | 用户回复“同意”。 |
| 5 | 是否接受 S09 只写 raw / manifest / run metadata / run-scoped audit / failure-resume metadata | 通过 | LLD §1 / §5 / §8 | 用户回复“同意”。 |
| 6 | 是否接受 S09 不自动 normalize / validate / publish，不更新 current pointer | 通过 | LLD §7 / §13 | 用户回复“同意”。 |
| 7 | 是否接受 S09 不打开或写 DuckDB，不引入 DuckDB 依赖 | 通过 | LLD §8 / §9 | 用户回复“同意”。 |
| 8 | 是否接受缺授权字段时 fail-closed，provider/lake/credential 计数为 0 | 通过 | LLD §6 / §10 / CP5 自动预检 | 用户回复“同意”。 |
| 9 | 是否接受文件影响范围为 LLD 中列出的 6 个后续实现文件 | 通过 | LLD §4 / §11 | 用户回复“同意”。 |
| 10 | 是否确认 S09 可以进入实现 | 通过 | 本 Decision Brief | 用户回复“同意”。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户明确 approve / 修改 / reject | 通过 | 用户回复“同意” | 解释为 `approve`。 |
| 若 approve：S09 LLD confirmed，可释放 implementation_allowed=true | 通过 | 本人工确认 + CP5 自动预检 PASS | 允许进入实现。 |
| 若修改或 reject：回退目标明确 | N/A | 用户选择 approve | 无需回退。 |
| 真实 run 授权未被混入 CP5 | 通过 | 本文件和 LLD | CP5 不批准真实 run；真实执行仍需后续 per-run authorization。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| S09 Story | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md` | 通过 | 用户回复“同意”。 |
| S09 LLD | `process/stories/CR014-S09-windowed-real-fetch-lake-write-run-LLD.md` | 通过 | 用户回复“同意”。 |
| CP5 自动预检 | `process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md` | 通过 | 结论 PASS。 |
| CP5 人工确认稿 | `checkpoints/CP5-CR014-S09-REAL-RUN-BATCH-B-LLD-REVIEW.md` | 通过 | 本文件，已回填 approved。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-27T11:10:21+08:00
- 修改意见：无；默认 pilot window 为 `2026-01-01..2026-05-26`。
- 风险接受项：接受 CP5 approve 只释放 S09 实现和 fake provider / tmp_path 验证，不授权真实 provider fetch、lake write、credential read、publish、retention execute 或 DuckDB 写入。

请直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```
