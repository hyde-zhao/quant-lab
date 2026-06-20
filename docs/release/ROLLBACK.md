---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-101
---

# CR099 Rollback

## 1. 回滚摘要

| 项目 | 内容 |
|---|---|
| 回滚目标版本 | `cr098-runner-readonly-integration-ready-with-risk` |
| 回滚范围 | CR099 HLD、checker、collector、tests、feature docs、release docs、process evidence |
| 是否涉及数据恢复 | no |
| 是否存在不可回滚项 | no |
| 决策人 | human |

## 2. 回滚触发条件

| Trigger ID | 条件 | 监控 / 证据 | 决策人 |
|---|---|---|---|
| RB-CR099-01 | CR099 collector 合同被确认不适合 runner readonly smoke | 用户反馈 / review | human |
| RB-CR099-02 | release 文档误导为授权额外 runtime / NAS / trading | CP8 review / user feedback | human |
| RB-CR099-03 | 后续真实 evidence gate 决定采用不同 schema | future CR decision | human |

## 3. 回滚步骤

| Step | 操作 | 前置条件 | 验证 | 风险 |
|---|---|---|---|---|
| 1 | 撤销 CR099 新增 HLD / checker / collector / tests / feature docs / release docs / process evidence | 用户明确要求回滚 | `git diff --check` / targeted tests 不再引用 CR099 | 回滚会丢失真实 readonly smoke 证据链 |
| 2 | 将 STATE / CR-INDEX 回退到 CR098 follow-up candidate 或标记 CR099 cancelled/superseded | 新 CR 或人工门禁批准 | `meta-flow check cr-tracking` 仅剩既有状态 | 需避免破坏历史追溯 |
| 3 | 保留 CR097 / CR098 closure 和 CR099 runtime evidence 审计事实 | 始终保留审计索引 | CR097 / CR098 / CR099 过程记录可读 | 删除审计事实会降低可追溯性 |

## 4. 回滚验证

| 验证项 | 方法 | 结果 |
|---|---|---|
| 安装 / 加载恢复 | N/A，本轮无 installer / service install | N/A |
| 状态 / 配置恢复 | 检查 `process/STATE.md`、`process/changes/CR-INDEX.yaml` | pending only if rollback requested |
| 敏感边界 | 确认未读取 Windows `.env` / account originals / NAS / trading | PASS in current delivery |

## 5. 不可回滚项

| 对象 | 是否存在 | 原因 | 处理 |
|---|---|---|---|
| runtime side effect | no | 本轮只读调用；未写外部状态 | N/A |
| NAS side effect | no | 本轮未访问 NAS | N/A |
| credential / account read side effect | no | 未输出凭据或账户原文 | N/A |

## CR100 Addendum - Rollback

| Trigger ID | 条件 | 回滚入口 | 说明 |
|---|---|---|---|
| RB-CR100-01 | fake exchange 合同需要撤回 | 文件级回滚 CR100 新增代码、脚本、测试和文档 | 无真实 NAS 外部副作用 |
| RB-CR100-02 | forbidden filename 规则误拒合法包 | 回修 `package_exchange.py` 并补 allowlist 测试 | 不需要真实 NAS |
| RB-CR100-03 | 后续真实 NAS gate 采用不同 manifest | 标记 CR100 superseded 或追加兼容层 | 保留 CR100 离线证据 |

CR100 未访问真实 NAS、未读取凭据、未启动 runtime，也未执行交易或 provider/lake/catalog publish，因此没有外部系统回滚动作。

## CR101 Addendum - Rollback

| Trigger ID | 条件 | 回滚入口 | 说明 |
|---|---|---|---|
| RB-CR101-01 | target taxonomy 或 adapter boundary 被后续设计取代 | 文件级回滚 CR101 相关 HLD、台账、checker/schema 文档和测试改动 | 保留 CR101 审计事实，后续 CR 应标记 superseded/reframed |
| RB-CR101-02 | 后续真实 QMT / MiniQMT / NAS gate 采用不同 evidence schema | 新 CR 中追加兼容层或标记 CR101 evidence contract superseded | 不需要回滚外部系统，因为 CR101 未连接真实系统 |
| RB-CR101-03 | release 文档误导为真实 runtime ready | 修订 release docs、baseline、CR-INDEX 和 handoff | 必须继续保留不授权边界 |

CR101 未访问真实 NAS、未读取凭据、未启动 QMT/MiniQMT/XtQuant/gateway runtime，也未执行交易或 provider/lake/catalog publish，因此没有外部系统回滚动作。
