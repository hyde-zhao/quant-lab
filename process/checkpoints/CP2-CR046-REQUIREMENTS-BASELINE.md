---
checkpoint_id: "CP2"
checkpoint_name: "CR046 Requirements / Dual-Target Framework Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-13T21:46:39+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-13T22:03:22+08:00"
auto_check_result: "process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  change_id: "CR-046"
  artifacts:
    - "process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md"
    - "process/context/CP2-CR046-REQUIREMENT-CONTEXT.yaml"
    - "process/USE-CASES.md"
    - "process/REQUIREMENTS.md"
---

# CP2 CR046 Requirements / Dual-Target Framework Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR046 formal CR、context capsule、产品基线增量、后续台账和不授权边界已就绪。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP2-CR046-REQUIREMENT-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | compact |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档。 |
| 全文档读取扩展 | 1 次；用户明确要求读取 CR046 正文、STATE 和 CR-INDEX，并需核对 legacy 产品基线路径。 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| STATE pending queue | `process/STATE.md.human_gate_decisions.pending_human_decisions[]` | scanned | 0 | 0 | 启动前无 CR046 pending gate；本轮从 CR / capsule / 用户指令聚合。 |
| 正式 CR | `process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md` | scanned | 6 | 6 | 范围、架构、实现边界、安全和 follow-up tracking 均纳入决策。 |
| Context Capsule | `process/context/CP2-CR046-REQUIREMENT-CONTEXT.yaml` | scanned | 6 | 6 | 与 CR 决策一致。 |
| Discussion log / checkpoint | `process/discussions/CP2-CR046-SCENARIO-DISCUSSION-LOG.md` / `process/checks/CP2-CR046-DISCUSSION-CHECKPOINT.json` | scanned | 6 | 6 | SGQ-CR046-01..06 均映射到 DQ-CR046-01..06。 |
| 自动预检结果 | `process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md` | scanned | 0 | 0 | 无阻断项。 |
| 下游正式产物 | `process/USE-CASES.md` / `process/REQUIREMENTS.md` | scanned | 0 | 0 | 已按 CR046 增量更新为 draft；等待 CP2 确认。 |
| 用户显式选择题 | 当前对话 | scanned | 1 | 1 | 用户要求 framework-first，不授权运行、连接或 submit/cancel。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CR046-01 | scope | CR046 是否改为 QMT + MiniQMT 双目标策略交付与验证框架，而不是具体策略交付？ | 是，本轮先交付框架和验证框架。 | A: 继续交付一个 QMT 策略包；B: 直接进入 MiniQMT runner 实现。 | 推荐方案先统一合同和验证门禁，避免后续每个策略重复设计；A 会让双目标不一致；B 会被权限和安全门禁阻塞。 | 本轮不会产生可交易具体策略。 | CP8 后启动 CR047 做首个策略交付。 |
| DQ-CR046-02 | architecture | 是否要求后续研究策略同时支持 QMT 终端和 MiniQMT runner？ | 是，双目标为标准交付合同。 | A: 只支持 QMT；B: 只支持 MiniQMT。 | 推荐方案兼顾当前 QMT 可用和未来 runner 自动化；代价是框架复杂度更高。 | 需要明确可复用策略核心和 adapter 边界。 | 若 MiniQMT 权限长期不可得，可在后续 CR 降级为 QMT-only。 |
| DQ-CR046-03 | implementation | MiniQMT runner 组件安装是否纳入本 CR？ | 是，纳入安装设计和 dry-run 方案，不执行真实安装 / 连接。 | A: 完全不纳入；B: 直接实现可运行 runner。 | 安装设计可提前冻结目录、uv、依赖、配置和日志规范；B 会被权限和安全门禁阻塞。 | install dry-run 方案不等于 runtime 授权。 | MiniQMT 权限开通后另起实机验证 CR。 |
| DQ-CR046-04 | security | 本 CR 是否继续禁止 QMT 终端运行验证、真实账户查询、submit/cancel、live 和 MiniQMT 连接？ | 是，仅框架 / 验证框架设计 / fixture 设计。 | A: 授权 QMT shadow；B: 授权 MiniQMT 只读连接；C: 授权最小模拟盘提交。 | 推荐方案风险最低，符合先框架后策略交付；备选均需逐 run 授权、策略包和脱敏证据。 | 无法产生真实运行证据，只产生设计和静态验证计划证据。 | 后续 runtime_authorization gate 开启。 |
| DQ-CR046-05 | follow_up_tracking | 首个具体策略交付是否作为 CR047 候选进入后续台账？ | 是，CR047-candidate。 | A: 在 CR046 内交付首个策略；B: 暂不登记。 | 推荐方案保持框架与策略交付分离；A 会扩大当前 CR；B 会丢失下一步追踪。 | 后续需要再次 CP2/CP3/CP5 确认具体策略。 | CR046 CP8 通过后启动。 |
| DQ-CR046-06 | follow_up_tracking | 研究框架完善是否作为 CR051 候选进入后续台账？ | 是，CR051-candidate。 | A: 并入 CR046；B: 暂不登记。 | 推荐方案先冻结交易交付框架，再反向完善研究框架；A 会让当前 CR 过大；B 会丢失研究输出合同缺口。 | CR051 需要消费 CR046 输出合同。 | CR046 CP8 通过后启动。 |

