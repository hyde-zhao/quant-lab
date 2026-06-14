---
checkpoint_id: "CP3"
checkpoint_name: "CR051 HLD / Research Lifecycle Migration Architecture Review"
type: "auto_then_manual"
status: "approved"
owner: "host-orchestrator"
created_at: "2026-06-14T01:52:00+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-14T08:03:59+08:00"
auto_check_result: "process/checks/CP3-CR051-HLD-CONSISTENCY.md"
target:
  phase: "solution-design"
  change_id: "CR-051"
  artifacts:
    - "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
    - "process/context/CP3-CR051-DESIGN-CONTEXT.yaml"
---

# CP3 CR051 HLD / Research Lifecycle Migration Architecture Review 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP3-CR051-HLD-CONSISTENCY.md` | PASS | 0 | HLD v0.5 覆盖研究生命周期、项目迁移、Git 归档、当前硬件冷热分层、项目命名、CP3 确认记录和不授权边界。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP3-CR051-DESIGN-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | compact |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档。 |
| 全文档读取扩展 | 1 次；需要读取 HLD v0.5 以确认硬件分层、迁移架构、项目命名策略和 CP3 确认记录。 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| STATE pending queue | `process/STATE.md.human_gate_decisions.pending_human_decisions[]` | scanned | 5 | 5 | CP3 DQ 已从 HLD / 硬件输入聚合。 |
| CP2 checkpoint | `process/checkpoints/CP2-CR051-REQUIREMENTS-BASELINE.md` | scanned | 5 | 0 | CP2 DQ 已 approved，作为 CP3 输入。 |
| Context Capsule | `process/context/CP3-CR051-DESIGN-CONTEXT.yaml` | scanned | 5 | 5 | 与本 Decision Brief 决策一致。 |
| 自动预检结果 | `process/checks/CP3-CR051-HLD-CONSISTENCY.md` | scanned | 0 | 0 | 无阻断项。 |
| 下游正式产物 | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | scanned | 7 | 6 | 仓库拓扑、硬件分层、交易 PC 边界、迁移阶段、项目命名和不授权边界进入决策。 |
| 用户显式选择题 | 当前对话 | scanned | 2 | 2 | 用户补充 NAS / PC 现状，已转为硬件分层架构决策；用户指定项目新名 `quant-lab`，已转为命名迁移决策。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP3-CR051-01 | architecture | 是否确认 CR051 首版继续采用一个主代码仓库 + 外部 archive/lake/broker archive？ | 是，正式项目名 / 未来主仓库名采用 `quant-lab`，当前 `local_backtest` 作为 legacy alias；外部根承载大 artifact / 数据 / broker facts。 | A: 拆多仓库；B: Git LFS / 单仓库全量保存。 | 推荐方案最适合当前单人 / 小团队和迁移成本；拆仓库当前过早；Git 全量保存污染风险高。 | 后续要做 path / forbidden content guardrail。 | 多用户权限隔离或交易生产发布成熟后再评估拆仓。 |
| DQ-CP3-CR051-02 | architecture | 是否采用基于当前硬件的冷热分层？ | 是：研究主机 2T SSD 做活跃 workspace；NAS 512G SSD 做热缓存 / package exchange；NAS 4T RAID 做 research archive 主层；NAS 14T HDD 做冷归档；交易主机 512G SSD 只做 package 消费和小型运行证据。 | A: 全部 archive 放研究主机；B: 全部 archive 放 NAS 14T；C: 交易主机也保存完整 archive。 | 推荐方案兼顾性能、容量和风险；A 容量和备份风险高；B 热读写慢；C 扩大交易主机风险面。 | 需要后续通过配置表达路径，不写死私有挂载。 | 若 NAS 性能或可用性不足，可临时把 active workspace 放研究主机，archive 延后同步。 |
| DQ-CP3-CR051-03 | security | 是否确认交易主机不是研究环境？ | 是，交易主机默认只消费 zip + sha256 + manifest + docs bundle 或只读 checkout。 | A: 交易主机 clone 完整研究仓库；B: 交易主机也挂载 research archive。 | 推荐方案权限最小；完整 clone / archive 会增加误运行研究脚本和敏感数据暴露风险。 | 后续策略包交付必须有 checksum 和人工 gate。 | 隔离测试机可临时 read-only checkout，但不得默认化。 |
| DQ-CP3-CR051-04 | implementation | 是否确认迁移采用 Git 归档点 + inventory + mechanical move + verification？ | 是，机械移动与语义修改分提交。 | A: 一次性大迁移；B: 只改文档不迁移。 | 推荐方案可回滚和审计；一次性迁移失败定位难；只改文档无法落地用户目标。 | 会带来较多路径引用修正和验证工作。 | CP3 未通过不迁移；机械移动失败回退到 pre-file-move。 |
| DQ-CP3-CR051-05 | runtime_authorization | 是否确认 CP3 approve 不授权任何真实操作？ | 是，不授权 NAS mount / copy / delete、provider/lake/publish、QMT/MiniQMT、交易、凭据、Git push。 | A: 同时授权 NAS inventory；B: 同时授权 archive migration。 | 推荐方案保持设计门和执行门分离；A/B 均需要独立 runtime_authorization 和清单。 | CP3 只冻结设计，后续 CP5/CP6 才能讨论实现。 | 用户另行授权后再启动 inventory / migration。 |
| DQ-CP3-CR051-06 | architecture | 是否确认项目正式名称从 `local_backtest` 迁移为 `quant-lab`？ | 是。`quant-lab` 作为正式项目名 / 仓库名 / 新文档名；`local_backtest` 作为 legacy alias 和历史审计名保留。 | A: 继续使用 `local_backtest`；B: 使用更长名称如 `quant-strategy-lab`；C: 立即全量替换历史文件中的旧名。 | 推荐方案简洁且覆盖范围不再局限于回测；继续旧名会误导范围；长名称不如 `quant-lab` 简洁；全量替换历史文件会污染审计链。 | 后续迁移需更新 README、USER-MANUAL、`pyproject.toml`、新环境变量、Windows 默认路径和路径 guardrail；历史 `process/` 不批量替换。 | 若后续发现名称冲突，可在 CP4 前重开命名决策；若实现阶段发现兼容成本过高，可保留 `local_backtest` 为更长过渡期 alias。 |

