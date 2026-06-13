---
status: "approved-cp3"
version: "1.0"
change: "CR-046"
source_hld: "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
---

# Architecture Decisions CR046

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | meta-po | 初版 CR046 ADR，固化双目标策略交付框架、平台无关核心、runner 安装设计、验证分级和后续 CR 切分 |
| 1.1 | 2026-06-13 | meta-po | 用户通过 CP3，ADR-CR046-001..006 进入 approved-cp3 状态 |

## ADR-CR046-001 新增 FEAT-09 双目标策略交付框架

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | CR046 需要同时覆盖 QMT terminal 与 MiniQMT runner 策略交付框架，但不能把策略交付合同混入 QMT gateway 或 OMS runtime。 |
| Decision | 新增 FEAT-09，拥有 StrategyCoreContract、StrategyPackageContract、QMTTerminalTargetContract、MiniQMTRunnerTargetContract 和 StrategyValidationEvidence。 |
| Consequences | 后续 CR047 / CR049 / CR051 有稳定消费入口；FEAT-05/06 保持 gateway / trading governance 边界。 |
| Reversal | 若 MiniQMT 路线长期放弃，可将 FEAT-09 降级为 QMT-only 子能力。 |

## ADR-CR046-002 StrategyCoreContract 平台无关

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | 同一研究策略核心必须能面向 QMT terminal 与 MiniQMT runner。 |
| Decision | StrategyCoreContract 禁止导入 QMT、XtQuant、MiniQMT 或 broker SDK；平台能力只能出现在 target adapter 合同。 |
| Consequences | 双目标可复用性增强；需要静态 guardrail 检查。 |
| Reversal | 若后续用户明确选择 QMT-only，可另起 CR 改写合同。 |

## ADR-CR046-003 MiniQMT Runner 本轮只做安装设计

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | 用户当前没有 MiniQMT 权限，但要求框架包含 runner 组件安装。 |
| Decision | CR046 只定义 runner 安装目录、uv 管理、依赖隔离、配置模板、start/stop/status/kill switch、日志、upgrade/uninstall/rollback 和 install dry-run 方案。 |
| Consequences | 可提前冻结安装合同；无真实安装或连接证据。 |
| Reversal | MiniQMT 权限就绪后，CR049 另行授权实机 install / readonly 验证。 |

## ADR-CR046-004 验证证据分级

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | design pass、static pass、fixture pass 容易被误读为 terminal/runtime verified。 |
| Decision | StrategyValidationEvidence 必须显式区分 schema、static guardrail、fixture dry-run、QMT terminal shadow plan、MiniQMT install dry-run plan 和 runtime verified；CR046 不能产出 runtime verified。 |
| Consequences | 后续 CP7/CP8 声明更安全；文档需要解释证据层级。 |
| Reversal | 后续真实运行 CR 可新增 runtime verified 证据类型，但不得回写篡改 CR046 结论。 |

## ADR-CR046-005 首个具体策略交付后置 CR047

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | 用户明确要求 CR046 先定框架，策略交付后续再做。 |
| Decision | CR047-candidate 负责首个具体策略双目标交付；CR046 只提供合同、设计和验证框架。 |
| Consequences | 当前 CR 范围收敛；后续策略选择、参数冻结、运行授权可独立审查。 |
| Reversal | 若用户要求 CR046 内交付策略，需回退到 CR 影响分析并重发 CP2。 |

## ADR-CR046-006 研究框架完善后置 CR051

| 字段 | 内容 |
|---|---|
| Status | Proposed for CP3 |
| Context | 用户要求交易交付框架定稿后继续完善研究框架。 |
| Decision | CR051-candidate 消费 StrategyCoreContract、StrategyPackageContract 和 StrategyValidationEvidence，反向补齐研究输出元数据、order intents、风险假设和验证证据。 |
| Consequences | 研究框架完善不扩大 CR046；合同先行可减少返工。 |
| Reversal | 若 CP5 发现研究输出合同缺失阻断 CR046，可将相关项转为 CR046 内 technical-note 或 Spike。 |

## 不授权项

这些 ADR 不授权具体策略交付、QMT 终端运行验证、MiniQMT 连接、真实 runner 安装、账户查询、submit/cancel、simulation/live、provider fetch、lake write、catalog publish 或凭据读取。
