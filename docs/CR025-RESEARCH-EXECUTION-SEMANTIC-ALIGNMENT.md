# CR-025 Research Execution Semantic Alignment

## 1. Purpose

CR-025 是 research execution semantic alignment 文档与合同集合，不是 QMT route activation，不是 simulation / live runbook，也不是多因子研究主框架建设。它把 lightweight baseline、Backtrader optional execution semantic reference、semantic diff、`order_intent_draft_v1`、Backtrader no-copy guardrail、no-real-operation safety 和后续路线边界放在同一处说明，供用户、后续 CR owner、meta-qa 和 meta-doc 复核。

本文件只解释已经完成的 CR025-S01..S05 离线合同和 CR025-S06 文档边界。它不授权依赖安装、Backtrader run、Backtrader source copy、broker、QMT / MiniQMT / XtQuant、provider fetch、lake write、broker lake write、publish、simulation/live、credential read、FactorSpec / FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包、Qlib / Alphalens / vectorbt / vnpy.alpha 集成。

## 2. What CR-025 Produces

| Output | Current role | Boundary |
|---|---|---|
| clean feed gate / backend selector | 保持 lightweight default，显式 Backtrader reference 只能在门控满足时返回结构化状态 | 默认路径 `import_attempted=false`；缺依赖或未选择时 structured unavailable。 |
| semantic diff | 比较 lightweight baseline 与 Backtrader-style execution semantic reference 的执行语义差异 | baseline / reference 双轨；reference unavailable 是合法结果；不是 production truth。 |
| `order_intent_draft_v1` | 把 target portfolio、semantic diff evidence、lineage、limitations 和 raw execution policy 写成后续 QMT route 可审查草案 | not order；not authorization；consumer later-gated。 |
| Backtrader module reference | 记录 `reference_only`、`adapt_interface`、`migration_candidate`、`exclude` 分类 | optional dependency、lazy import、no-copy、`migration_candidate=[]`、no runtime default。 |
| no-real-operation safety | 用 fixture-only 测试和静态扫描证明真实操作计数为 0 | 不读取凭据、不运行 Backtrader、不启动 QMT、不写湖、不 publish。 |
| docs / follow-up handoff | 给 README、USER-MANUAL 和后续 CR owner 提供入口 | CR-020..CR-024、CR-030 都必须独立授权。 |

## 3. What CR-025 Does Not Authorize

CR-025 的 CP5、CP6、CP7、Story `verified`、本专题文档、README 入口或 USER-MANUAL 说明均不提供真实运行许可。

| Scope | Authorization state | Required future route |
|---|---|---|
| dependency install / dependency change | `not_authorized` | 另起 CR 或依赖 Spike；重新通过 CP2 / CP3 / CP5。 |
| Backtrader run / samples / tests / runtime | `not_authorized` | 只有后续明确批准 optional runtime CR 后才可评估。 |
| Backtrader source copy / source migration | `not_authorized` | 新 CR + legal review + CP3 risk acceptance + CP5 implementation authorization。 |
| QMT / MiniQMT / XtQuant / broker | `not_authorized` | CR-020..CR-024 独立推进，且每次真实 run 需要 per-run authorization。 |
| provider fetch / lake write / broker lake write / publish | `not_authorized` | 独立数据或交易 CR；不能从 CR-025 继承。 |
| simulation / live / live_readonly / small_live / scale_up | `not_authorized` | Stage gate、CP 链路、per-run authorization、reconciliation 和 kill switch 证据齐全后才可申请。 |
| credential read | `not_authorized` | 真实凭据不得进入文档、日志、检查点或 fixture；后续授权也只记录脱敏 ref。 |
| multifactor research framework | `not_authorized` | CR-030 或后续正式 CR；CR-025 只提供执行语义边界输入。 |

## 4. CP3 Decision Traceability

