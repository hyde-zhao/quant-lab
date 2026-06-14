---
status: "confirmed"
version: "0.2"
change_id: "CR-053"
owner: "host-orchestrator"
created_at: "2026-06-14T10:02:00+08:00"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-14T10:59:13+08:00"
---

# Architecture Decision CR053

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-14 | host-orchestrator | 初版 CR053 ADR，覆盖 NAS 映射、传输、备份、真实迁移时点和交易主机边界 |
| 0.2 | 2026-06-14 | host-orchestrator | 按用户确认补充 Linux 三分区统一视图、现有数据湖映射保持不变、Windows 交易机仅映射 package exchange；ADR 状态改为 accepted |

## ADR-CR053-001：NAS 目录映射使用逻辑 root

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | 使用 `QUANT_LAB_*_ROOT` 逻辑变量映射 NAS 512G hot、4T warm、14T cold，不硬编码真实挂载路径；Linux 研究机可把三个分区汇总为 `/mnt/quant-lab/*` 逻辑视图，但底层物理分区仍分离。 |
| 推荐理由 | 当前不授权 NAS 扫描，逻辑 root 能提供可评审架构，同时避免泄漏私有路径。 |
| 备选 | 立即扫描 NAS；只做 Git-only。 |
| 回退 / 切换 | 用户授权 NAS read-only inventory 后，可把逻辑 root 绑定到实际路径。 |

## ADR-CR053-002：数据传输采用 manifest-first 两阶段协议

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | 所有 durable transfer 采用 staging -> checksum -> promote -> record。 |
| 推荐理由 | 可审计、可回滚，适合从 research PC 到 NAS warm archive、从 package exchange 到 trading PC 的边界。 |
| 备选 | 直接复制；整目录 mirror。 |
| 回退 / 切换 | 小型本地 fixture 可 Git commit；大型 artifact 必须 manifest-first。 |

## ADR-CR053-003：备份采用 warm archive + cold backup 分层

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | NAS 4T RAID 是 research archive 主层，NAS 14T HDD 是 cold backup；hot 512G 不是备份层。 |
| 推荐理由 | RAID 不是备份；cold backup 需要独立快照和恢复演练。 |
| 备选 | 只依赖 RAID；把 hot SSD 也作为备份。 |
| 回退 / 切换 | 若 14T HDD 不可用，必须另选外部 cold backup 或暂停真实迁移。 |

## ADR-CR053-004：真实迁移不在 CR053 执行

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | CR053 只产出 dry-run / inventory 设计和报告；真实 repo-local mechanical move 在 CR058 CP6 执行。 |
| 推荐理由 | 设计门、dry-run 门和真实迁移门分离，降低不可逆变更风险。 |
| 备选 | CR053 CP6 执行真实迁移；无限期不规划真实迁移。 |
| 回退 / 切换 | 用户明确授权且 CP5 设计证据通过后，才进入 CR058。 |

## ADR-CR053-005：交易主机只读消费 package exchange

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | Windows 交易机不挂载 full research archive / cold backup / 完整 market data lake，只读消费 package exchange 中的 zip、manifest、checksum、docs bundle。 |
| 推荐理由 | 降低交易主机暴露面，避免把研究环境带入 runtime 主机。 |
| 备选 | 交易主机挂载 full archive；交易主机保留完整研究仓库。 |
| 回退 / 切换 | 隔离测试机可临时 read-only checkout，但不得默认化。 |

## ADR-CR053-006：现有 market data lake 映射保持不变

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | 保持现有 `MARKET_DATA_LAKE_ROOT` / 显式 `--lake-root` 数据湖合同；`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作为文档 alias / pointer，不作为现阶段代码入口。 |
| 推荐理由 | 现有数据湖 CLI、backup / restore、quality / catalog 和 publish gate 均围绕 `MARKET_DATA_LAKE_ROOT` 建立；CR053 目标是迁移 dry-run，不应破坏已验证数据湖路径合同。 |
| 备选 | 立即替换为 `QUANT_LAB_MARKET_DATA_LAKE_ROOT`；在 CR053 中移动真实 lake。 |
| 回退 / 切换 | 若未来确需移动真实 lake，必须另起数据湖迁移 CR，先完成 backup / restore drill，再切换 `.env` 或运行参数。 |

## ADR-CR053-007：Linux 研究机为主挂载端，Windows 交易机窄映射

| 字段 | 内容 |
|---|---|
| 状态 | accepted |
| 决策 | Linux 研究机可以同时挂载 NAS 512G SSD / 4T RAID / 14T HDD 并暴露统一 `/mnt/quant-lab/*` 视图；Windows 交易机只映射 package exchange，默认 read-only。 |
| 推荐理由 | 研究机需要完整研究 / 归档视图，交易机只需要策略包消费面；分开映射降低误运行和敏感数据暴露风险。 |
| 备选 | 三分区混并成单大盘；Windows 交易机映射 full archive / full lake。 |
| 回退 / 切换 | 只有隔离测试机可临时 read-only checkout；交易机默认保持窄映射。 |
