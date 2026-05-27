---
artifact: "process/reviews/LLD-DETAIL-REVIEW-RECHECK-2026-05-15.md"
reviewer: "Lorentz"
lane: "lane-implementation"
round: 2
status: draft
governance_mode: review-gated
---

# Review Findings

## 1. 审查范围

- 目标对象：F-001 至 F-007 整改复查；`process/stories/STORY-004-*-LLD.md` 至 `process/stories/STORY-013-*-LLD.md`
- 审查目标：确认原 LLD 评审 findings 是否被关闭、降级为硬门禁或仍需整改；确认 LLD 未误标 `confirmed=true`；确认 `STORY-010 -> STORY-011` 依赖仍存在
- 审查依据：`process/reviews/LLD-DETAIL-REVIEW-2026-05-15.md`、`process/reviews/LLD-RISK-RESOLUTION-PLAN-2026-05-15.md`、`process/reviews/LLD-RISK-RESOLUTION-EXECUTION-2026-05-15.md`、`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md`、相关 LLD、`process/DEVELOPMENT-PLAN.yaml`

## 2. Findings

<!-- findings-table -->

| ID | 原问题摘要 | 整改证据路径与行号 | 复查结论 | 剩余风险 | 是否阻塞批量确认 |
|----|------------|--------------------|----------|----------|------------------|
| F-001 | STORY-005 组合会计字段、先卖后买、现金缩放、调仓幂等和会计恒等式未定义。 | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md:95`-`:118` 补 `PortfolioState`、`PositionRecord`、`TradeRecord`、`CostRecord`、`DailyPortfolioSnapshot` 与 `PortfolioResult` 字段；`:141`-`:146` 补幂等、先卖后买、现金缩放、每日恒等式流程；`:167`-`:170` 固化成本、缩放、幂等和恒等式口径；`:196`-`:200` 补相关测试；`process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md:102`-`:107` 固化下游消费字段。 | CLOSED | 仅剩实现阶段需按 LLD 落地并测试；设计缺口已关闭。 | 否 |
| F-002 | STORY-006 调仓日生成算法不够可执行，缺 warm-up、首个信号日、T+1 缺失和 2019-2025 schedule 验收。 | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md:99`-`:101` 补 `RebalanceScheduleItem`；`:114` 新增 `build_rebalance_schedule(...)`；`:128`-`:129` 将回测流程改为使用 schedule；`:163`-`:169` 固化 warm-up、首个信号日、每 `rebalance_freq` 个开市日、T+1 跳过和 2019-2025 fixture；`:195`-`:198` 补 schedule 测试；`process/stories/STORY-007-parameter-sweep-report-LLD.md:146` 要求扫描继承 STORY-006 schedule。 | CLOSED | 仅剩实现阶段测试 fixture 必须真实覆盖固定日期集合；设计缺口已关闭。 | 否 |
| F-003 | STORY-009/010/011 raw/manifest/normalizer/quality/loader 同步契约缺 source/interface exact registry；原 `source/interface` 仍未定。 | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md:102`-`:106` 建立 `index_members` registry 且 `UNRESOLVED` fail fast；`:155`-`:157` 禁止模糊匹配；`process/stories/STORY-010-trade-status-constraints-LLD.md:104`-`:108` 建立 `trade_status` registry；`:161` 要求 exact registry；`process/stories/STORY-011-limit-event-available-at-LLD.md:106`-`:111` 建立 `prices_limit/events` registry；`:162` 要求 exact registry 与 `UNRESOLVED` fail fast；`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md:50`、`:94`、`:100`、`:102` 明确降级为 W3 实现前硬门禁。 | DOWNGRADED-HARD-GATE | `source/interface` 仍是 `UNRESOLVED`，不能进入 W3 数据准备、normalizer、quality、loader 启用实现；但 fail-fast 门禁足以阻止模糊匹配和伪造数据源。 | 否；阻塞 W3 实现，不阻塞用户批量确认 |
| F-004 | STORY-004 至 STORY-013 缺最小日志设计；服务监控可 NA，但 CLI 诊断日志不可缺。 | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md:288`、`:317`、`:333` 补 data loader 日志契约、测试和任务；`process/stories/STORY-007-parameter-sweep-report-LLD.md:159`、`:174` 补 scanner 日志；`process/stories/STORY-010-trade-status-constraints-LLD.md:172`、`:193` 补 trade status 日志；`process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md:153`、`:173` 补策略日志；`checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md:51` 汇总已补最小本地 CLI 诊断日志契约。 | CLOSED | 代码尚未实现，但本次只复查 LLD 契约；实现时必须按日志契约落地。 | 否 |
| F-005 | STORY-012 偏差审计 baseline/enhanced 输入契约、关联键、候选 rank 降级 schema 未定。 | `process/stories/STORY-012-bias-audit-report-LLD.md:84`-`:102` 定义 `AuditInputSource`、`AuditComparableRun`、`params_key`、候选 rank、降级 warning 与文本防护；`:113`-`:117` 增加输入加载、归一化和写出接口；`:123`-`:127` 固化对象/CSV+sidecar 输入与缺 rank 降级流程；`:149`-`:152` 固化输入优先级、参数组合 key、run_id 和 candidate rank 降级；`:176`-`:179` 补对象输入、CSV sidecar、归一化和缺 rank 测试。 | CLOSED | CSV only 路径信息不足仍会 warning 降级，但这是已设计的可控行为。 | 否 |
| F-006 | STORY-013 RSI/MACD 示例算法仍是示例语言，缺确定公式、默认参数、warm-up、排序和 tie-breaker。 | `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md:91`-`:94` 固化 RSI/MACD 参数；`:132`-`:139` 固化 Wilder RSI、MACD `adjust=False`、目标选择、warm-up 和参数校验；`:163`-`:167` 补公式、warm-up、tie-breaker、空目标测试；`:180`-`:181` 将公式和测试写入实施步骤。 | CLOSED | STORY-013 仍为 W4/P2；实现前需按已固化公式落地。 | 否 |
| F-007 | STORY-007/008/012 CSV/Markdown 自由文本字段缺公式注入防护。 | `process/stories/STORY-007-parameter-sweep-report-LLD.md:147`、`:156`、`:173` 补扫描 CSV 文本防护和测试；`process/stories/STORY-008-candidate-report-jq-template-LLD.md:91`、`:103`、`:140`、`:168` 补候选 CSV `sanitize_tabular_text` 契约和测试；`process/stories/STORY-012-bias-audit-report-LLD.md:102`、`:117`、`:155`、`:185` 补审计 CSV/Markdown 表格文本防护和测试。 | CLOSED | 代码尚未实现，但 LLD 已明确文本字段转义契约。 | 否 |