| Decision ID | Topic | CR-025 decision | Evidence path | Current state |
|---|---|---|---|---|
| DQ-CP3-CR025-01 | Backtrader 定位 | Backtrader 只作为 optional execution semantic reference / design reference；lightweight 仍是默认 baseline。 | ADR-074、HLD §34.1 / §34.4 | `resolved`; not default runtime。 |
| DQ-CP3-CR025-02 | 模块矩阵 / no-copy | 采用 `reference_only` / `adapt_interface` / `migration_candidate` / `exclude`；`migration_candidate=[]`。 | ADR-075、S04 reference doc | `resolved`; source migration count 0。 |
| DQ-CP3-CR025-03 | GPLv3 governance | 默认 no-copy；任何源码级例外需 legal review、CP3 和 CP5 双门控。 | ADR-076、S04 / S05 CP7 | `resolved`; no-copy。 |
| DQ-CP3-CR025-04 | clean feed / semantic diff | semantic diff 保留 baseline / reference 双轨，输出 unavailable、limitations 和 diff reason。 | S01 / S02 CP7 | `resolved`; not production truth。 |
| DQ-CP3-CR025-05 | order intent / QMT boundary | `order_intent_draft_v1` 是草案，不是订单，不授权 QMT；consumer 是 CR-020..CR-024 later-gated。 | ADR-077、HLD-QMT §18、S03 CP7 | `resolved`; not order。 |
| DQ-CP3-CR025-06 | no-real-operation | CP3 / CP5 / CP6 / CP7 都只授权离线合同和静态验证，不授权真实操作。 | CP5 batch、S05 CP7 | `resolved`; real operation counters 0。 |

## 5. Story Traceability

| Story | Output | User-facing meaning | Not authorized by this Story |
|---|---|---|---|
| CR025-S01-clean-feed-gate-backend-selector | clean feed gate、backend selector、structured unavailable | 默认 lightweight；Backtrader reference 只有显式选择和门控满足时才可作为状态对象 | dependency change、Backtrader run、provider fetch、lake write、credential read。 |
| CR025-S02-semantic-diff-schema-artifact | semantic diff schema / artifact contract | 执行语义比较，包含 baseline、reference、unavailable、limitations、diff reason | production truth、simulation-ready、QMT admission pass、factor tear sheet、IC report。 |
| CR025-S03-order-intent-draft-qmt-boundary | `order_intent_draft_v1` builder / validator contract | later-gated handoff candidate；`qmt_allowed=false`、`not_authorization=true` | QMT call、MiniQMT call、XtQuant import/call、order submit、order cancel、account query、broker lake write、service start。 |
| CR025-S04-backtrader-module-reference-no-copy-guardrail | Backtrader module reference / no-copy doc | optional reference、no-copy、no-source-migration、no-vendored-source、`migration_candidate=[]` | source copy、samples/tests/datas copy、live store migration、line/metaclass runtime migration。 |
| CR025-S05-no-real-operation-safety-verification | fixture-only safety tests and static scan | 证明 forbidden-operation counters 全部为 0 | 真实 Backtrader run、QMT environment、provider、lake、credential、multifactor framework implementation。 |
| CR025-S06-route-docs-and-follow-up-handoff | 本文档、README 入口、USER-MANUAL 边界 | 汇总 CR-025 语义边界与后续路线 | dependency install、runtime activation、QMT route activation、multifactor framework delivery。 |

## 6. Semantic Diff Contract

semantic diff 是 research comparison artifact。它以 lightweight baseline 为基线，以 Backtrader optional semantic reference 或 structured unavailable 为 reference 轨道。两个轨道必须同时保留，不能把 reference 覆盖成 baseline，也不能把 reference 结果提升为 production truth。

