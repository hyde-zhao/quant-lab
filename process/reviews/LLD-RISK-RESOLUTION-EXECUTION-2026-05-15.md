---
artifact: "process/reviews/LLD-RISK-RESOLUTION-EXECUTION-2026-05-15.md"
owner: "meta-po"
status: "completed-confirmed-by-user"
created_at: "2026-05-15"
source_plan: "process/reviews/LLD-RISK-RESOLUTION-PLAN-2026-05-15.md"
source_review: "process/reviews/LLD-DETAIL-REVIEW-2026-05-15.md"
scope: "STORY-004..STORY-013 LLD risk remediation"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-15"
implementation_allowed: true
delivery_write_allowed: false
data_generation_allowed: false
---

# LLD 风险整改执行记录

> 本轮只修订 LLD、检查点、状态和评审闭环文档；未实现业务代码，未生成真实数据，未写 `delivery/**`，未生成或安装脚本。用户已于 2026-05-15 明确确认通过 `STORY-004` 至 `STORY-013` 批量 LLD / Story Package。

## 1. 组织分工

| 角色 | 本轮职责 | 执行方式 | 输出 |
|---|---|---|---|
| meta-se | 提供风险解决方案 | 读取 `LLD-RISK-RESOLUTION-PLAN-2026-05-15.md` 作为整改依据 | 不改文件 |
| meta-dev | 修订 LLD 设计契约 | 按 F-001 至 F-007 修改对应 Story LLD，保持实现门控关闭 | `process/stories/STORY-004..013-*-LLD.md` |
| meta-qa | 补测试、失败路径和门禁 | 为 schedule、会计、registry、日志、审计、RSI/MACD、CSV/Markdown 防护补测试项 | 各 LLD §9/§10/§11 |
| meta-po | 编排与闭环 | 聚合状态、检查点和整改执行记录；确认未推进到开发 | `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`、`process/STATE.md`、`process/STORY-STATUS.md` |

## 2. Findings 状态

| Finding | 处理文件 | 当前状态 | 剩余门禁 |
|---|---|---|---|
| F-001 | `STORY-005`、`STORY-006` | 关闭，用户已确认 | 按 Story DAG 进入 dev-ready 计算；会计恒等式测试必须在实现验证中覆盖 |
| F-002 | `STORY-006`、`STORY-007` | 关闭，用户已确认 | 2019-2025 schedule fixture 必须在实现验证中覆盖 |
| F-003 | `STORY-009`、`STORY-010`、`STORY-011` | 降级为 W3 实现前硬门禁 | `UNRESOLVED` source/interface 未替换为 exact 值前，W3 data_prep/normalizer/quality/loader 启用路径必须 fail fast |
| F-004 | `STORY-004` 至 `STORY-013` | 已补齐 LLD 契约 | 任一 STORY-004+ 实现时必须落地最小 CLI 诊断日志和测试 |
| F-005 | `STORY-012` | 关闭，用户已确认 | 实现时必须支持对象输入与 CSV/JSON sidecar 兼容路径 |
| F-006 | `STORY-013` | 关闭，用户已确认 | STORY-013 可在 STORY-008 verified 后与 W3 起点并行排队；实现时必须使用 LLD 固化公式和测试 |
| F-007 | `STORY-007`、`STORY-008`、`STORY-012` | 已补齐 LLD 契约 | 任一 CSV/Markdown writer 实现时必须调用 `sanitize_tabular_text` 或等价逻辑 |

## 3. 修改文件

| 文件 | 修改摘要 |
|---|---|
| `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | 增加最小 CLI 诊断日志契约、测试和实施任务。 |
| `process/stories/STORY-005-momentum-portfolio-engine-LLD.md` | 增加组合会计状态机、核心字段表、先卖后买、现金缩放、调仓幂等和会计恒等式测试；`open_items` 从 3 调整为 1。 |
| `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md` | 固化 `PortfolioResult` 字段消费，新增 `build_rebalance_schedule(...)`、schedule 边界规则和 2019-2025 schedule 测试；`open_items` 从 2 调整为 1。 |
| `process/stories/STORY-007-parameter-sweep-report-LLD.md` | 引用 STORY-006 schedule 口径，补 CLI 日志和 CSV 文本字段公式注入防护。 |
| `process/stories/STORY-008-candidate-report-jq-template-LLD.md` | 补 CLI 日志和候选/聚宽文本字段公式注入防护。 |
| `process/stories/STORY-009-pit-universe-provider-contract-LLD.md` | 补 `index_members` source/interface exact registry、`UNRESOLVED` fail fast 和 CLI 日志。 |
| `process/stories/STORY-010-trade-status-constraints-LLD.md` | 补 `trade_status` source/interface exact registry、`UNRESOLVED` fail fast 和 CLI 日志。 |
| `process/stories/STORY-011-limit-event-available-at-LLD.md` | 补 `prices_limit/events` source/interface exact registry、`UNRESOLVED` fail fast 和 CLI 日志。 |
| `process/stories/STORY-012-bias-audit-report-LLD.md` | 固化对象优先 + CSV/JSON sidecar 审计输入，定义 `AuditComparableRun`、参数组合 key、缺候选排序 warning 降级、表格文本防护和 CLI 日志；`open_items` 从 2 调整为 0。 |
| `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md` | 固化 RSI/MACD 公式、默认参数、warm-up、排序、tie-breaker、空目标 warning、非法参数测试和 CLI 日志；`open_items` 从 2 调整为 0。 |
| `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` | 增加风险整改执行摘要，更新 open items 与确认门控说明。 |
| `process/STORY-STATUS.md` | 刷新当前门控为风险整改后等待人工确认。 |
| `process/STATE.md` | 刷新 last_action、next_action、open items count、history 和批量 LLD 状态事实。 |

## 4. 剩余确认事项

| 类型 | 事项 |
|---|---|
| 人工确认 | 用户已于 2026-05-15 明确确认通过 STORY-004 至 STORY-013 批量 LLD / Story Package。 |
| 实现门禁 | STORY-004+ 可按 DAG 与文件所有权进入实现；仍不得生成真实生产数据、写 `delivery/**` 或安装脚本。 |
| W3 硬门禁 | STORY-009/010/011 的 `UNRESOLVED` source/interface 必须在 W3 实现前替换为 exact 值，否则相关入口 fail fast。 |

## 5. 轻量检查

| 检查项 | 状态 | 结果 |
|---|---|---|
| STORY-004 至 STORY-013 LLD frontmatter 已回写 `confirmed: true` | 通过 | 用户确认后已更新 frontmatter，记录 `confirmed_by=user` 与 `confirmed_at=2026-05-15` |
| F-001/F-002 当前状态为关闭、用户已确认 | 通过 | 检查点 §1.1 不再将二者列为待修阻塞项 |
| `STORY-010 -> STORY-011` 依赖仍存在 | 通过 | `STORY-011` LLD `depends_on` 保留 `STORY-010` Story 与 LLD；`DEVELOPMENT-PLAN.yaml` 仍含 `["STORY-010", "STORY-011"]` |