## 3. 汇总结论

- blocking_count: 0
- required_count: 0
- optional_count: 0
- recommended_next_action: `proceed-to-human-batch-confirmation`

总体结论：**条件关闭**。

说明：F-001、F-002、F-004、F-005、F-006、F-007 已在 LLD 契约层关闭；F-003 仍保留 `UNRESOLVED`，但已明确降级为 W3 实现前硬门禁，并且 LLD 写明 fail fast 与禁止模糊匹配，因此不再阻塞用户批量确认。

## 4. 待确认项

- 用户仍需在 `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md` 指定的批量确认协议中确认 STORY-004 至 STORY-013 LLD 包。
- W3 实现前必须将 STORY-009/010/011 的 `UNRESOLVED` source/interface 替换为 exact 值；未替换时相关 data_prep、normalizer、quality、loader 启用路径必须 fail fast。

## 5. 门控复核

| 门控项 | 证据 | 结论 |
|---|---|---|
| STORY-004 至 STORY-013 LLD frontmatter 未误标 `confirmed: true` | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md:8`、`STORY-005...LLD.md:8`、`STORY-006...LLD.md:8`、`STORY-007...LLD.md:8`、`STORY-008...LLD.md:8`、`STORY-009...LLD.md:8`、`STORY-010...LLD.md:8`、`STORY-011...LLD.md:8`、`STORY-012...LLD.md:8`、`STORY-013...LLD.md:8` 均为 `confirmed: false`；另用 frontmatter 扫描未发现 `confirmed: true`。 | PASS |
| `STORY-010 -> STORY-011` 依赖仍存在 | `process/stories/STORY-011-limit-event-available-at-LLD.md:24`-`:28` 保留 `STORY-010` Story 与 LLD 依赖；`process/DEVELOPMENT-PLAN.yaml:225` 保留 `depends_on: ["STORY-009", "STORY-010"]`；`:294` 保留边 `["STORY-010", "STORY-011"]`。 | PASS |
| 检查点仍禁止实现、写 delivery、生成数据 | `checkpoints/STORY-PACKAGE-LLD-CHECKPOINT.md:16`-`:18` 为 false，`:23` 明确确认前不得实现、生成数据、写 `delivery/**` 或标记 confirmed。 | PASS |

## 6. 是否建议进入用户批量确认

建议：**可以进入用户批量确认**。

剩余硬门禁：

1. 用户确认前仍不得实现 STORY-004+、不得生成数据、不得写 `delivery/**`、不得把任何 LLD 标记为 `confirmed=true`。
2. STORY-009/010/011 的 `source/interface=UNRESOLVED` 是 W3 实现前硬门禁；替换为 exact 值前，相关启用路径必须 fail fast。