| Required field group | Meaning | Failure / limitation handling |
|---|---|---|
| metadata | `schema_version`、baseline backend、reference backend、generated time、source run、lineage | 缺 lineage 时 fail closed。 |
| availability | baseline / reference availability、blocked reason、limitations | reference unavailable 合法，必须写明 reason。 |
| fills | fill count、fill timing、partial flag、price source、rounding policy | 不能声明真实成交。 |
| cash / cost | starting cash、ending cash、commission、tax、slippage、cash reconciliation | 只做研究比较，不写 broker truth。 |
| portfolio | holdings delta、position sizing delta、turnover delta、net value delta | 不作为策略准入包。 |
| timeline / explanation | event timeline、diff reason、severity、qmt relevance | 不触发 QMT handoff 外的操作。 |

semantic diff 的限制标签必须包含以下含义：

- `not_production_truth`: 不是 production truth。
- `not_simulation_ready`: 不是 simulation-ready 证据。
- `not_qmt_admission_pass`: 不是 QMT admission pass。
- `not_factor_tear_sheet`: 不是 factor tear sheet、IC report 或策略准入包。
- `reference_unavailable_allowed`: reference unavailable 是可审计状态，不是裸异常。

## 7. `order_intent_draft_v1` Contract

`order_intent_draft_v1` 是从 research output 到后续 QMT route 的离线草案。它只把 target portfolio、semantic diff evidence、lineage、limitations、raw execution policy 和 cost config reference 组织为可审查字段。

| Contract field | Required value / rule | Boundary |
|---|---|---|
| `schema_version` | `order_intent_draft_v1` | 未知版本 blocked。 |
| `execution_price_policy` | `raw` | 非 raw hard block，不进入 handoff。 |
| `qmt_allowed` | `false` | 固定不授权 QMT。 |
| `not_authorization` | `true` | draft 不是订单，不是运行授权。 |
| `consumer` | `CR-020..CR-024 later-gated` | 后续 consumer 必须独立 CR / CP。 |
| `data_lineage_ref` | required | 缺失时 fail closed。 |
| `limitations` | required | 缺失时 fail closed。 |
| sensitive fields | forbidden | 账户号、token、cookie、session、private key、交易密码等不得进入 draft。 |

如果用户或后续系统把 draft 当作可提交订单、gateway input、simulation submit、live submit、broker lake write 或 account query trigger，处理结果必须是 blocked，并回到 CR-020..CR-024 的独立门控。

## 8. Backtrader Boundary

CR-025 中 Backtrader 的当前边界是 optional dependency / lazy import / no-copy / no runtime default。它只服务 execution semantic reference，不承接多因子研究主框架。

| Category | Current handling | Allowed in CR-025 | Forbidden in CR-025 |
|---|---|---|---|
| `reference_only` | feed、broker、order、trade、position、commission、slippage、analyzer、observer、writer、strategy lifecycle 等概念参考 | 描述语义、字段和差异维度 | 复制类、函数、runtime、samples、tests、datas。 |
| `adapt_interface` | clean feed、semantic diff、cost / slippage / fill assumption、target order concept | 用本项目自有合同 clean-room 定义字段和行为 | 移植 Backtrader internals。 |
| `migration_candidate` | `migration_candidate=[]` | 当前无源码级候选 | fork、vendor、裁剪、改写、源码级迁移。 |
| `exclude` | live store、外部 feeds、line/metaclass runtime、indicator library migration、samples/tests/datas copy、真实 broker integration | 作为风险说明 | 进入实现、测试 fixture 或运行路径。 |

Backtrader 不是 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包的实现入口。若后续需要真实 Backtrader optional runtime，对应 CR 必须重新确认依赖、license、回归矩阵、输入 clean feed 和输出 limitations。

## 9. No-Real-Operation Table

