---
checkpoint_id: "CP2"
checkpoint_name: "CR051 Requirements / Research Lifecycle and Migration Baseline"
type: "auto_then_manual"
status: "approved"
owner: "host-orchestrator"
created_at: "2026-06-14T01:28:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-14T01:48:00+08:00"
auto_check_result: "process/checks/CP2-CR051-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  change_id: "CR-051"
  artifacts:
    - "process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md"
    - "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
    - "process/context/CP2-CR051-REQUIREMENT-CONTEXT.yaml"
    - "process/discussions/CP2-CR051-SCENARIO-DISCUSSION-LOG.md"
---

# CP2 CR051 Requirements / Research Lifecycle and Migration Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP2-CR051-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR051 active-lock 已由用户解除；迁移设计、Git 归档策略、归档边界和不授权项已进入需求基线。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP2-CR051-REQUIREMENT-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | compact |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档。 |
| 全文档读取扩展 | 1 次；用户新增项目整体迁移和 Git 归档要求，需要读取 CR051 与 HLD 草案并补充迁移设计。 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| STATE pending queue | `process/STATE.md.human_gate_decisions.pending_human_decisions[]` | scanned | 0 | 0 | 本轮从 CR051 blocked 状态、用户回复和 HLD 草案聚合。 |
| 正式 CR | `process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md` | scanned | 5 | 5 | 范围、架构、迁移、安全和后续 CR 分流均纳入决策。 |
| Context Capsule | `process/context/CP2-CR051-REQUIREMENT-CONTEXT.yaml` | scanned | 5 | 5 | 与本 Decision Brief 决策一致。 |
| Discussion log | `process/discussions/CP2-CR051-SCENARIO-DISCUSSION-LOG.md` | scanned | 5 | 5 | SGQ-CR051-01..05 均映射到 DQ-CR051-01..05。 |
| 自动预检结果 | `process/checks/CP2-CR051-REQUIREMENTS-BASELINE.md` | scanned | 0 | 0 | 无阻断项。 |
| 下游正式产物 | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | scanned | 5 | 5 | HLD 的 architecture gray areas、迁移章节和 ADR 候选进入决策。 |
| 用户显式选择题 | 当前对话 | scanned | 2 | 2 | 用户允许推进 CR051，并要求项目整体迁移和 Git 归档。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CR051-01 | scope | CR051 是否定位为策略研究生命周期和项目迁移设计 CR，而不是具体策略实现或 runtime CR？ | 是。CR051 只冻结生命周期、taxonomy、归档、仓库拓扑、PC 使用方式、迁移方案和后续 CR 路线。 | A: 将多因子 proof cycle 并入 CR051；B: 只做文档，不设计迁移。 | 推荐方案让后续 CR052+ 有稳定框架；A 会让 CR051 过大且难验证；B 无法支撑用户要求的项目整体迁移。 | 本轮不产出可交易策略，也不迁移外部 archive。 | 若用户需要立即研究多因子，回退并拆出 CR052；若迁移暂缓，保留 CR051 为设计基线。 |
| DQ-CR051-02 | architecture | 仓库拓扑是否采用一个主 Git 仓库 + 外部 research archive / market data lake / broker archive？ | 是。保持 `local_backtest` 为 canonical 主仓库，Git 只存代码、文档、schema、小型 redacted fixture、manifest 和 pointer。 | A: 拆多仓库；B: 单仓库保存全部 artifact。 | 推荐方案迁移成本最低且安全边界清晰；A 当前运维成本过高；B 高风险污染 Git。 | 需要后续 guardrail 防止大 artifact / 敏感事实进入 Git。 | 若多人权限隔离或交易生产权限成为硬约束，再评估多仓库。 |
| DQ-CR051-03 | architecture | 本项目整体迁移是否采用阶段化 Git 归档与清单化机械迁移？ | 是。先 baseline commit / 可选 tag，再 CP3 设计冻结，再 inventory，再 mechanical move，再 externalization，再验证。 | A: 直接一次性搬目录；B: 只整理文档不迁移结构。 | 推荐方案可审计、可回滚；A 难以定位失败；B 不满足用户迁移目标。 | 后续会产生较大文件移动 diff，需要单独提交和路径引用检查。 | 若 CP3 未通过，停止迁移；若机械迁移失败，回退到 pre-file-move 归档点。 |
| DQ-CR051-04 | security | 是否继续禁止凭据、账户事实、完整市场数据、大型研究 artifact、broker facts 进入 Git？ | 是。Git 只保留 schema、docs、summary、redacted fixture、manifest、checksum 和 pointer。 | A: 将小型研究输出全部留在 Git；B: 将 archive 放入 Git LFS。 | 推荐方案最保守，符合当前安全边界；A 需要逐项大小/敏感性审查；B 引入新工具和权限治理成本。 | 迁移阶段必须做 inventory 和 forbidden content scan。 | 若某 artifact 需要留 Git，必须在 M2 inventory 中标为 redacted-small 并有 owner。 |
| DQ-CR051-05 | follow_up_tracking | 是否把 CR052..CR056 作为 CR051 后续路线，且全部受 CR051 gate 阻塞？ | 是。CR052 多因子 proof cycle，CR053 事件型，CR054 ML Spike，CR055 消费桥，CR056 反馈闭环。 | A: 只登记 CR052；B: 将 CR053+ 放入 backlog 不编号。 | 推荐方案让路线可追踪；A 会遗漏策略族扩展；B 降低状态机可查询性。 | 后续 CR 仍需单独 CP2/CP3/CP5 和运行授权；不自动启动。 | CR051 CP8 后可重排优先级或取消候选。 |

