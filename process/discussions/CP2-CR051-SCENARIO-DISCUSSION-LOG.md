---
cr_id: CR-051
discussion_id: CP2-CR051-SCENARIO-DISCUSSION
status: ready-for-cp2-review
owner: host-orchestrator
created_at: 2026-06-14T01:28:00+08:00
---

# CP2 CR051 场景讨论日志

## 背景

用户确认可以推进 CR051，并补充关键约束：CR051 的设计必须考虑当前 `local_backtest` 项目整体迁移；项目改造完成后，当前项目会全部迁移为 CR051 设计后的结构，包括 Git 归档。

本日志记录用户可见场景确认。由于当前平台未被用户显式授权启动子 agent，本轮由 Host Orchestrator 主进程整理，不声明 meta-pm 独立完成。

## Scenario Gray Areas

| 问题 ID | 问题 | 推荐方案 | 当前结论 | 影响 |
|---|---|---|---|---|
| SGQ-CR051-01 | CR051 是否可在 CR046 挂起期间推进？ | 可以。CR046 保持 paused CP6 恢复点；CR051 只做研究生命周期和迁移设计，不推进 CR046 CP7。 | 用户已回复“同意，你可以推进 CR051 了” | 解除 active-lock 阻塞，但不恢复 CR046。 |
| SGQ-CR051-02 | 当前项目迁移是否必须纳入 CR051 设计？ | 必须纳入。CR051 需定义迁移目标结构、Git 归档点、阶段门禁和回滚策略。 | 用户明确要求“这次项目改造完成后我会将本项目全部迁移为你设计后的结构。包括 git 归档。” | HLD 增加迁移章节；后续 CP3/CP5 必须覆盖迁移。 |
| SGQ-CR051-03 | 仓库拓扑采用单仓库还是多仓库？ | 首版采用一个主代码仓库 + 外部 research archive / market data lake / broker archive。 | 等待 CP2 approve | 降低迁移复杂度，并保持当前仓库为 canonical 工具项目根。 |
| SGQ-CR051-04 | Git 是否保存研究和交易大 artifact？ | 不保存。Git 只存代码、文档、schema、小型 redacted fixture、manifest 和 pointer。 | 等待 CP2 approve | 防止真实数据、凭据、broker facts 或大型模型污染仓库。 |
| SGQ-CR051-05 | 是否现在启动多因子完整证明周期或具体策略？ | 不启动。CR052 才做多因子完整证明周期，CR053+ 再扩展策略类型。 | 等待 CP2 approve | 防止 CR051 膨胀为研究实现和交易交付混合 CR。 |

## 冻结场景草案

| 场景 ID | 场景 | 预期 |
|---|---|---|
| SC-CR051-01 | 研究生命周期治理 | 信息源、idea、立项、研究协议、run、验证、准入、消费、反馈 / 退役形成统一状态机。 |
| SC-CR051-02 | 策略 taxonomy | 多因子、事件型、择时、技术型、统计套利、ML、增强指数、tick / 高频 Spike 均有扩展入口。 |
| SC-CR051-03 | 归档分层 | Git、research archive、market data lake、broker / trading archive、strategy package exchange 各自边界清晰。 |
| SC-CR051-04 | 当前项目迁移 | 先 Git 归档，再设计冻结，再 inventory，再机械迁移，再外置 archive，再验证和 CP8。 |
| SC-CR051-05 | 交易 PC 消费 | 交易 PC 默认只消费 release package / read-only checkout，不作为研究开发环境。 |
| SC-CR051-06 | 后续 CR 分流 | CR052 多因子 proof cycle、CR053 事件型、CR054 ML Spike、CR055 消费桥、CR056 反馈闭环均后置。 |

## 不授权项

| 项目 | 状态 |
|---|---|
| CR046 CP7 验证或关闭 | not-authorized |
| CR047 / CR048 / CR049 启动 | not-authorized |
| QMT / MiniQMT runtime、连接、传输、导入 | not-authorized |
| 账户 / 资金 / 持仓 / 委托 / 成交查询 | not-authorized |
| submit / cancel / simulation / live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| 凭据、token、account_id、账号、密码、session、cookie、private key 读取或记录 | not-authorized |
| 外部 archive 实际复制 / 删除 / 搬迁 | not-authorized |
| git push、删除分支、重写历史 | not-authorized |
