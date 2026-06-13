---
checkpoint_id: "CP3"
checkpoint_name: "CR046 QMT / MiniQMT Dual-Target Framework HLD Review"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-13T22:03:22+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-13T22:23:42+08:00"
auto_check_result: "process/checks/CP3-CR046-HLD-CONSISTENCY.md"
auto_final_authorization: false
target:
  phase: "solution-design"
  change_id: "CR-046"
  artifacts:
    - "process/context/CP3-CR046-DESIGN-CONTEXT.yaml"
    - "docs/design/BLUEPRINT.md"
    - "docs/design/DOMAIN-MAP.md"
    - "docs/design/DEPENDENCY-MAP.md"
    - "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
    - "docs/design/ARCHITECTURE-DECISION-CR046.md"
    - "process/discussions/CP3-CR046-HLD-DISCUSSION-LOG.md"
    - "process/checks/CP3-CR046-DISCUSSION-CHECKPOINT.json"
---

# CP3 CR046 QMT / MiniQMT Dual-Target Framework HLD Review 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP3-CR046-HLD-CONSISTENCY.md` | PASS | 0 | 蓝图、领域、依赖、HLD、ADR、context capsule 和不授权边界已就绪。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP3-CR046-DESIGN-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | compact |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档。 |
| 全文档读取扩展 | 1 次；用户明确要求判断蓝图等设计文件是否需要刷新，并同意继续推进 CP3。 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| CP2 checkpoint | `process/checkpoints/CP2-CR046-REQUIREMENTS-BASELINE.md` | scanned | 6 | 0 | CP2 已 approved；作为 CP3 前置，不重复发起。 |
| Blueprint / Domain / Dependency | `docs/design/BLUEPRINT.md` / `DOMAIN-MAP.md` / `DEPENDENCY-MAP.md` | scanned | 6 | 6 | FEAT-09、对象、规则和禁止依赖进入 CP3 决策。 |
| CR046 HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | scanned | 6 | 6 | Architecture Gray Areas 和 ADR 候选均映射到 DQ-CP3-CR046-01..06。 |
| CR046 ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` | scanned | 6 | 6 | ADR-CR046-001..006 映射为 CP3 决策。 |
| CP3 discussion log / checkpoint | `process/discussions/CP3-CR046-HLD-DISCUSSION-LOG.md` / `process/checks/CP3-CR046-DISCUSSION-CHECKPOINT.json` | scanned | 6 | 6 | Architecture Gray Areas 已处理。 |
| CP3 自动预检 | `process/checks/CP3-CR046-HLD-CONSISTENCY.md` | scanned | 0 | 0 | 无阻断项。 |
| 用户显式选择题 | 当前对话 | scanned | 1 | 0 | 用户已同意 CP2 framework-first；本轮只发起 CP3 设计确认。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP3-CR046-01 | architecture | 是否接受新增 FEAT-09 承载 QMT / MiniQMT 双目标策略交付框架？ | 接受；FEAT-05/06 继续只负责 gateway 和交易治理。 | A: 并入 FEAT-05；B: 并入 FEAT-06。 | 推荐方案边界最清晰；A/B Feature 数更少但容易把合同误读为 runtime 或 OMS 能力。 | 影响蓝图、Story 拆解、后续 CR047/049/051 消费入口。 | 若 MiniQMT 路线长期放弃，可降级为 QMT-only 子能力。 |
| DQ-CP3-CR046-02 | architecture | 是否接受 StrategyCoreContract 平台无关并禁止导入 QMT / XtQuant / MiniQMT？ | 接受；平台能力只在 target adapter 合同出现。 | A: core 允许 QMT API；B: 只设计 QMT-only core。 | 推荐方案支撑双目标；A/B 简化当前实现但破坏复用和边界。 | 影响静态 guardrail、策略包合同和后续策略交付。 | 若后续用户选择 QMT-only，另起 CR 改写合同。 |
| DQ-CP3-CR046-03 | implementation | MiniQMT runner 本 CR 是否只做安装设计和 install dry-run 方案？ | 接受；覆盖目录、uv、依赖隔离、配置、日志、kill switch、upgrade/uninstall/rollback。 | A: 完全不设计 runner；B: 真实安装 / 连接。 | 推荐方案满足用户要求且不触碰真实环境；A 覆盖不足；B 越权。 | 影响 CR049 实机 install / readonly 验证前置。 | MiniQMT 权限就绪后另起 CR049。 |
| DQ-CP3-CR046-04 | risk_acceptance | 是否接受 StrategyValidationEvidence 证据分级，且 CR046 不声明 runtime verified？ | 接受；区分 schema/static/fixture/dry-run plan/runtime verified。 | A: fixture pass 即 runtime-ready；B: 不设计验证框架。 | 推荐方案降低误读风险；A 高风险；B 无法支撑后续策略交付。 | 影响 CP7/CP8 声明和用户手册。 | 后续真实运行 CR 可新增 runtime verified 证据。 |
| DQ-CP3-CR046-05 | follow_up_tracking | 是否接受首个具体策略交付继续后置 CR047？ | 接受；CR046 只交付合同和框架。 | A: 并入 CR046；B: 暂不追踪。 | 推荐方案保持范围收敛；A 扩大当前 CR；B 丢失下一步。 | 影响 Story 范围和交付预期。 | 若用户要求当前交付策略，回退重开 CP2。 |
| DQ-CP3-CR046-06 | follow_up_tracking | 是否接受研究框架完善继续后置 CR051？ | 接受；CR051 消费 StrategyCoreContract 和 StrategyValidationEvidence。 | A: 并入 CR046；B: 暂不追踪。 | 推荐方案先冻结交易交付合同；A 当前范围过大；B 丢失研究框架缺口。 | 影响研究输出元数据、order intents 和准入证据后续完善。 | 若 CP5 发现研究合同阻断 CR046，可转 Spike 或 technical-note。 |

### 用户需决策事项

| 决策 ID | 用户需决策事项 |
|---|---|
| DQ-CP3-CR046-01 | 是否批准新增 FEAT-09 作为双目标策略交付框架边界。 |
| DQ-CP3-CR046-02 | 是否批准 StrategyCoreContract 平台无关，禁止导入 QMT / XtQuant / MiniQMT。 |
| DQ-CP3-CR046-03 | 是否批准 MiniQMT runner 本轮只做安装设计和 install dry-run 方案。 |
| DQ-CP3-CR046-04 | 是否批准验证证据分级，且 CR046 不声明 runtime verified。 |
| DQ-CP3-CR046-05 | 是否批准首个具体策略交付继续后置 CR047。 |
| DQ-CP3-CR046-06 | 是否批准研究框架完善继续后置 CR051。 |

### 用户视角复述与不授权项

如果你回复 `approve`，表示你接受以上 6 项 CP3 推荐方案：CR046 采用独立 FEAT-09，策略核心平台无关，MiniQMT runner 本轮只做安装设计，验证证据分级，具体策略交付后置 CR047，研究框架完善后置 CR051。

如果你回复 `approve`，不表示授权以下 14 项禁止操作：

| 不授权项 | 当前状态 |
|---|---|
| 交付具体交易策略或可交易策略包 | not-authorized |
| 执行 QMT 终端 shadow / 模拟盘运行验证 | not-authorized |
| 真实安装 MiniQMT runner | not-authorized |
| 连接 MiniQMT / XtQuant / QMT 外部 Python API | not-authorized |
| 订阅真实行情或启动 runner runtime | not-authorized |
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
| 查询资金 / cash | not-authorized |
| 查询持仓 / position | not-authorized |
| 查询委托 / order | not-authorized |
| 查询成交 / fill / execution report | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |

自动终验授权：false。CP3 approved 不构成 CP5、CP6、CP7、CP8 自动通过，也不构成任何真实运行授权。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP2 已 approved | PASS | `process/checkpoints/CP2-CR046-REQUIREMENTS-BASELINE.md` | 用户已接受 framework-first 范围。 |
| CP3 HLD / ADR 已产出 | PASS | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md`；`docs/design/ARCHITECTURE-DECISION-CR046.md` | draft-for-cp3，待本门禁确认。 |
| Architecture Gray Areas 已处理 | PASS | `process/discussions/CP3-CR046-HLD-DISCUSSION-LOG.md`；`process/checks/CP3-CR046-DISCUSSION-CHECKPOINT.json` | 6 个灰区已进入 Decision Brief。 |
| 自动预检 PASS | PASS | `process/checks/CP3-CR046-HLD-CONSISTENCY.md` | 阻断项 0。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受新增 FEAT-09 独立承载双目标策略交付框架 | 通过 | DQ-CP3-CR046-01 | 用户回复“同意”，按 `approve` 处理。 |
| 2 | 是否接受 StrategyCoreContract 平台无关 | 通过 | DQ-CP3-CR046-02 | 用户回复“同意”，按 `approve` 处理。 |
| 3 | 是否接受 MiniQMT runner 只做安装设计和 install dry-run 方案 | 通过 | DQ-CP3-CR046-03 | 用户回复“同意”，按 `approve` 处理。 |
| 4 | 是否接受验证证据分级且 CR046 不声明 runtime verified | 通过 | DQ-CP3-CR046-04 | 用户回复“同意”，按 `approve` 处理。 |
| 5 | 是否接受具体策略交付后置 CR047 | 通过 | DQ-CP3-CR046-05 | 用户回复“同意”，按 `approve` 处理。 |
| 6 | 是否接受研究框架完善后置 CR051 | 通过 | DQ-CP3-CR046-06 | 用户回复“同意”，按 `approve` 处理。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 人工结论为 approved / changes_requested / rejected | 通过 | 当前对话 | 用户回复“同意”，按 `approve` 处理。 |
| 若 approved，CR046 可进入 story-planning / CP4 | 通过 | 本文件 | 仍不授权 implementation 或 runtime。 |
| 若 changes_requested，按修改点重发 CP3 | N/A | 当前对话 | 无修改请求。 |
| 若 rejected，CR046 回退或关闭 | N/A | 当前对话 | 未拒绝。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CP3 Context Capsule | `process/context/CP3-CR046-DESIGN-CONTEXT.yaml` | 通过 | ready |
| CP3 自动预检 | `process/checks/CP3-CR046-HLD-CONSISTENCY.md` | 通过 | PASS |
| Blueprint refresh | `docs/design/BLUEPRINT.md` | 通过 | v1.1 |
| Domain map refresh | `docs/design/DOMAIN-MAP.md` | 通过 | v1.1 |
| Dependency map refresh | `docs/design/DEPENDENCY-MAP.md` | 通过 | v1.1 |
| HLD index refresh | `docs/design/HLD.md` | 通过 | v1.1 |
| CR046 HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` | 通过 | approved-cp3 |
| ADR index refresh | `docs/design/ARCHITECTURE-DECISION.md` | 通过 | v1.1 |
| CR046 ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` | 通过 | approved-cp3 |
| CP3 discussion log | `process/discussions/CP3-CR046-HLD-DISCUSSION-LOG.md` | 通过 | ready-for-cp3 |
| CP3 discussion checkpoint | `process/checks/CP3-CR046-DISCUSSION-CHECKPOINT.json` | 通过 | PASS |

## 人工审查结果

- 结论：`approved`
- reviewed_by: user
- reviewed_at: 2026-06-13T22:23:42+08:00
- 备注：用户回复“同意”，按 `approve` 处理；接受 DQ-CP3-CR046-01..06 推荐方案，允许 CR046 进入 story-planning / CP4。该批准不授权具体策略交付、QMT 运行验证、MiniQMT 连接、MiniQMT 真实安装、账户查询、submit/cancel、simulation/live、provider/lake/publish 或凭据读取。