### 用户需决策事项

| 决策 ID | 用户需决策事项 |
|---|---|
| DQ-CR051-01 | 是否批准 CR051 只做框架、迁移和治理设计，不做具体策略 / runtime。 |
| DQ-CR051-02 | 是否批准一个主 Git 仓库 + 外部 research archive / lake / broker archive 的拓扑。 |
| DQ-CR051-03 | 是否批准项目整体迁移采用 Git 归档点 + inventory + 机械迁移 + 验证的阶段化方案。 |
| DQ-CR051-04 | 是否确认 Git 禁止保存凭据、账户事实、完整市场数据、大型 artifact 和 broker facts。 |
| DQ-CR051-05 | 是否批准 CR052..CR056 作为后续候选路线，均由 CR051 gate 阻塞。 |

### 用户视角复述与不授权项

如果你回复 `approve`，表示你接受以上 5 项推荐方案：CR051 进入 standard 工作流，当前只授权需求 / 场景基线进入 CP3 架构评审，不授权实现、外部归档搬迁或任何真实运行。

如果你回复 `approve`，不表示授权以下 14 项禁止操作：

| 不授权项 | 当前状态 |
|---|---|
| CR046 CP7 验证或关闭 | not-authorized |
| CR047 / CR048 / CR049 启动 | not-authorized |
| 交付具体交易策略或可交易策略包 | not-authorized |
| QMT / MiniQMT runtime、连接、传输、导入 | not-authorized |
| 账户 / 资金 / 持仓 / 委托 / 成交查询 | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
| 外部 archive 实际复制 / 删除 / 搬迁 | not-authorized |
| 删除仓库历史文件或清空历史过程证据 | not-authorized |
| git push、删除分支、重写历史 | not-authorized |
| 创建真实交易 PC package 并传输 | not-authorized |

自动终验授权：false。CP2 approved 不构成 CP3、CP5、CP6、CP7、CP8 自动通过，也不构成任何运行授权。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | 通过 | `process/checks/CP2-CR051-REQUIREMENTS-BASELINE.md` | 用户回复“同意”，按 `approve` 处理。 |
| 待人工决策项已收集 | 通过 | 本文件 Decision Brief | DQ-CR051-01..05 推荐方案均被接受。 |
| 不授权边界已用户可见 | 通过 | 本文件“不授权项” | CP2 approve 不构成任何运行、外部归档搬迁、Git push 或交易授权。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR051 只做框架 / 迁移 / 治理设计 | 通过 | DQ-CR051-01 | 接受推荐方案。 |
| 2 | 是否接受一个主 Git 仓库 + 外部 archive/lake 拓扑 | 通过 | DQ-CR051-02 | 接受推荐方案。 |
| 3 | 是否接受阶段化迁移和 Git 归档点 | 通过 | DQ-CR051-03 | 接受推荐方案。 |
| 4 | 是否确认 Git 禁止敏感和大型事实进入 | 通过 | DQ-CR051-04 | 接受推荐方案。 |
| 5 | 是否接受 CR052..CR056 后续路线 | 通过 | DQ-CR051-05 | 接受推荐方案。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户明确 approve / 修改 / reject | 通过 | 当前对话：用户回复“同意。” | 按 `approve` 处理。 |
| 无阻断项 | 通过 | CP2 自动预检 | PASS。 |
| 不授权边界明确 | 通过 | 本文件“不授权项” | CP2 只放行 CP3 设计。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR051 正式 CR | `process/changes/CR-051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK-2026-06-14.md` | 通过 | 进入 CP3 设计。 |
| CR051 HLD 草案 | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 通过 | 进入 CP3 设计；用户补充硬件现状需纳入 HLD。 |
| CP2 Context Capsule | `process/context/CP2-CR051-REQUIREMENT-CONTEXT.yaml` | 通过 | ready。 |
| CP2 自动预检 | `process/checks/CP2-CR051-REQUIREMENTS-BASELINE.md` | 通过 | PASS。 |
| CP2 场景讨论日志 | `process/discussions/CP2-CR051-SCENARIO-DISCUSSION-LOG.md` | 通过 | 已覆盖 SGQ-CR051-01..05。 |

## 人工审查结果

- 结论：`approved`
- reviewed_by: user
- reviewed_at: 2026-06-14T01:48:00+08:00
- 备注：用户回复“同意”，接受 DQ-CR051-01..05 推荐方案；同时补充硬件现状：NAS 含 512G SSD、4T RAID 硬盘、14T 机械硬盘；交易主机 512G SSD；主力研究主机 2T SSD。该补充作为 CP3 架构设计输入，不构成 NAS 挂载、数据复制、外部归档搬迁、provider/lake/publish、Git push 或交易运行授权。
