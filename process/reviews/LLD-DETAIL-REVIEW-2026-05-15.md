---
artifact: "process/reviews/LLD-DETAIL-REVIEW-2026-05-15.md"
reviewer: "codex-lld-detail-reviewer"
lane: "lane-implementation"
round: 1
status: draft
governance_mode: review-gated
---

# Review Findings

## 1. 审查范围

- 目标对象：`process/stories/STORY-004-*-LLD.md` 至 `process/stories/STORY-013-*-LLD.md`
- 审查目标：低层设计完整性、Story 间契约一致性、用户补齐点回归检查、批量门控进入确认前风险识别
- 审查依据：用户指定 14 项 LLD 评审维度、`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`、`.agents/skills/review-artifact-protocol/templates/REVIEW-FINDINGS-TEMPLATE.md`

## 2. Findings

<!-- findings-table -->

| ID | 严重度 | 影响 Story | 维度 | 文件路径与行号 | 问题描述 | 影响 | 建议修复 |
|----|--------|------------|------|----------------|----------|------|----------|
| F-001 | REQUIRED | STORY-005，传导至 STORY-006/007/008 | 3 数据结构，5 算法逻辑，6 并发/重复执行，14 代码影响范围 | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md:87`、`:90`、`:100`、`:111`、`:134` | 组合会计仍停留在“等权目标、成本扣除、现金和持仓更新”的描述层，未定义持仓数量/权重/市值字段、是否允许小数股或整手、卖出与买入顺序、现金不足时买入缩放、同一调仓日重复执行的幂等口径、会计恒等式。 | W1 的 `PortfolioResult.nav/positions/trades/costs` 是 STORY-006 指标和 STORY-007 扫描的强输入；如果实现者自行解释，会造成换手、现金、成本和净值不一致，后续候选排序不可复现。 | 在 STORY-005 LLD 中补充 `PortfolioState`、`PositionRecord`、`TradeRecord`、`CostRecord` 字段表；明确先卖后买、目标金额计算、小数股/整手策略、现金约束缩放、调仓日唯一键或重复执行策略；增加会计恒等式测试，例如 `cash + positions_market_value - costs == nav` 的允许误差。 |
| F-002 | REQUIRED | STORY-006，传导至 STORY-007/008 | 4 业务流程，5 算法逻辑，12 单元测试点 | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md:112`、`:137`、`:168`；对照 `process/HLD.md:453`、`:456`、`:459` | LLD 只写“按 `rebalance_freq` 生成调仓日”，没有把 HLD 中“第 `rebalance_freq` 个交易日触发信号、T+1 或之后成交、无 T+1 价格处理”的口径落成可执行算法。缺少首个可交易信号日、lookback warm-up、最后一个交易日无 T+1、2019-2025 起止覆盖与调仓日关系的明确定义。 | 不同实现会生成不同调仓日集合，导致 60 组扫描结果、失败行和候选选择不稳定；`T-BACKTEST-2019-2025-01` 只有覆盖验收，但不足以锁定调度算法。 | 在 STORY-006 LLD 中补充 `build_rebalance_schedule(calendar, lookback_days, rebalance_freq, start_date, end_date)` 或等价接口；明确从满足 lookback 的首个信号日开始、按开市日计数、最后无 T+1 时失败还是跳过并记录；新增 schedule 单元测试覆盖边界日期和 2019-2025 fixture。 |
| F-003 | REQUIRED | STORY-009/010/011 | 2 接口定义，3 数据结构，5 算法逻辑，13 兼容和迁移 | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md:142`、`:145`、`:195`；`process/stories/STORY-010-trade-status-constraints-LLD.md:149`、`:205`；`process/stories/STORY-011-limit-event-available-at-LLD.md:149`、`:203` | 三个增强 Story 已补入 raw/manifest/normalizer/quality/loader 同步契约，但 `source/interface` 仍以 OPEN 形式留到实现前确认；同时 LLD 又要求 normalizer exact dataset/interface 映射。缺少正式枚举、临时占位值或“未知接口 fail fast”的注册机制。 | exact 匹配是项目规则。没有可执行的 source/interface registry 时，实现阶段容易出现字符串猜测、模糊匹配或各模块字段名不一致，破坏 raw -> manifest -> normalizer -> quality -> loader 的同步契约。 | 在 W3 LLD 中补一张共享字段注册表：`target_dataset`、允许的 `source`、允许的 `interface`、覆盖字段、raw metadata 必填项、manifest 必填项、normalizer 函数；如果数据源未定，明确使用 `interface=UNRESOLVED` 时 data_prep/normalizer 必须 fail fast，且实现前关闭 OPEN。 |
| F-004 | REQUIRED | STORY-004 至 STORY-013 | 9 日志设计，10 监控指标 | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md:272`、`process/stories/STORY-007-parameter-sweep-report-LLD.md:140`、`process/stories/STORY-010-trade-status-constraints-LLD.md:152`、`process/stories/STORY-012-bias-audit-report-LLD.md:130` | 各 LLD 的安全与性能章节覆盖无网络、只读、耗时或质量字段，但没有任何日志设计：日志级别、事件名、run_id/manifest_run_id/参数摘要、错误脱敏、是否输出到 CLI stderr 或返回对象均未定义。监控对本地 CLI 可标为 NA，但至少需要运行级诊断日志契约。 | 本项目强调可追溯和可调试。缺少日志契约会让数据合同失败、单组扫描失败、候选选择、增强约束拒绝等问题只能依赖异常文本或 CSV 行定位，后续 QA 与用户排错成本上升。 | 补充最小日志规范：本地 CLI 不接入服务监控，监控维度标 NA；每个入口记录 `INFO start/end`、`WARNING degraded/warn quality`、`ERROR structured_error`，包含 `run_id` 或 `manifest_run_id`、Story 模块名、参数摘要和相对路径，禁止记录凭据或绝对隐私路径。 |
| F-005 | REQUIRED | STORY-012 | 2 接口定义，3 数据结构，13 兼容和迁移，14 代码影响范围 | `process/stories/STORY-012-bias-audit-report-LLD.md:76`、`:90`、`:93`、`:120`、`:173`、`:174` | 偏差审计要求比较 baseline/enhanced 和候选排序，但输入契约仍未落定：baseline/enhanced 是内存对象、CSV、JSON sidecar 还是候选报告派生视图仍为 OPEN；关键字段、缺失候选排序时的降级输出 schema、报告文件之间的关联键也未具体化。 | STORY-012 是 W3 真实性增强的收口报告。输入未定会导致审计实现时回头改 STORY-006/007/008/010/011 的报告 schema，扩大文件影响范围。 | 在 STORY-012 LLD 中明确首选输入格式和最小字段集，例如 `BacktestResult` dict + candidate CSV/JSON sidecar；定义参数组合 key、baseline/enhanced run_id、候选 rank 字段、缺候选排序时的 warning 字段；关闭或前置 O-01/O-02。 |
| F-006 | ADVISORY | STORY-013 | 5 算法逻辑，8 配置项，12 单元测试点 | `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md:122`、`:123`、`:142`、`:144`、`:173` | RSI/MACD 仍以“默认参数可设”和“按低位反转/金叉信号排序”的示例语言描述，没有锁定 RSI 计算公式、EMA adjust 口径、warm-up 处理、排序字段、tie-breaker、空目标策略。 | STORY-013 为 P2，不阻塞 W1/W2 主路径，但如果进入实现，会因策略公式解释差异导致示例结果不可复现。 | 将 RSI/MACD 算法从示例语言改成确定性公式；默认参数从 OPEN 或检查点默认建议回写到 LLD；为 warm-up、缺失价格、tie-breaker 和非法参数增加测试。 |
| F-007 | ADVISORY | STORY-007/008/012 | 11 安全细节，7 错误处理 | `process/stories/STORY-007-parameter-sweep-report-LLD.md:47`、`:103`；`process/stories/STORY-008-candidate-report-jq-template-LLD.md:77`、`:84`、`:95`；`process/stories/STORY-012-bias-audit-report-LLD.md:94` | 多个 CSV 输出包含 `error_message`、`selection_reason`、`jq_notes`、`jq_difference_reason` 等用户或异常派生字符串，但未说明 CSV/表格公式注入防护。 | 用户可能用表格软件打开报告，若字符串以 `=`, `+`, `-`, `@` 开头，存在误执行公式或误导展示风险。 | 在 CSV writer 设计中加入简单转义策略：对文本字段首字符为 `=+-@` 时前置单引号或空格，并在测试中覆盖。 |