| Operation class | Current count | CR-025 status | Evidence / expected handling |
|---|---:|---|---|
| LLD authorization as runtime authorization | 0 | `not_authorized` | LLD / CP5 只批准设计与离线实现。 |
| implementation expanding runtime scope | 0 | `not_authorized` | 实现不得扩大 Story owner 或文件范围。 |
| dependency change | 0 | `not_authorized` | `pyproject.toml` / `uv.lock` diff 必须为 0。 |
| Backtrader run | 0 | `not_authorized` | 不运行 backend、samples、tests 或 runtime。 |
| Backtrader source copy | 0 | `not_authorized` | no-copy、no-source-migration、no-vendored-source。 |
| broker operation | 0 | `not_authorized` | 不接真实 broker 或 live store。 |
| QMT / MiniQMT / XtQuant | 0 | `not_authorized` | 不启动 gateway，不调用 API。 |
| provider fetch | 0 | `not_authorized` | 不联网抓取 provider。 |
| lake write | 0 | `not_authorized` | 不写 raw / manifest / canonical / quality / catalog / gold。 |
| broker lake write | 0 | `not_authorized` | 不写 broker lake。 |
| publish | 0 | `not_authorized` | 不发布 current pointer。 |
| simulation/live | 0 | `not_authorized` | 不运行 simulation、live_readonly、small_live、scale_up。 |
| credential read | 0 | `not_authorized` | 不读取、打印、记录或保存任何凭据。 |
| service start / port bind | 0 | `not_authorized` | 不启动 gateway、broker、provider 或外部服务。 |
| multifactor framework implementation | 0 | `not_authorized` | 不实现 FactorSpec / IC / RankIC 等研究闭环能力。 |
| Qlib / Alphalens / vectorbt / vnpy.alpha integration | 0 | `not_authorized` | 只作为 CR-030 候选参考方向。 |

## 10. CR-020..CR-024 QMT Route

CR-020..CR-024 是真实 QMT route 的独立后续链路。CR-025 可以提供 semantic evidence 和 `order_intent_draft_v1` 作为 later-gated 输入，但不继承任何运行授权。

| Future CR | Route role | Relationship to CR-025 | Required independent gates |
|---|---|---|---|
| CR-020 | QMT Windows gateway health / deployment admission | 可以审查 `order_intent_draft_v1` 字段和 blocked reason | independent CR、CP2 / CP3 / CP5、stage gate、service boundary、per-run authorization if any runtime is requested。 |
| CR-021 | simulation account admission | 只能消费已审查 draft 和 risk / OMS evidence | independent CR、simulation stage gate、per-run authorization、kill switch、reconciliation。 |
| CR-022 | live-readonly admission | 只能做只读路线候选 | independent CR、readonly allowlist、redaction、per-run authorization。 |
| CR-023 | small-live admission | 只在前置 route verified 后申请 | independent CR、risk gate、capital limit、manual approval、rollback plan。 |
| CR-024 | scale-up admission | 只在 small-live 稳定后申请 | independent CR、research maturity gate、risk limits、reconciliation evidence。 |

README、USER-MANUAL、CR-025 CP7 PASS 或本文件均不把 CR-020..CR-024 的任一阶段从 later-gated 改成 authorized。

## 11. CR-030 Multifactor Research Framework Candidate

CR-030 是多因子研究框架借鉴与研究闭环标准化候选，不是 CR-025 的交付项。CR-030 可以消费 CR-025 的 clean feed、semantic evidence、limitations 和 order intent boundary，但不能继承依赖变更、provider fetch、lake write、publish、Backtrader runtime、QMT / MiniQMT / XtQuant、simulation/live 或 credential read 授权。

| Candidate context | Follow-up CR only boundary |
|---|---|
| FactorSpec | 后续定义因子输入字段、窗口、PIT / available_at、辅助数据依赖和失败路径。 |
| FactorRunSpec | 后续定义 universe、label window、参数、缓存、manifest 和复跑合同。 |
| IC / RankIC | 后续定义横截面统计、窗口、分组、benchmark 和解释口径。 |
| 分层收益 | 后续定义分层、换手、覆盖率、group analysis 和失效条件。 |
| 多因子组合 | 后续定义合成、权重、正交化 / 中性化、容量和风险暴露。 |
| 实验追踪 | 后续定义 experiment manifest、artifact lineage、复跑入口和结果注册。 |
| 策略准入包 | 后续定义研究结果进入 simulation / QMT 前的 evidence、limitations 和 handoff。 |

