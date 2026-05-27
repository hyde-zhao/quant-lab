---
checkpoint_id: "STORY-PACKAGE-LLD-CHECKPOINT-2026-05-15"
checkpoint_type: "story-lld-package"
status: "confirmed"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-15"
created_at: "2026-05-15"
created_by: "meta-po"
updated_at: "2026-05-15"
updated_by: "meta-po"
scope: "STORY-004..STORY-013"
source_state: "process/STATE.md"
source_story_status: "process/STORY-STATUS.md"
source_lld_batch_plan: "process/LLD-BATCH-PLAN.md"
source_story_backlog: "process/STORY-BACKLOG.md"
source_development_plan: "process/DEVELOPMENT-PLAN.yaml"
implementation_allowed: true
delivery_write_allowed: false
data_generation_allowed: false
---

# STORY-004 至 STORY-013 批量 LLD / Story Package 人工确认检查点

> 本检查点只用于确认 LLD 包。用户已于 2026-05-15 明确确认通过，`STORY-004` 至 `STORY-013` 允许按 Story DAG、文件所有权和验证门控进入实现；仍不得生成真实生产数据、写入 `delivery/**` 或生成安装脚本。

## 0. 修订记录

| 日期 | 修订人 | 变更要点 |
|---|---|---|
| 2026-05-15 | codex | 按用户 `修改:` 请求修订 STORY-004/006/007/008/009/010/011 LLD：质量报告缺失主路径失败、nav 完整性、扫描完整 schema、聚宽差异字段、增强 raw/manifest/normalizer/quality/loader 同步契约，以及 STORY-011 依赖 STORY-010 |
| 2026-05-15 | meta-po | 组织 meta-dev/meta-qa 按 meta-se 风险解决方案修订 STORY-004 至 STORY-013 LLD：关闭 F-001/F-002 原确认前门禁，补 W3 exact registry、CLI 诊断日志、偏差审计输入契约、RSI/MACD 公式和 CSV/Markdown 文本字段公式注入防护；所有待确认 LLD 仍 `confirmed=false` |
| 2026-05-15 | meta-po | 用户明确确认通过批量 LLD / Story Package；回写 STORY-004 至 STORY-013 `confirmed=true`，并进入 story-execution 调度。 |

## 1. 检查点结论

| 检查项 | 结论 | 说明 |
|---|---|---|
| STORY-004 至 STORY-013 LLD 齐全 | 通过 | 10 个待确认 LLD 文件均存在 |
| 14 个可见主章节 | 通过 | 每个 LLD 均包含 14 个主章节，另有“人工确认区” |
| frontmatter 强输入字段 | 通过 | 每个 LLD 均包含 `story_id`、`title`、`story_slug`、`tier`、`status`、`confirmed`、`source_story`、`source_hld`、`source_adr`、`shared_fragments`、`open_items`、`depends_on` |
| LLD 确认状态 | 通过 | 10 个 LLD 均已按用户确认回写为 `status=confirmed`、`confirmed=true`、`confirmed_by=user`、`confirmed_at=2026-05-15` |
| Story 状态可进入 story-execution | 通过 | STORY-004 至 STORY-013 均纳入本批 Story Package 确认；STORY-001/002/003 保持 verified |
| 越界输出 | 通过 | 本检查点未实现代码、未生成真实数据、未写 `delivery/**`、未生成安装脚本 |
| LLD 风险整改 | 通过 | F-001/F-002 已完成 LLD 修订并由用户确认；F-003/F005/F006/F007 已收敛为 LLD 契约或实现前硬门禁；F-004 已补最小 CLI 诊断日志契约 |

## 1.1 LLD 风险整改执行摘要