### 用户需决策事项

| 决策 ID | 用户需决策事项 |
|---|---|
| DQ-CP3-CR051-01 | 是否确认单主仓库 + 外部 archive/lake/broker archive。 |
| DQ-CP3-CR051-02 | 是否确认基于当前 NAS / PC 的冷热分层。 |
| DQ-CP3-CR051-03 | 是否确认交易主机只做 package 消费和小型运行证据。 |
| DQ-CP3-CR051-04 | 是否确认阶段化迁移和 Git 归档点。 |
| DQ-CP3-CR051-05 | 是否确认 CP3 仍不授权真实操作。 |
| DQ-CP3-CR051-06 | 是否确认正式项目名为 `quant-lab`，旧名 `local_backtest` 只作为 legacy alias 和历史审计名保留。 |

### 用户视角复述与不授权项

如果你回复 approve，表示你接受以上 6 项推荐方案，允许 CR051 进入 story-planning / CP4；不表示授权以下禁止操作。

| 不授权项 | 当前状态 |
|---|---|
| NAS mount / scan / copy / delete / migration execution | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| QMT / MiniQMT runtime、传输、导入、连接 | not-authorized |
| 账户 / 资金 / 持仓 / 委托 / 成交查询 | not-authorized |
| 下单 / 撤单 / simulation / live | not-authorized |
| 凭据、token、account_id、账号、密码、session、cookie、private key 读取或记录 | not-authorized |
| git push、删除分支、重写历史 | not-authorized |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | 通过 | `process/checks/CP3-CR051-HLD-CONSISTENCY.md` | 用户回复“同意”，按 `approve` 处理。 |
| HLD v0.5 可读 | 通过 | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 接受 HLD v0.5 作为 CR051 story-planning / CP4 输入。 |
| 待人工决策项已收集 | 通过 | 本文件 Decision Brief | 接受 DQ-CP3-CR051-01..06 推荐方案。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受单主仓库 + 外部 archive/lake/broker archive | 通过 | DQ-CP3-CR051-01 | 接受推荐方案：未来主仓库名采用 `quant-lab`，当前 `local_backtest` 为 legacy alias；外部 archive / lake / broker archive 分离。 |
| 2 | 是否接受硬件冷热分层 | 通过 | DQ-CP3-CR051-02 | 接受推荐方案：研究主机 2T SSD、NAS 512G SSD、NAS 4T RAID、NAS 14T HDD、交易主机 512G SSD 分层使用。 |
| 3 | 是否接受交易主机非研究环境 | 通过 | DQ-CP3-CR051-03 | 接受推荐方案：交易主机只消费 package / checksum / manifest / docs 和小型运行证据。 |
| 4 | 是否接受阶段化迁移和 Git 归档点 | 通过 | DQ-CP3-CR051-04 | 接受推荐方案：Git 归档点 + inventory + mechanical move + verification。 |
| 5 | 是否确认不授权真实操作 | 通过 | DQ-CP3-CR051-05 | CP3 approve 仍不授权目录重命名、NAS 操作、provider/lake/publish、QMT/MiniQMT、交易、凭据或 Git push。 |
| 6 | 是否接受项目正式命名为 `quant-lab` 并保留 `local_backtest` legacy alias | 通过 | DQ-CP3-CR051-06 | 接受推荐方案：`quant-lab` 为正式项目名，`local_backtest` 为 legacy alias 和历史审计名。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户明确 approve / 修改 / reject | 通过 | 当前对话：用户回复“同意” | 按 `approve` 处理。 |
| 无阻断项 | 通过 | CP3 自动预检 | PASS，阻断项 0。 |
| 不授权边界明确 | 通过 | 本文件“不授权项” | CP3 只放行 story-planning / CP4，不授权真实操作。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR051 HLD | `docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md` | 通过 | HLD v0.5 approved；可作为 CP4 输入。 |
| CP3 Context Capsule | `process/context/CP3-CR051-DESIGN-CONTEXT.yaml` | 通过 | ready；包含硬件分层与 `quant-lab` 命名决策。 |
| CP3 自动预检 | `process/checks/CP3-CR051-HLD-CONSISTENCY.md` | 通过 | PASS。 |

## 人工审查结果

- 结论：`approved`
- reviewed_by: user
- reviewed_at: 2026-06-14T08:03:59+08:00
- 备注：用户回复“同意”，接受 DQ-CP3-CR051-01..06 推荐方案：单主仓库 + 外部 archive/lake/broker archive、基于当前硬件的冷热分层、交易主机非研究环境、阶段化迁移和 Git 归档点、CP3 不授权真实操作、正式项目名采用 `quant-lab` 且 `local_backtest` 作为 legacy alias。该确认只授权进入 CR051 story-planning / CP4；不授权目录重命名、NAS mount / scan / copy / delete / migration execution、provider/lake/publish、QMT/MiniQMT、账户查询、交易、凭据读取、Git push、远端仓库改名或历史文件批量替换。