候选参考对象只作为正式 CR 前的调研方向，正式启动时必须重新验证 license、维护状态、依赖体量、数据接口假设、A 股适配性、clean-room 借鉴边界和安全限制。

| Candidate reference | Possible learning direction | Current boundary |
|---|---|---|
| Qlib | data handler、dataset、processor、workflow recorder、ML factor workflow | 不安装、不运行、不写 provider path；CR-026 可作为窄范围候选。 |
| Alphalens | factor tear sheet、IC / RankIC、分层收益、turnover、group analysis | 不直接引入依赖或复制实现。 |
| vectorbt | 向量化扫描、多参数 / 多资产广播、walk-forward、性能分析 | 不替代现有 engine truth。 |
| Zipline Reloaded | event time、pipeline、asset、calendar、order lifecycle | 只作为时间和执行语义参考。 |
| QuantConnect LEAN | broker / fill / fee / slippage / portfolio / order model 分层 | 不引入大型运行时。 |
| RQAlpha | A 股规则、配置化运行、mod 扩展、simulation / live 语义 | license / 非商业边界需重验。 |
| vn.py / vnpy.alpha | 国内交易生态、alpha dataset、model、paper account、gateway 思路 | 不集成 gateway，不授权实盘。 |
| PyBroker | ML strategy、walk-forward、bootstrap、caching | 只参考实验组织。 |
| bt | 组合构建 DSL，如 select / weigh / rebalance | 不复制接口。 |
| Backtrader | feed / broker / order / commission / slippage / analyzer 执行语义 | 已由 CR-025 承接为 execution semantic reference；不是多因子研究主框架。 |

## 12. Failure Handling

| User or downstream request | Required response |
|---|---|
| “用 CR-025 直接启动 gateway” | blocked；启动 CR-020 或对应后续 CR，重新过 CP 和授权。 |
| “把 semantic diff 当 simulation-ready 证据” | blocked；改回 research comparison 和 limitations。 |
| “把 `order_intent_draft_v1` 当订单提交” | blocked；draft is not order，not authorization。 |
| “把 Backtrader reference 结果当 production truth” | blocked；lightweight baseline 与 reference 双轨保留。 |
| “复制 Backtrader 源码或样例” | blocked；`migration_candidate=[]`，需新 CR + legal review + CP3 / CP5。 |
| “在 CR-025 内建设 FactorSpec / IC / RankIC / 策略准入包” | blocked；路由到 CR-030 或后续正式 CR。 |
| “在文档里写真实账号、token、cookie、session、private key 或交易密码” | blocked；只能记录脱敏 ref 和授权摘要。 |

## 13. Verification Entry

S06 后续验证应保持离线、fixture-only 和静态扫描。推荐验证范围：

| Verification | Expected result |
|---|---|
| CR025 组合回归测试 | S01..S05 合同测试全部 PASS。 |
| docs boundary scan | CR025-S01..S06、DQ-CP3-CR025-01..06、CR-020..CR-024、CR-030、no-real-operation 表均可追溯。 |
| forbidden authorization scan | 正向运行授权语义命中为 0。 |
| dependency diff | `pyproject.toml` / `uv.lock` diff 为 0。 |
| private / credential scan | 凭据示例、真实私有路径、账户值、token 值、cookie、session、private key、交易密码命中为 0。 |

## 14. Close-out Boundary

CR-025 可关闭的范围是 research execution semantic alignment：clean feed gate、semantic diff、`order_intent_draft_v1`、Backtrader no-copy / optional reference、no-real-operation safety、README / USER-MANUAL 入口和后续路线说明。

CR-025 关闭后仍不授权真实 QMT、Backtrader runtime、provider fetch、lake write、publish、simulation/live、credential read 或多因子研究主框架。任何后续真实运行或研究框架建设都必须通过独立 CR、独立 CP、明确文件 owner、验证入口和用户授权。