| Finding | 原门禁 | 当前状态 | 说明 |
|---|---|---|---|
| F-001 | 原为确认前必修 | 关闭，用户已确认 | STORY-005 已补组合会计状态机、`PortfolioState` / `PositionRecord` / `TradeRecord` / `CostRecord` / `DailyPortfolioSnapshot` 字段、先卖后买、现金不足买入缩放、`rebalance_key` 幂等和会计恒等式测试；STORY-006 已固化 `PortfolioResult` 消费字段。 |
| F-002 | 原为确认前必修 | 关闭，用户已确认 | STORY-006 已新增 `build_rebalance_schedule(...)` 契约，明确 warm-up、首个信号日、每 `rebalance_freq` 个开市日触发、最后无 T+1 跳过/空 schedule 失败，以及 2019-2025 schedule fixture 测试；STORY-007 已引用该 schedule 口径。 |
| F-003 | W3 无条件确认阻塞 | 降级为 W3 实现前硬门禁 | STORY-009/010/011 已补共享 source/interface exact registry；未定 source/interface 使用 `UNRESOLVED`，data_prep、normalizer、quality、loader 启用路径均 fail fast，禁止模糊匹配。 |
| F-004 | 任一 STORY-004+ 实现前门禁 | 已补齐 LLD 契约 | STORY-004 至 STORY-013 均补最小本地 CLI 诊断日志契约；服务监控标 NA，不新增持久化日志文件。 |
| F-005 | W3 无条件确认阻塞 | 关闭，用户已确认 | STORY-012 已采用对象优先 + CSV/JSON sidecar 兼容输入，定义 `AuditComparableRun`、参数组合 key、baseline/enhanced `run_id`、候选 rank 字段和缺候选排序 warning 降级 schema。 |
| F-006 | STORY-013 实现前门禁 | 关闭，用户已确认 | STORY-013 已固化 RSI/MACD 公式、默认参数、warm-up、排序字段、tie-breaker、空目标 warning 和非法参数测试。 |
| F-007 | CSV/Markdown writer 实现前门禁 | 已补齐 LLD 契约 | STORY-007/008/012 已补 `sanitize_tabular_text` 等价契约，对 `= + - @` 开头的自由文本字段前置单引号，数值/日期/枚举不转字符串。 |

## 2. 批量确认范围

