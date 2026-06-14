---
status: "candidate"
version: "1.0"
change_id: "CR-053"
source_gate: "CP8"
created_at: "2026-06-14T13:05:00+08:00"
release_decision: "READY_WITH_RISK"
---

# CR-053 Follow-up Tracking

> 本台账只记录 CR053 CP8 后续候选，不自动创建正式 CR，不授权真实迁移、NAS、数据湖、交易、凭据读取或 git remote 操作。host-orchestrator 回收后可按用户确认同步 `STATE.md.cr_tracking`。

## 1. 汇总

| 项目 | 内容 |
|---|---|
| 当前 CR053 结论建议 | `READY_WITH_RISK`，静态 migration inventory / dry-run 交付就绪。 |
| 风险接受候选 | `R-CR053-01`、`R-CR053-02`、`R-CR053-03` |
| 后续候选数量 | 4 |
| 不授权项 | 9 项，见 CP8 checkpoint 和 release context。 |

## 2. 风险接受候选

| Risk ID | 分流类别 | 决策类型 | 推荐处理 | 备选方案 | owner | 验收标准 | 重访条件 |
|---|---|---|---|---|---|---|---|
| R-CR053-01 | risk_acceptance | risk_acceptance | 接受真实 NAS path / capacity / permission 未验证，不阻断 CR053 静态 close。 | 备选：NOT_READY，要求先做 NAS read-only inventory；不推荐，因为会扩大 CR053 授权范围。 | human / host-orchestrator | CP8 用户明确接受；后续真实迁移前有独立 NAS 授权。 | 用户要求真实 NAS 迁移或 CR060+ 启动。 |
| R-CR053-02 | risk_acceptance | risk_acceptance | 接受 backup / restore rehearsal 和 rollback_ref planned-only，不阻断 CR053 静态 close。 | 备选：NOT_READY，要求先生成 git bundle / restore evidence；不推荐，因为 CR053 未授权真实备份恢复。 | human / host-orchestrator | CP8 用户明确接受；CR058/CR060+ 前不得绕过 rollback_ref。 | CR058 repo-local move 或 CR060+ NAS 实迁启动前。 |
| R-CR053-03 | risk_acceptance | follow_up_tracking | 接受 CR058 manual review / rollback gates 为未来前置。 | 备选：立即合并到 CR053 返工；不推荐，因为会扩大当前 close gate 范围。 | host-orchestrator | CR058 启动前有独立 checkpoint 和门禁。 | 用户明确启动 CR058。 |

## 3. 后续候选

| Candidate ID | 分流类别 | 决策类型 | 推荐处理 | 备选方案 | owner | 验收标准 | 重访条件 |
|---|---|---|---|---|---|---|---|
| FU-CR053-01 | follow_up_candidate | follow_up_tracking | 将 CR058 repo-local mechanical migration 保持为后续候选，不自动启动。 | 备选 A：本轮直接启动 CR058；不推荐，缺新的人工范围确认。备选 B：取消 CR058；适用于用户放弃 rename / path rewrite。 | host-orchestrator / human | 若转正式 CR，必须有 CP2/CP3/CP5/CP8、rollback_ref、candidate list、preserve-audit allowlist。 | 用户确认要推进 README / USER-MANUAL / future-facing docs rewrite。 |
| FU-CR053-02 | follow_up_candidate | runtime_authorization | 将 CR060+ NAS / archive real migration 保持为后续候选，不自动启动。 | 备选 A：先做 NAS read-only inventory spike；适用于需要路径事实。备选 B：取消 NAS 实迁，仅保留 Git-only。 | host-orchestrator / human | 独立 NAS 授权、路径白名单、容量/权限验证、restore rehearsal、failure manifest。 | 用户提供 NAS 路径并要求真实迁移。 |
| FU-CR053-03 | follow_up_candidate | runtime_authorization | 将独立 data lake migration CR 保持为候选，不从 CR053 继承授权。 | 备选 A：保持 `MARKET_DATA_LAKE_ROOT` 永久不动。备选 B：先做只读 lake policy audit。 | host-orchestrator / data owner | 独立 backup / restore drill、lake root 切换方案、publish gate 和回滚证据。 | 用户明确要求真实数据湖迁移或 root replacement。 |
| FU-CR053-04 | follow_up_candidate | runtime_authorization | 将 trading / QMT / MiniQMT runtime authorization 保持为候选，不自动启动。 | 备选 A：只做 package manifest offline review。备选 B：取消交易运行授权，保留研究端流程。 | host-orchestrator / trading owner | 独立交易 runtime gate、凭据边界、脱敏证据、账户查询/交易授权分离。 | 用户要求连接 QMT/MiniQMT、账户查询或交易动作。 |

## 4. 不授权项分流

| Item ID | 分流类别 | 决策类型 | 推荐处理 | 备选方案 | owner | 验收标准 | 重访条件 |
|---|---|---|---|---|---|---|---|
| NA-CR053-01 | not_authorized | runtime_authorization | 本轮不授权 NAS mount / scan / mkdir / copy / delete / migration。 | 单项授权 NAS read-only inventory；不推荐，需新 CR 或 Spike。 | human | CP8 approve 明确不授权。 | 用户提供路径并发起 NAS 授权。 |
| NA-CR053-02 | not_authorized | runtime_authorization | 本轮不授权真实目录 move / rename / delete 或 repo-local mechanical move。 | 单项授权 repo-local move；不推荐，需 CR058。 | human | CP8 approve 明确不授权。 | CR058 启动。 |
| NA-CR053-03 | not_authorized | runtime_authorization | 本轮不授权 `MARKET_DATA_LAKE_ROOT` replacement 或真实数据湖迁移。 | 只读 lake policy audit；需新门禁。 | human / data owner | CP8 approve 明确不授权。 | 数据湖迁移诉求出现。 |
| NA-CR053-04 | not_authorized | security | 本轮不授权 Windows full archive / cold / full lake mount。 | 只读 package exchange review；需交易主机安全设计。 | trading owner | CP8 approve 明确不授权。 | 交易主机映射诉求出现。 |
| NA-CR053-05 | not_authorized | security | 本轮不授权凭据、`.env`、token、password、cookie、session、private key 读取。 | N/A；默认禁止。 | human / security owner | CP8 approve 明确不授权。 | 独立凭据处理方案获批。 |
| NA-CR053-06 | not_authorized | runtime_authorization | 本轮不授权 provider fetch / lake write / catalog publish。 | 只读 catalog audit；需新门禁。 | data owner | CP8 approve 明确不授权。 | 数据发布诉求出现。 |
| NA-CR053-07 | not_authorized | runtime_authorization | 本轮不授权 QMT / MiniQMT runtime、账户查询或交易动作。 | 离线 package review；需新门禁。 | trading owner | CP8 approve 明确不授权。 | 交易运行诉求出现。 |
| NA-CR053-08 | not_authorized | runtime_authorization | 本轮不授权 git push / tag / remote rename / history rewrite。 | 本地 commit / bundle checkpoint；需用户单独授权。 | human / host-orchestrator | CP8 approve 明确不授权。 | 用户要求远端发布或 rename。 |
| NA-CR053-09 | not_authorized | follow_up_tracking | 本轮不自动启动 CR058 / CR060+ 或真实迁移。 | 用户明确启动单个 follow-up。 | human / host-orchestrator | CP8 approve 明确不授权。 | 用户选择推进后续 CR。 |
