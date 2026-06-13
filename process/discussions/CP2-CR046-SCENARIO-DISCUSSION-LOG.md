---
cr_id: CR-046
discussion_id: CP2-CR046-SCENARIO-DISCUSSION
status: pending-cp2-review
owner: meta-po
created_at: 2026-06-13T21:46:39+08:00
---

# CP2 CR046 场景讨论日志

## 背景

用户明确要求继续推进 CR046，并重新收窄为 framework-first：先定 QMT / MiniQMT 双目标策略交付框架、验证框架、MiniQMT runner 安装设计和策略包契约；不做具体策略交付、不做 QMT 运行验证、不连接 MiniQMT、不 submit/cancel。用户还要求研究完交易交付框架后继续完善研究框架。

## Scenario Gray Areas

| 问题 ID | 问题 | 推荐方案 | 当前结论 | 影响 |
|---|---|---|---|---|
| SGQ-CR046-01 | CR046 是框架 CR 还是具体策略交付 CR？ | 采用 framework-first，只交付框架与验证设计。 | 待 CP2 approve | 防止提前生成具体策略或真实运行计划。 |
| SGQ-CR046-02 | 是否同时保留 QMT 终端和 MiniQMT runner 两个目标？ | 保留双目标；QMT terminal 是当前可用主线，MiniQMT runner 是未来路线。 | 待 CP2 approve | 决定策略核心合同和 target adapter 边界。 |
| SGQ-CR046-03 | MiniQMT runner 安装是否进入本 CR？ | 纳入安装设计和 dry-run 方案，不执行真实安装或连接。 | 待 CP2 approve | 冻结 Windows 目录、uv、配置、日志、kill switch、rollback。 |
| SGQ-CR046-04 | 当前是否授权真实运行、账户查询或 submit/cancel？ | 不授权。 | 待 CP2 approve | 所有真实运行和交易动作保持 0。 |
| SGQ-CR046-05 | 首个具体策略交付是否后置？ | 是，登记为 CR047-candidate。 | 待 CP2 approve | 保持框架与策略交付分离。 |
| SGQ-CR046-06 | 研究框架完善是否并入本 CR？ | 不并入，登记为 CR051-candidate。 | 待 CP2 approve | 先冻结交易交付框架，再反向约束研究输出。 |

## 冻结场景草案

| 场景 ID | 场景 | 预期 |
|---|---|---|
| SC-CR046-01 | 双目标策略核心合同 | QMT terminal target 和 MiniQMT runner target 可消费同一策略核心合同。 |
| SC-CR046-02 | QMT terminal target 交付形态 | 定义入口、配置、输入输出、日志、shadow 报告和导入说明；不运行终端。 |
| SC-CR046-03 | MiniQMT runner 安装设计 | 定义 Windows 目录、uv、依赖隔离、配置、日志、kill switch 和 dry-run；不真实安装。 |
| SC-CR046-04 | 验证框架 | 覆盖 fixture/schema、QMT shadow 计划、MiniQMT install dry-run 计划和后续 runtime gate。 |
| SC-CR046-05 | 后续 CR 分流 | CR047..CR051 候选清晰记录阻塞前置和不授权边界。 |

## 不授权项

| 项目 | 状态 |
|---|---|
| 具体交易策略交付 | not-authorized |
| QMT 终端运行验证 | not-authorized |
| MiniQMT / XtQuant 连接 | not-authorized |
| 账户 / 资金 / 持仓 / 委托 / 成交查询 | not-authorized |
| submit / cancel / simulation / live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| 凭据、token、account_id、账号、密码、session、cookie、private key 读取或记录 | not-authorized |