| Story ID | Wave | Story 状态 | LLD 文件 | LLD 状态 | open_items |
|---|---|---|---|---|---|
| STORY-004 | W1 | dev-ready | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | confirmed, confirmed=true | 3 |
| STORY-005 | W1 | lld-approved-blocked-by-dependency | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md` | confirmed, confirmed=true | 1 |
| STORY-006 | W1 | lld-approved-blocked-by-dependency | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md` | confirmed, confirmed=true | 1 |
| STORY-007 | W2 | lld-approved-blocked-by-dependency | `process/stories/STORY-007-parameter-sweep-report-LLD.md` | confirmed, confirmed=true | 0 |
| STORY-008 | W2 | lld-approved-blocked-by-dependency | `process/stories/STORY-008-candidate-report-jq-template-LLD.md` | confirmed, confirmed=true | 0 |
| STORY-009 | W3 | lld-approved-blocked-by-dependency | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md` | confirmed, confirmed=true | 4 |
| STORY-010 | W3 | lld-approved-blocked-by-dependency | `process/stories/STORY-010-trade-status-constraints-LLD.md` | confirmed, confirmed=true | 3 |
| STORY-011 | W3 | lld-approved-blocked-by-dependency | `process/stories/STORY-011-limit-event-available-at-LLD.md` | confirmed, confirmed=true | 3 |
| STORY-012 | W3 | lld-approved-blocked-by-dependency | `process/stories/STORY-012-bias-audit-report-LLD.md` | confirmed, confirmed=true | 0 |
| STORY-013 | W4 | lld-approved-blocked-by-dependency | `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md` | confirmed, confirmed=true | 0 |

## 3. 既有完成事实

| Story ID | 状态 | 说明 |
|---|---|---|
| STORY-001 | verified | LLD 已确认，实现已完成，meta-qa 正式验收 PASS |
| STORY-002 | verified | LLD 已确认，实现已完成，meta-qa 正式验收 PASS |
| STORY-003 | verified | LLD 已确认，实现与限定范围 bugfix 已完成，回归验证 PASS，`BUG-STORY-003-001` 已关闭 |

## 4. Open Items 与默认建议

| Story | Item | 当前问题 | 默认建议 | 影响 |
|---|---|---|---|---|
| STORY-004 | O-01 | 质量报告缺失时是否允许 Data Loader 在内存中调用 `calculate_quality(...)` 重算摘要但不写 `reports/**` | 已按用户修改：验收主路径缺 `reports/data_quality_report.csv` 直接 fail；仅显式探索模式可内存重算且不满足 P0 验收 | 与 HLD/ADR-006 对齐，避免绕过质量报告契约 |
| STORY-004 | O-02 | `quality_policy` 第一版是否只允许 pass/warn 成功、fail 永远拒绝 | 确认 pass/warn 可成功、fail 拒绝 | 降低误用 fail 数据的风险；不提供探索性绕过模式 |
| STORY-004 | O-03 | `.md` 质量报告是否不作为机器解析入口 | 只解析 CSV 或内存 `QualitySummary`，`.md` 仅作人工材料 | 避免 Markdown 表格解析脆弱性；要求后续质量报告保留机器可读 CSV |
| STORY-004 | O-04 | PIT 股票池声明不完整时 loader 拒绝还是警示 | 默认拒绝 `is_pit_universe=true` 但缺 `snapshot_date` 或 `available_at` 的数据 | 防止未来函数和股票池偏差；后续 STORY-009 可补齐契约 |
| STORY-005 | O-01 | STORY-004 `LoadedBacktestData` schema 与 `metadata` 字段是否确认 | 采用 STORY-004 LLD 中 `close_df`、`universe`、`calendar`、`metadata` 输出对象 | 下游组合和报告层可稳定消费 loader 输出 |
| STORY-005 | O-02 | `sell_buffer` 精确定义 | 已回写为 RESOLVED：采用 `top_count * (1 + sell_buffer)` 后取整为卖出缓冲边界 | 保持参数为比例语义；扫描时更易解释 |
| STORY-005 | O-03 | 全部目标未成交时继续还是失败 | 已回写为 RESOLVED：单期留现金并记录原因；仅在关键输入缺失或全区间不可运行时失败 | 避免单日不可交易导致整次回测失败，同时保留 metadata 披露 |
| STORY-006 | O-01 | Sharpe 标准差为 0 时输出什么 | 输出空值，并在 metadata warning 披露 | 防止除零或伪造 Sharpe；报告需处理空值 |
| STORY-006 | O-02 | STORY-005 `PortfolioResult` 成交金额字段名称 | 已回写为 RESOLVED：统一使用 `turnover_amount` 与 `trade_notional`，报告层消费 `turnover_amount` | 降低指标层与成交层字段歧义 |
| STORY-007 | O-01 | 扫描 CSV 26 类字段最终字段名 | 已按用户修改：STORY-007 LLD §5.1 固化完整扫描 CSV schema，覆盖参数、成本、区间、指标、状态、质量、新鲜度、偏差和过拟合警示字段 | 下游候选报告可按固定表头消费 |
| STORY-008 | O-01 | 保守低换手候选是否要求收益非负 | 已按用户修改：成功且质量合格，回撤不差于中位回撤 1.25 倍，收益非负或 Sharpe 不低于中位数 80%，再按换手升序选择 | 与 REQ-029 对齐；若无候选则记录缺失原因 |
| STORY-009 | O-01 | 历史沪深 300 成分股 raw source/interface 名称 | 已回写为 HARD-GATE：暂用 `UNRESOLVED`，W3 实现前替换为 exact source/interface；未替换时 batch planning、normalizer、quality 和 loader PIT 均 fail fast | 不阻塞 W1/W2；禁止伪造数据源或模糊匹配 |
| STORY-009 | O-02 | 只有日期无时间的 `available_at` 如何解释 | 统一按当日收盘后可用 | 与日频收盘信号口径一致，降低时间粒度复杂度 |
| STORY-009 | O-03 | PIT 缺单日成分覆盖时 fail 还是 warn | 对 P1 增强默认 fail；允许显式固定池 fallback 但不得混合伪装为 PIT | 提高 PIT 审计可信度；数据缺口会阻断 PIT 模式 |
| STORY-009 | O-04 | 是否允许同一区间 fixed 与 PIT 混合 | 默认不允许混合模式 | 避免回测期间股票池口径漂移 |
| STORY-010 | O-01 | 交易状态缺失时 warn 还是 fail | 默认 quality fail；若用户要求宽松，可显式降级为 warn + unknown 不成交 | 更符合真实性增强目标；可能提高数据准备要求 |
| STORY-010 | O-02 | 卖出不可交易原因枚举命名 | 使用方向化枚举：`sell_suspended`、`buy_suspended` 等 | 报告和审计可区分买卖方向约束 |
| STORY-010 | O-03 | 交易状态数据 source/interface 名称 | 已回写为 HARD-GATE：暂用 `UNRESOLVED`，W3 实现前替换为 exact source/interface；未替换时 batch planning、normalizer、quality 和 loader trade status 均 fail fast | 不阻塞 W1/W2；禁止伪造数据源或模糊匹配 |
| STORY-011 | O-01 | 涨停买入/跌停卖出默认拒绝还是延后 | 默认拒绝本次成交：买入留现金，卖出保留持仓 | 规则简单可审计；不引入订单排队或延后撮合 |
| STORY-011 | O-02 | limit_up/limit_down 与 qfq close 的口径一致性来源字段 | 已回写为 HARD-GATE：暂用 `UNRESOLVED`，W3 实现前替换为 exact source/interface；未替换时 batch planning、normalizer、quality 和启用约束均 fail fast | 避免价格口径混用；禁止伪造数据源或模糊匹配 |
| STORY-011 | O-03 | 第一批允许启用的事件类型 | 默认空集合；事件能力只做契约和校验，不进入动量第一版信号 | 防止事件字段被误用为未来信息 |
| STORY-012 | O-01 | baseline/enhanced 结果传入方式 | 已回写为 RESOLVED：对象优先 + CSV/JSON sidecar 兼容；CSV only 信息不足时 warning 降级 | 兼顾内存测试与文件级审计可复现 |
| STORY-012 | O-02 | 候选排序变化是否要求重新生成 enhanced 候选报告 | 已回写为 RESOLVED：优先比较 baseline/enhanced candidate rows；缺 rank 时输出 `candidate_rank_delta_status=not_available` 与 warning，不强制回头重跑 W2 | 审计保留指标 delta，不因候选排序缺失阻断全部报告 |
| STORY-013 | O-01 | RSI/MACD 默认参数 | 已回写为 RESOLVED：RSI 使用 `period=14`；MACD 使用 `fast=12`、`slow=26`、`signal=9` | 采用常见默认值，示例更易复现 |
| STORY-013 | O-02 | 策略接口返回目标集合还是允许目标权重前置集合 | 已回写为 RESOLVED：第一版返回目标集合；权重仍由组合层统一处理 | 保持策略层纯信号职责，避免绕过组合层契约 |

## 5. 批量确认结果

| 字段 | 值 |
|---|---|
| 确认结果 | 通过 |
| confirmed_by | user |
| confirmed_at | 2026-05-15 |
| 用户原文 | `确认通过，你可以让 Volta组织其他子agent并行完成所有story的开发了，注意story之间的存在依赖关系的story需要串行开发。` |
| 后续动作 | 进入 story-execution，按依赖 DAG、文件所有权和逐 Story 验证门控推进 |

## 6. 确认通过后的默认执行策略

1. meta-po 将 STORY-004 至 STORY-013 的 LLD 确认状态回写为通过，并只把依赖满足、文件所有权不冲突的 Story 放入 `dev-ready`。
2. 开发按 DAG 串行门控推进：`STORY-004 -> STORY-005 -> STORY-006 -> STORY-007 -> STORY-008 -> STORY-009 -> STORY-010 -> STORY-011 -> STORY-012`；`STORY-011` 必须在 `STORY-010` 的交易状态检查接口或等价共享交易约束接口就绪后实现。
3. 因用户明确要求“存在依赖关系的 story 串行、可并行则并行”，且 `STORY-013` 只依赖 `STORY-008`，与 W3 起点 `STORY-009` 文件所有权无冲突，`STORY-013` 在 `STORY-008` verified 后可与 W3 起点并行排队；若后续发现 `engine/scanner.py` / `engine/reporting.py` 写冲突，则退回串行。
4. 每个 Story 实现后进入 meta-qa 验证；验证通过后才收敛为 `verified`。
5. 整个开发与验证阶段继续禁止生成真实生产数据；测试使用临时目录、fixture 或 fake adapter。