### 用户需决策事项

| 决策 ID | 用户需决策事项 |
|---|---|
| DQ-CR046-01 | 是否批准 CR046 只做 framework-first，不在本轮交付具体策略。 |
| DQ-CR046-02 | 是否批准 QMT terminal + MiniQMT runner 作为后续策略标准双目标。 |
| DQ-CR046-03 | 是否批准 MiniQMT runner 安装设计和 dry-run 方案进入本 CR，但不真实安装或连接。 |
| DQ-CR046-04 | 是否确认本 CR 继续不授权真实运行、账户查询、submit/cancel、simulation/live。 |
| DQ-CR046-05 | 是否批准首个具体策略交付进入 CR047-candidate。 |
| DQ-CR046-06 | 是否批准研究框架完善进入 CR051-candidate。 |

### 用户视角复述与不授权项

如果你回复 `approve`，表示你接受以上 6 项推荐方案：CR046 进入 standard 工作流，当前只授权 framework-first 的需求 / 场景基线进入 CP3 架构设计，不授权任何具体策略交付或真实运行。

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

自动终验授权：false。CP2 approved 不构成 CP3、CP5、CP6、CP7、CP8 自动通过，也不构成任何运行授权。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | PASS | `process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md` | 用户回复“好的同意，继续推进”，按 `approve` 处理。 |
| 待人工决策项已收集 | PASS | 本文件 Decision Brief | DQ-CR046-01..06 推荐方案均被接受。 |
| 不授权边界已用户可见 | PASS | 本文件“不授权项” | CP2 approve 不构成任何运行授权。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR046 限定为 framework-first | 通过 | DQ-CR046-01 | 接受推荐方案。 |
| 2 | 是否接受 QMT terminal + MiniQMT runner 双目标 | 通过 | DQ-CR046-02 | 接受推荐方案。 |
| 3 | 是否接受 MiniQMT runner 安装设计进入本 CR 但不真实安装 / 连接 | 通过 | DQ-CR046-03 | 接受推荐方案。 |
| 4 | 是否确认当前不授权真实运行、账户查询、submit/cancel、simulation/live | 通过 | DQ-CR046-04 | 不授权边界保持有效。 |
| 5 | 是否接受首个具体策略交付后置为 CR047-candidate | 通过 | DQ-CR046-05 | 接受推荐方案。 |
| 6 | 是否接受研究框架完善后置为 CR051-candidate | 通过 | DQ-CR046-06 | 接受推荐方案。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户明确 approve / 修改 / reject | 通过 | 当前对话：用户回复“好的同意，继续推进” | 按 `approve` 处理。 |
| 无阻断项 | 通过 | CP2 自动预检 | PASS。 |
| 不授权边界明确 | 通过 | 本文件“不授权项” | CP2 只放行 CP3 设计。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR046 正式 CR | `process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md` | 通过 | 进入 CP3 设计。 |
| CR046 follow-up tracking | `process/changes/CR-046-FOLLOW-UP-TRACKING-2026-06-13.md` | 通过 | CR047 / CR051 候选保留。 |
| USE-CASES 增量 | `process/USE-CASES.md` | 通过 | v1.15 confirmed。 |
| REQUIREMENTS 增量 | `process/REQUIREMENTS.md` | 通过 | v1.16 confirmed。 |
| CP2 Context Capsule | `process/context/CP2-CR046-REQUIREMENT-CONTEXT.yaml` | 通过 | ready。 |
| CP2 自动预检 | `process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md` | 通过 | PASS。 |

## 人工审查结果

- 结论：`approved`
- reviewed_by: user
- reviewed_at: 2026-06-13T22:03:22+08:00
- 备注：用户回复“好的同意，继续推进”，接受 DQ-CR046-01..06 推荐方案。CP2 通过仅授权 CR046 framework-first 需求 / 场景基线进入 CP3 设计；不授权具体策略交付、QMT 运行验证、MiniQMT 连接、真实安装、账户查询、submit/cancel、simulation/live、provider/lake/publish 或凭据读取。