## 3. 汇总结论

- blocking_count: 0
- required_count: 5
- optional_count: 2
- recommended_next_action: `revise-and-resubmit / conditional-proceed`

## 4. 待确认项

- `STORY-005` 是否接受补充组合会计字段和调仓日幂等规则后再进入实现。
- `STORY-006` 是否按 HLD §9.2 的“第 rebalance_freq 个交易日触发信号”回写调仓日生成算法。
- `STORY-009/010/011` 是否在 LLD 包确认前关闭 source/interface 枚举，或将其明确列为实现前硬门禁。
- `STORY-012` 是否优先采用 CSV/JSON sidecar 作为 baseline/enhanced 审计输入。

## 5. Story × 14 维度矩阵

标记说明：Pass = 明确且可执行；Partial = 有方向但仍需补字段、算法或门禁；Fail = 维度缺失；NA = 本地离线 CLI/内存对象场景不适用，原因见矩阵备注。

| Story | 1 模块职责 | 2 接口 | 3 数据结构 | 4 业务流程 | 5 算法 | 6 并发 | 7 错误 | 8 配置 | 9 日志 | 10 监控 | 11 安全 | 12 单测 | 13 兼容/迁移 | 14 影响范围 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| STORY-004 | Pass | Pass | Pass | Pass | Pass | NA | Pass | Partial | Fail | NA | Pass | Pass | Partial | Pass |
| STORY-005 | Pass | Partial | Partial | Partial | Partial | Partial | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |
| STORY-006 | Pass | Pass | Pass | Partial | Partial | Pass | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |
| STORY-007 | Pass | Pass | Pass | Pass | Pass | NA | Pass | Pass | Fail | Partial | Pass | Pass | Pass | Pass |
| STORY-008 | Pass | Pass | Pass | Pass | Pass | NA | Pass | Partial | Fail | NA | Partial | Pass | Pass | Pass |
| STORY-009 | Pass | Partial | Partial | Pass | Partial | NA | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |
| STORY-010 | Pass | Partial | Partial | Pass | Partial | NA | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |
| STORY-011 | Pass | Partial | Partial | Pass | Partial | NA | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |
| STORY-012 | Pass | Partial | Partial | Pass | Pass | NA | Pass | Partial | Fail | NA | Pass | Pass | Partial | Pass |
| STORY-013 | Pass | Partial | Partial | Pass | Partial | NA | Pass | Partial | Fail | NA | Pass | Pass | Pass | Pass |

