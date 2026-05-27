---
artifact: "process/reviews/LLD-RISK-RESOLUTION-PLAN-2026-05-15.md"
owner: "meta-se"
lane: "lane-architecture"
status: "draft"
created_at: "2026-05-15"
source_review: "process/reviews/LLD-DETAIL-REVIEW-2026-05-15.md"
scope: "LLD risk resolution plan"
confirmed: false
---

# LLD 风险解决方案计划

> 本文只做架构/设计层风险分析与修订建议，不修改 LLD 本体，不实现代码，不生成数据，不写 `delivery/**`，不将任何 LLD 标记为 `confirmed=true`。

## 1. 输入与边界

### 1.1 已读取输入

| 类型 | 文件 |
|---|---|
| 评审来源 | `process/reviews/LLD-DETAIL-REVIEW-2026-05-15.md` |
| 架构基线 | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md` |
| 计划基线 | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` |
| 主要 LLD | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md`、`process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md`、`process/stories/STORY-009-pit-universe-provider-contract-LLD.md`、`process/stories/STORY-010-trade-status-constraints-LLD.md`、`process/stories/STORY-011-limit-event-available-at-LLD.md`、`process/stories/STORY-012-bias-audit-report-LLD.md`、`process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md` |
| 必要补充 LLD | `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`、`process/stories/STORY-007-parameter-sweep-report-LLD.md`、`process/stories/STORY-008-candidate-report-jq-template-LLD.md` |

### 1.2 判断原则

| 原则 | 说明 |
|---|---|
| P0 主路径优先 | STORY-005/006 是 W1 单次回测主链路，若算法口径不确定，会传导到 W2 扫描和候选选择，必须在批量确认前修订。 |
| exact 契约优先 | HLD 与项目规则均要求 source/interface、字段、路径、版本和规则命中使用 exact 语义，不允许实现阶段猜字符串或模糊匹配。 |
| LLD 门控不等于实现 | 对 P1/P2 增强可允许条件确认，但必须在对应 Story 实现前关闭 OPEN 或写成硬门禁。 |
| 横切规则集中定义、分散回写 | 日志、CSV 注入防护这类横切问题应有统一最小契约，再回写到受影响 LLD 的接口、错误、安全、测试和实施章节。 |

## 2. 总体结论

| Finding | 风险等级判断 | 影响范围 | 是否阻塞批量确认 | 推荐处理时机 | meta-se 结论 |
|---|---|---|---|---|---|
| F-001 | 高 | STORY-005，传导至 STORY-006/007/008 | 是 | 批量确认前修订 | 补齐组合会计状态机、字段表、买卖顺序、现金缩放、幂等键和恒等式测试。 |
| F-002 | 高 | STORY-006，传导至 STORY-007/008 | 是 | 批量确认前修订 | 补齐可执行调仓日生成算法，明确 warm-up、首个信号日、T+1 缺失和边界测试。 |
| F-003 | 中高 | STORY-009/010/011 | 阻塞 W3 无条件确认；不阻塞 W1/W2 | 条件确认硬门禁或 W3 实现前修订 | 建立共享 source/interface exact registry；未定数据源必须使用 `UNRESOLVED` 并 fail fast。 |
| F-004 | 中 | STORY-004 至 STORY-013 | 不阻塞批量确认，但阻塞任一受影响 Story 实现 | 实现前硬门禁，优先随批量修订一次性补齐 | 定义本地 CLI 最小诊断日志契约；监控标 NA，但日志不可缺。 |
| F-005 | 中高 | STORY-012，可能回传 STORY-006/007/008/010/011 | 阻塞 W3 无条件确认；不阻塞 W1/W2 | 条件确认硬门禁或 STORY-012 实现前修订 | 审计输入采用对象优先、CSV/JSON sidecar 兼容的双入口契约，并固化关联键。 |
| F-006 | 中低 | STORY-013 | 否 | 后置到 P2 Story；STORY-013 实现前硬门禁 | 把 RSI/MACD 从示例语言收敛为确定性公式、默认参数、排序与 tie-breaker。 |
| F-007 | 中 | STORY-007/008/012，扩展至所有 CSV/Markdown 表格文本输出 | 不阻塞批量确认，但阻塞 CSV writer 实现 | 实现前硬门禁；建议随 F-004 统一回写 | 建立 `sanitize_tabular_text` 或等价 CSV 文本字段转义契约，并补测试。 |

## 3. F-001：STORY-005 组合会计细节不足

### 3.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 高。组合会计是净值、换手、成本、现金和候选排序的事实源。 |
| 影响范围 | 直接影响 `PortfolioResult.nav/positions/trades/costs/cash/turnover/unfilled`；传导至 STORY-006 指标、STORY-007 扫描和 STORY-008 候选选择。 |
| 是否阻塞批量确认 | 是。STORY-005 是 W1 P0 主路径，不能把会计口径留给实现阶段自由解释。 |
| 推荐处理时机 | 批量确认前修订 STORY-005 LLD，并同步解除 STORY-006 中 `PortfolioResult` 字段名 OPEN。 |

### 3.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. 内存级会计状态机固化 | 在 STORY-005 LLD 内定义 `PortfolioState`、`PositionRecord`、`TradeRecord`、`CostRecord`、`DailyPortfolioSnapshot` 字段；按交易日状态转移更新现金、持仓、成本、净值 | 最小改动；符合轻量本地回测层；可直接服务 W1/W2 | 不提供独立账本持久化；审计历史依赖返回对象 | 第一版研究工具；不追求完整交易系统 | 修订 STORY-005 §5/6/7/8/10/11/12；STORY-006 §5/6/12 引用字段 |
| B. 引入事件/账本 ledger 抽象 | 将每笔买卖、成本、现金变动作为 ledger event，再由 ledger 聚合出每日状态 | 审计能力更强；后续交易状态/涨跌停增强更自然 | 明显提高复杂度；可能偏离 HLD “轻量日频回测层”；扩大文件影响范围 | 后续明确要做完整事件驱动或多账户审计 | 需要重写 STORY-005 模块边界，影响 STORY-006/010/011 |

### 3.3 推荐方案

推荐 **方案 A：内存级会计状态机固化**。

理由：

- HLD 与 ADR-002 选择的是项目内轻量日频回测层，不应为第一版引入完整 ledger 抽象。
- F-001 的核心问题是字段、顺序、现金约束和幂等口径缺失，不是需要事件驱动框架。
- 方案 A 可以在 LLD 层完成契约收敛，不需要回退 Story planning。

### 3.4 必须收敛的设计点

| 设计点 | 推荐口径 |
|---|---|
| 持仓字段 | `symbol`、`quantity`、`last_price`、`market_value`、`weight`、`cost_basis`、`as_of_date`；第一版允许小数股，`quantity = target_amount / execution_price`。 |
| 现金字段 | `cash_before_trade`、`cash_after_sell`、`cash_after_buy`、`ending_cash`。 |
| 交易字段 | `trade_id`、`rebalance_key`、`signal_date`、`execution_date`、`symbol`、`side`、`quantity`、`price`、`gross_amount`、`commission`、`slippage`、`sell_tax`、`net_cash_flow`、`status`、`unfilled_reason`。 |
| 买卖顺序 | 先卖出非目标或超配部分，再用卖出后现金执行买入。 |
| 买入缩放 | 当计划买入总额加买入成本超过可用现金时，对全部买入目标按比例缩放；缩放后仍保留等权意图与实际成交金额差异。 |
| 成本扣除 | 成本在 T+1 调仓成交后扣除；买入成本减少现金，卖出税只作用于卖出。 |
| 幂等口径 | `rebalance_key = signal_date + execution_date + params_hash`；同一 `PortfolioState` 不允许重复应用同一 key。 |
| 会计恒等式 | 每日 `nav = ending_cash + sum(position_market_value)`；成本通过现金流体现，不再二次从 nav 中扣除；误差容忍使用浮点 epsilon。 |
| 全部目标未成交 | 默认留现金并继续，若连续或比例阈值导致质量 fail 可由 STORY-006/007 失败策略处理；不要在组合层随意失败。 |

### 3.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-005 | §5 数据模型与持久化设计：补字段表；§6 API：补 `PortfolioState` 输入/输出；§7 核心流程：补状态转移；§8 技术细节：补卖买顺序、缩放、幂等；§10 测试：补会计恒等式、现金不足缩放、重复 rebalance key；§11 实施步骤：补会计对象与测试；§12 OPEN：关闭 O-03 或改为已默认。 |
| STORY-006 | §5/6/12：引用确认后的 `PortfolioResult` 字段，关闭 O-02 或转为已解决。 |

## 4. F-002：STORY-006 调仓日生成算法不够可执行

### 4.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 高。调仓日集合直接决定收益路径、扫描行指标、失败行和候选选择。 |
| 影响范围 | STORY-006 `run_backtest`，传导至 STORY-007 60 组扫描与 STORY-008 候选报告。 |
| 是否阻塞批量确认 | 是。HLD 已确认“第 `rebalance_freq` 个交易日触发信号，T+1 或之后成交”，LLD 必须落到可执行算法。 |
| 推荐处理时机 | 批量确认前修订 STORY-006 LLD。 |

### 4.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. calendar 驱动的确定性 schedule 函数 | 定义 `build_rebalance_schedule(calendar, lookback_days, rebalance_freq, start_date, end_date)`；从满足 warm-up 的首个信号日开始，每 `rebalance_freq` 个开市日触发；要求存在 T+1 执行日 | 与 HLD 完全对齐；可单测；W2 复现稳定 | 需要明确最后无 T+1 是跳过还是失败 | 第一版本地主路径 | 修订 STORY-006 §6/7/8/10/11 |
| B. 由组合层遇到日期动态决定 | `run_portfolio` 遍历 calendar，按计数器决定是否调仓 | 状态集中在组合层；回测入口较薄 | 破坏信号/组合分层；难以让 STORY-007 复用和测试 schedule | 若未来改成事件循环框架 | 需要调整 STORY-005/006 边界，不推荐 |

### 4.3 推荐方案

推荐 **方案 A：calendar 驱动的确定性 schedule 函数**。

理由：

- HLD 的调仓日规则属于 backtest 编排责任，不应下沉到组合层。
- 参数扫描需要对 schedule 进行可复现测试，独立函数最容易固定边界。
- 该方案不扩大文件影响范围，仍在 STORY-006 `engine/backtest.py` 内闭合。

### 4.4 必须收敛的设计点

| 设计点 | 推荐口径 |
|---|---|
| calendar 输入 | 使用 STORY-004 返回的请求区间开市日，升序且无重复。 |
| warm-up | `signal_date` 必须有 `lookback_days` 个历史开市日可用于动量端点；首个信号日为 `calendar[lookback_days]` 或等价第一个满足窗口的开市日。 |
| rebalance 计数 | 从首个合格信号日开始计数；首个信号日触发一次，此后每隔 `rebalance_freq` 个开市日触发。 |
| 成交日 | 每个 signal_date 必须能找到下一个开市日作为默认 T+1 execution_date；找不到时该 signal 不进入 schedule，并记录 `skipped_no_execution_date`。若整个 schedule 为空，单次回测失败。 |
| end_date 边界 | 信号日必须在请求区间内；执行日可在请求区间内，若执行日超过请求区间则跳过并 warning，避免生成无法归属收益的最后一笔交易。 |
| 2019-2025 验收 | fixture 应固定 start/end、lookback、rebalance_freq 下的 signal/execution 日期集合，而不只检查净值覆盖。 |

### 4.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-006 | §6 API：新增 `build_rebalance_schedule`；§7 核心流程：用 schedule 替换“按 rebalance_freq 生成调仓日”的泛化描述；§8 技术设计细节：补 warm-up、首个信号日、最后无 T+1、空 schedule；§10 测试：新增 `T-REBALANCE-SCHEDULE-01`、`T-REBALANCE-WARMUP-01`、`T-NO-TPLUS1-SKIP-01`、`T-BACKTEST-2019-2025-SCHEDULE-01`；§11 实施步骤：补 schedule 任务。 |
| STORY-007 | §12 风险：引用 STORY-006 schedule 固定字段，避免扫描结果因调仓算法变动。 |

## 5. F-003：STORY-009/010/011 source/interface exact registry 缺口

### 5.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 中高。W3 扩展必须同步 raw、manifest、normalizer、quality、loader；source/interface 未定会破坏 exact 契约。 |
| 影响范围 | STORY-009 PIT 成分、STORY-010 交易状态、STORY-011 涨跌停/事件；间接影响 STORY-012 审计输入。 |
| 是否阻塞批量确认 | 不阻塞 W1/W2；阻塞 W3 无条件确认。若整包批量确认，需要把 registry 关闭作为 W3 实现前硬门禁。 |
| 推荐处理时机 | 最好在批量确认前补最小 registry；若数据源确实未定，则条件确认并在 W3 实现前关闭。 |

### 5.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. LLD 内共享 registry 表 | 在 STORY-009/010/011 各自 LLD 中加入同构 registry 表：`target_dataset`、`source`、`interface`、raw metadata、manifest fields、normalizer function、fail-fast 行为 | 不新增规划文件；修订局部；可快速闭合 exact 契约 | 三份 LLD 可能重复，需要保持一致 | 数据源基本可确认，或可使用 `UNRESOLVED` | 修订三份 LLD §5/6/8/10/11/12 |
| B. 新增统一实现期 registry 模块 | 设计 `engine/contracts.py` 中统一 `DATASET_INTERFACE_REGISTRY`，所有 normalizer/data_prep 使用 | 运行时一致性最好；减少重复 | 对 W0 已实现/验证部分可能有变更影响；需谨慎避免回写过大 | W3 确认要统一扩展 source/interface | 修订 STORY-009/010/011 及可能 STORY-003/004/002 的 contracts 影响 |
| C. 保持 OPEN 到实现前确认 | LLD 不写具体枚举，只写实现前由用户确认 | 初始成本最低 | 与 exact 规则冲突；实现阶段容易猜测；review 仍会卡住 | 仅当 W3 长期后置且不做整包无条件确认 | 只能作为条件确认，不可直接开发 |

### 5.3 推荐方案

推荐 **方案 A，并允许使用 `UNRESOLVED` 占位 + fail fast**。

理由：

- 当前问题可以在 LLD 内闭合，不需要回退 Story planning。
- `UNRESOLVED` 是显式状态，不是模糊匹配；可以保证实现阶段不会猜 source/interface。
- 若后续 W3 需要运行时统一注册，可在 STORY-009/010/011 的 `engine/contracts.py` 修改中落地，不必提前影响 W0-W2。

### 5.4 最小 registry 契约

| 字段 | 推荐要求 |
|---|---|
| `target_dataset` | 枚举：`index_members`、`trade_status`、`prices_limit`、`events`。 |
| `source` | 已确认则写具体源；未确认写 `UNRESOLVED`。 |
| `interface` | 已确认则写 exact interface；未确认写 `UNRESOLVED`。 |
| `raw_metadata_required` | 至少包含 `target_dataset`、`source`、`interface`、`request_params`、覆盖区间、`raw_path`。 |
| `manifest_required` | 覆盖 dataset 专属字段、`raw_path`、`standardized_output_path`、`success_items`、`failed_items`、`status`。 |
| `normalizer_entry` | 指向明确函数名，如 `normalize_historical_members`、`normalize_trade_status`、`normalize_limit_event`。 |
| `fail_fast_rule` | 任一 `source/interface=UNRESOLVED` 时，data_prep batch planning、normalizer exact dispatch 和 quality 入口必须失败，错误说明需要实现前确认。 |

### 5.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-009 | §5 数据模型：补 registry 表；§6 API：明确 `plan_historical_members_batches` 消费 registry；§8 技术细节：补 `UNRESOLVED` fail fast；§10 测试：补 `T-UNRESOLVED-INTERFACE-FAIL-01`；§12 OPEN：O-01 改为硬门禁或已解决。 |
| STORY-010 | §5/6/8/10/12 同步补交易状态 registry 与 `UNRESOLVED` 规则。 |
| STORY-011 | §5/6/8/10/12 同步补 limit/event registry 与 `UNRESOLVED` 规则。 |

## 6. F-004：STORY-004 至 STORY-013 最小日志契约缺口

### 6.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 中。本项目不是服务型系统，监控可标 NA，但本地 CLI/离线工具仍需要可追溯诊断日志。 |
| 影响范围 | STORY-004 至 STORY-013 所有入口、报告写入和失败路径。 |
| 是否阻塞批量确认 | 不阻塞批量确认；但阻塞任一受影响 Story 实现。 |
| 推荐处理时机 | 作为实现前硬门禁；建议在批量确认前一次性回写，避免每个 Story 独立解释日志。 |

### 6.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. 最小本地 CLI 诊断日志契约 | 使用 Python logging 或等价标准库；规定 `INFO start/end`、`WARNING degraded`、`ERROR structured_error`；输出 stderr；字段含 run_id/module/params/path/status | 轻量；不引入服务监控；满足可调试性 | 不提供集中采集和指标看板 | 当前本地研究工具 | 回写 STORY-004 至 013 §9/10/11 |
| B. 结构化 JSONL 运行日志文件 | 每次运行写 `reports/run_logs/*.jsonl` 或类似路径 | 审计更强，便于后续分析 | 新增持久化输出面；需要路径、清理、隐私规则；可能超出 LLD 允许范围 | 用户明确需要运行日志文件 | 需要新增输出文件边界，影响多个 Story |

### 6.3 推荐方案

推荐 **方案 A：最小本地 CLI 诊断日志契约**。

理由：

- HLD 强调本地轻量工具与报告可追溯，不要求服务监控。
- 标准库 logging 可满足调试，不新增持久化文件和清理负担。
- 诊断日志作为实现前硬门禁即可，不必阻断当前整包设计确认。

### 6.4 最小日志契约

| 项 | 推荐要求 |
|---|---|
| 输出位置 | 默认 stderr；不写持久化日志文件，除非后续另起 Story。 |
| 日志级别 | `INFO`：入口 start/end；`WARNING`：quality warn、降级、跳过、单组失败保留；`ERROR`：结构化错误。 |
| 公共字段 | `event_name`、`run_id` 或 `manifest_run_id`、`module`、`story_id`、`status`、`params_summary`、`relative_path`、`elapsed_seconds`。 |
| 脱敏规则 | 不记录凭据、绝对隐私路径、完整原始响应、大型 DataFrame；路径优先相对仓库路径。 |
| 监控口径 | 本地 CLI 不接入服务监控，§9/§10 中监控标 NA，但日志契约必须存在。 |
| 错误衔接 | 日志不替代结构化异常；ERROR 日志应记录异常 `to_dict()` 摘要。 |

### 6.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-004 至 STORY-013 | §9 安全与性能设计：新增“诊断日志”行；§10 测试设计：新增 `T-LOGGING-MINIMAL-01` 或按 Story 命名；§11 实施步骤：在入口/写报告/失败捕获任务中加入日志要求。 |
| STORY-007/008/012 | 同步说明 CSV/报告写入失败的 ERROR 日志字段。 |

## 7. F-005：STORY-012 偏差审计输入契约未定

### 7.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 中高。审计输入不确定会反向推动 W2 报告 schema 和 W3 增强结果对象返工。 |
| 影响范围 | STORY-012，可能影响 STORY-006 BacktestResult、STORY-007 扫描 CSV、STORY-008 候选 CSV、STORY-010/011 约束明细。 |
| 是否阻塞批量确认 | 阻塞 W3 无条件确认；不阻塞 W1/W2 主路径。 |
| 推荐处理时机 | 条件确认硬门禁；若整包无条件确认，则批量确认前修订 STORY-012。 |

### 7.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. 对象优先 + sidecar 兼容 | `run_bias_audit` 主要接收 `BacktestResult`/candidate rows 内存对象；可选读取 CSV + JSON metadata sidecar；统一转换为 `AuditComparableRun` | 不强迫 W2 立即改为 sidecar；实现可单测；兼容 CLI 报告 | 需要定义转换函数和最小字段集 | 第一版 W3 审计，需兼容内存和报告文件 | 修订 STORY-012 §5/6/7/8/10/11/12 |
| B. 只消费 CSV 报告 | baseline/enhanced 均从扫描/候选 CSV 读取 | 用户可复现；与报告产物直接绑定 | 单次回测对象、约束明细和 metadata 复杂字段会被压扁；可能要求 W2 补 sidecar | 审计只面向运行后文件 | 可能反向修改 STORY-006/007/008 报告 schema |
| C. 只消费内存对象 | 审计模块只接受已运行的 baseline/enhanced `BacktestResult` 和候选 rows | 实现简单，测试清晰 | CLI 文件级审计不便；用户无法仅凭报告重跑审计 | 审计只作为代码内 API，不作为用户报告工具 | 与 HLD 偏差审计报告可交接性弱 |

### 7.3 推荐方案

推荐 **方案 A：对象优先 + sidecar 兼容**。

理由：

- 它避免为了 STORY-012 提前重构 W2 CSV，又给后续 CLI 文件审计留出路径。
- `AuditComparableRun` 可以成为审计内部稳定对象，屏蔽 baseline/enhanced 来源差异。
- 候选排序缺失时可以降级为指标 delta + warning，不必阻断完整审计。

### 7.4 最小输入契约

| 字段 | 推荐要求 |
|---|---|
| run identity | `run_id`、`scenario_label` 枚举 `baseline/enhanced`、`params_hash` 或参数组合 key。 |
| 参数组合 key | `strategy_name`、`lookback_days`、`rebalance_freq`、`top_fraction`、`sell_buffer`、成本参数。 |
| 指标字段 | `total_return`、`annual_return`、`max_drawdown`、`sharpe`、`turnover`、`final_nav`。 |
| 限制项 metadata | `is_pit_universe`、trade status enabled、limit enabled、event enabled、execution timing、available_at rule。 |
| 约束明细 | `unfilled_reason`、constraint reason、affected sample count；无明细时允许用 metadata 汇总并 warning。 |
| 候选字段 | `candidate_type`、`rank`、参数组合 key、核心指标；缺候选排序时输出 `candidate_rank_delta_status=not_available`。 |
| 文件输入 | CSV 为行级数据；复杂 metadata 可来自 JSON sidecar；若没有 sidecar，使用 CSV 扁平字段并标记信息不足。 |

### 7.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-012 | §5 数据模型：新增 `AuditComparableRun`、`AuditCandidateRow`、输入来源枚举；§6 API：补 `load_audit_inputs`、`normalize_audit_input`；§7 流程：先归一化再比较；§8 技术细节：参数组合 key、缺候选降级；§10 测试：补对象输入、CSV+sidecar 输入、缺候选排序 warning；§12 OPEN：关闭 O-01/O-02 或改为实现前硬门禁。 |
| STORY-006/007/008 | 不必立即重写；只需在各自风险或报告字段章节标注 STORY-012 读取的最小字段，不要求新增真实 sidecar。 |

## 8. F-006：STORY-013 RSI/MACD 示例算法不够确定

### 8.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 中低。STORY-013 是 P2，非 W1/W2 主路径，但实现前必须保证示例可复现。 |
| 影响范围 | STORY-013 的 `strategies/rsi.py`、`strategies/macd.py`、`engine/scanner.py` 策略分派和 reporting 策略字段。 |
| 是否阻塞批量确认 | 否。可后置到 P2 Story 或作为 STORY-013 实现前硬门禁。 |
| 推荐处理时机 | STORY-013 LLD 单独确认或实现前修订。 |

### 8.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. 固化 RSI/MACD 示例公式 | RSI 使用 Wilder 平滑或明确 rolling 口径；MACD 使用 pandas `ewm(adjust=False)`；定义 warm-up、排序和 tie-breaker | 可复现；测试明确；保留示例价值 | 需要选择技术口径 | STORY-013 仍作为示例策略 | 修订 STORY-013 §8/10/12 |
| B. 把 RSI/MACD 降级为接口占位 | 只实现策略协议和伪示例，不承诺指标公式 | 减少争议；更聚焦扩展接口 | 不满足“至少 2 个策略函数示例可进入同一报告 schema”的验收精神 | 用户只关心接口，不关心示例结果 | 需要调整验收与测试，可能不符合 Backlog |

### 8.3 推荐方案

推荐 **方案 A：固化 RSI/MACD 示例公式**。

理由：

- Backlog 明确 STORY-013 需要两个策略函数示例进入同一报告 schema。
- 示例策略如果不可复现，会削弱策略扩展接口测试。
- 该问题不影响 P0，可后置，但不能进入实现。

### 8.4 推荐算法口径

| 策略 | 推荐口径 |
|---|---|
| RSI | 默认 `period=14`，使用 Wilder 平滑：`avg_gain/avg_loss` 递推或 `ewm(alpha=1/period, adjust=False)`；`RSI = 100 - 100/(1+RS)`；warm-up 不足剔除。 |
| RSI 目标选择 | 选择 RSI 由低位回升的 symbol：可定义 `rsi_prev < oversold` 且 `rsi_current >= oversold`；排序按 `rsi_current - rsi_prev` 降序、`rsi_current` 升序、symbol 升序；无反转目标时返回空目标并 warning。 |
| MACD | 默认 `fast=12`、`slow=26`、`signal=9`，EMA 使用 `adjust=False`；`macd_line = ema_fast - ema_slow`，`signal_line = ewm(macd_line, span=signal, adjust=False)`，`histogram = macd_line - signal_line`。 |
| MACD 目标选择 | 金叉优先：`hist_prev <= 0` 且 `hist_current > 0`；排序按 `hist_current - hist_prev` 降序、`hist_current` 降序、symbol 升序；无金叉目标时返回空目标并 warning。 |
| 参数校验 | `period > 1`；`fast < slow`；`signal > 1`；`top_fraction` 与动量同约束。 |

### 8.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-013 | §8 技术设计细节：替换“可设/示例”语言为确定公式；§10 测试：补公式 fixture、warm-up、tie-breaker、非法参数、空目标；§12 OPEN：关闭 O-01，O-02 默认目标集合。 |

## 9. F-007：STORY-007/008/012 CSV/表格公式注入防护缺口

### 9.1 风险判断

| 维度 | 判断 |
|---|---|
| 风险 | 中。报告面向人工打开，错误文本、选择理由、聚宽备注、差异原因等文本字段存在表格公式注入风险。 |
| 影响范围 | STORY-007 扫描 CSV、STORY-008 候选 CSV、STORY-012 审计 CSV/Markdown 表格；可扩展到所有表格文本输出。 |
| 是否阻塞批量确认 | 不阻塞批量确认；但阻塞 CSV writer 实现。 |
| 推荐处理时机 | 实现前硬门禁；建议与 F-004 一起作为横切规则回写。 |

### 9.2 可选方案对比

| 方案 | 核心做法 | 优点 | 缺点 | 适用条件 | 对 Story/LLD 的影响 |
|---|---|---|---|---|---|
| A. 写入前文本字段统一转义 | 定义 `sanitize_tabular_text(value)`：文本首个非空字符为 `= + - @` 时前置单引号；只作用于声明为文本的 CSV/表格字段 | 简单、明确、易测；不影响数值字段排序 | 用户看到前置单引号；需要字段分类 | 当前 CSV 报告 | 修订 STORY-007/008/012 §8/9/10/11 |
| B. 全字段强制字符串化并 quote | 所有字段都按 CSV quote 写出，并对危险首字符加前缀 | 安全覆盖广 | 数值字段类型丢失，不利于排序和后续读取 | 报告只给人工阅读 | 会影响 STORY-008 读取扫描 CSV，不推荐 |
| C. 仅文档提示用户不要直接打开 | 不改写入逻辑，只在报告说明风险 | 成本最低 | 不能防护实际风险；不满足安全评审 | 只作为补充说明 | 不应作为主方案 |

### 9.3 推荐方案

推荐 **方案 A：写入前文本字段统一转义**。

理由：

- 既防护表格公式注入，又不破坏数值字段的机器可读性。
- 可以集中在 reporting/scanner/candidates/bias_audit writer 边界处理，不污染算法对象。
- 测试成本低，适合作为实现前硬门禁。

### 9.4 最小防护契约

| 项 | 推荐要求 |
|---|---|
| 危险前缀 | 文本字段去除前导空白后的首字符为 `=`、`+`、`-`、`@`。 |
| 转义策略 | 前置单引号 `'`；保留原始内容其余部分。 |
| 适用字段 | `error_message`、`selection_reason`、`dedupe_reason`、`jq_notes`、`jq_difference_reason`、`impact_summary`、`warning`、`data_limitations`、所有自由文本原因字段。 |
| 不适用字段 | 数值指标、日期、枚举状态、布尔值、参数值。 |
| 测试 | 覆盖四类危险前缀、普通文本不变、数值字段不转字符串。 |

### 9.5 建议回写章节

| LLD | 章节 |
|---|---|
| STORY-007 | §8 技术设计细节：CSV writer 调用文本转义；§9 安全：公式注入防护；§10 测试：新增 `T-CSV-FORMULA-INJECTION-01`；§11 实施步骤：写入任务补转义。 |
| STORY-008 | §8/9/10/11 同步补候选 CSV 文本字段转义。 |
| STORY-012 | §8/9/10/11 同步补审计 CSV/Markdown 表格文本字段转义。 |

## 10. 落地顺序与门控

### 10.1 批量确认前必须修订

| 顺序 | Finding | 必修原因 | 目标 LLD |
|---|---|---|---|
| 1 | F-001 | W1 P0 组合会计不确定会导致净值、换手、成本和现金不可复现 | STORY-005，联动 STORY-006 |
| 2 | F-002 | W1 P0 调仓日集合不确定会导致单次回测、扫描和候选结果不可复现 | STORY-006，联动 STORY-007 |

### 10.2 可作为实现前硬门禁

| Finding | 门禁内容 | 适用范围 |
|---|---|---|
| F-003 | W3 任一 data_prep/normalizer/quality/loader 实现前必须关闭 source/interface registry 或使用 `UNRESOLVED` fail fast | STORY-009/010/011 |
| F-004 | 任一 STORY-004+ 实现前必须补最小日志契约和日志测试 | STORY-004 至 STORY-013 |
| F-005 | STORY-012 实现前必须固化 `AuditComparableRun` 输入、关联键和降级 schema | STORY-012，必要时标注 STORY-006/007/008 |
| F-007 | 任一 CSV/Markdown 表格 writer 实现前必须补文本字段转义 | STORY-007/008/012 |

### 10.3 可后置到低优先级 Story

| Finding | 后置条件 | 目标 Story |
|---|---|---|
| F-006 | 不影响 W1/W2；但 STORY-013 LLD 单独确认或实现前必须补公式 | STORY-013 |

## 11. 最终决策建议

建议选择：**批量确认前修订**。

理由：

1. F-001 与 F-002 同时落在 W1 P0 主路径，且会直接改变净值、指标和 60 组扫描结果，不能仅作为实现前口头门禁。
2. F-003、F-005、F-004、F-007 可以条件化处理，不需要回退到 Story planning；它们不改变 Story DAG、文件所有权或 Wave 划分。
3. F-006 属于 P2 策略扩展示例确定性问题，可后置到 STORY-013 单独 LLD 修订。

不建议选择“回退到 Story planning”：当前问题均可通过 LLD 章节修订或实现前硬门禁解决，没有发现依赖图无效、输出文件冲突或 Story 边界根本错误。

不建议直接“条件确认”整包：如果不先修 F-001/F-002，W1 主路径会把组合会计和调仓日算法留给实现者解释，违背 HLD 已确认口径和 LLD 可交接性要求。