## 6. NA 与 Partial 说明

| 维度 | 适用判断 |
|---|---|
| 6 并发 | 大多数 Story 是本地离线 CLI 或纯函数串行路径，不涉及服务并发、事务锁或多用户更新，标 NA；但 STORY-005/006/007 涉及重复执行、扫描循环或无全局状态，若已有设计则 Pass/Partial。 |
| 10 监控 | 本项目不是常驻服务，QPS、在线延迟和队列长度等服务监控不适用；对扫描耗时、质量状态、失败率这类报告内指标可作为 Partial，但不等价于运行监控系统。 |
| 8 配置 | 多数 Story 定义了参数方向，但默认值、取值范围、动态生效方式未完全落到配置对象或 constants，因此标 Partial。 |
| 9 日志 | 所有 LLD 均未定义日志级别、事件名、run_id/trace id、脱敏和输出位置，因此标 Fail。 |

## 7. 用户重点补齐点回归

| 重点项 | 复核结论 | 证据 |
|---|---|---|
| STORY-004 质量报告缺失主路径失败 | 已补齐，Pass | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md:58`、`:169`、`:222`、`:304` |
| STORY-006 nav 完整性和 2019-2025 验收 | 已补齐，Pass；调仓日算法仍需按 F-002 加细 | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md:46`、`:47`、`:102`、`:166`、`:168` |
| STORY-007 扫描 CSV 完整 schema | 已补齐，Pass | `process/stories/STORY-007-parameter-sweep-report-LLD.md:47`、`:84`、`:158` |
| STORY-008 聚宽方向五类字段和保守低换手规则 | 已补齐，Pass | `process/stories/STORY-008-candidate-report-jq-template-LLD.md:46`、`:47`、`:124`、`:131`、`:152`、`:153` |
| STORY-009/010/011 raw/manifest/normalizer/quality/loader 同步契约 | 基本补齐，Partial；source/interface exact registry 仍需关闭 | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md:142`、`process/stories/STORY-010-trade-status-constraints-LLD.md:149`、`process/stories/STORY-011-limit-event-available-at-LLD.md:149` |
| STORY-011 依赖 STORY-010 | 已补齐，Pass | `process/stories/STORY-011-limit-event-available-at-LLD.md:22`、`:24`、`:27`、`process/DEVELOPMENT-PLAN.yaml:225`、`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md:108` |

## 8. 是否建议进入批量确认

结论：**条件通过**。

条件：

1. 批量确认前至少关闭 F-001 与 F-002，避免 W1 P0 主路径实现时出现不可复现的组合会计和调仓日算法。
2. 若仍要先进入批量确认，必须把 F-003 与 F-005 明确写成实现前硬门禁，禁止 W3 实现阶段临时猜测 source/interface 或审计输入 schema。
3. F-004 可作为批量确认后的统一 LLD 修订项，但应在任何 STORY-004+ 实现前补入最小日志契约。
