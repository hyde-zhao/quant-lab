---
status: "implemented-cp6-static"
version: "1.0"
change_id: "CR-053"
title: "NAS Mapping for quant-lab Migration Inventory and Dry-run"
created_by: "meta-dev"
created_at: "2026-06-14T12:19:53+08:00"
source_hld: "docs/design/HLD-CR053-QUANT-LAB-MIGRATION-INVENTORY-AND-DRY-RUN.md"
source_adr: "docs/design/ARCHITECTURE-DECISION-CR053.md"
source_lld: "process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md"
real_migration_authorized: false
nas_operation_authorized: false
data_lake_mapping_change_authorized: false
---

# NAS Mapping CR053

## 1. 结论摘要

CR053 采用 logical root map，而不是当前 NAS 真实路径声明。本文只冻结后续 CR058 / CR060+ 可消费的映射合同，不执行 NAS mount、scan、mkdir、copy、delete 或 migration。

| 项目 | 结论 |
|---|---|
| NAS 三个分区逻辑映射 | 512G SSD 作为 hot / package exchange，4T RAID 作为 warm research archive，14T HDD 作为 cold backup。 |
| Linux 研究机映射 | 可以把三分区暴露为 `/mnt/quant-lab/hot`、`/mnt/quant-lab/archive`、`/mnt/quant-lab/cold-backup` 的统一逻辑视图；底层仍分层，不混并为一个职责不明的大盘。 |
| Windows 交易机映射 | 只映射 package exchange，默认 read-only；不映射 full research archive、cold backup、完整 market data lake 或完整 Git workspace。 |
| 数据湖映射 | 保持现有 `MARKET_DATA_LAKE_ROOT` / 显式 `--lake-root` 合同；不替换为 `QUANT_LAB_MARKET_DATA_LAKE_ROOT`，不移动真实 data lake。 |
| 当前验证状态 | `logical-only`；真实路径、容量、权限和可达性需要后续独立授权验证。 |

## 2. Root Map 合同

| root_id | 建议变量 / 入口 | 主设备 / 层 | 逻辑路径 / 相对目录 | 允许内容 | 禁止内容 | 备份等级 | verification_status |
|---|---|---|---|---|---|---|---|
| `repo_workspace` | `QUANT_LAB_REPO_ROOT` | Linux 研究机 2T SSD | `~/workspace/quant-lab` | Git checkout、代码、docs、schema、小 fixture、过程证据 | raw data、凭据、大 artifact、broker raw facts | Git commit / git bundle | logical-only |
| `hot_cache` | `QUANT_LAB_HOT_CACHE_ROOT` | NAS 512G SSD | `/mnt/quant-lab/hot/cache` | 近期 run cache、可重建中间文件、临时 staging | 唯一副本、凭据、未脱敏账户信息、broker raw facts | 可丢弃；TTL 7-14 天建议 | requires-runtime-authorization |
| `package_exchange` | `QUANT_LAB_PACKAGE_EXCHANGE_ROOT` | NAS 512G SSD | `/mnt/quant-lab/hot/package-exchange` | strategy package zip、manifest、sha256、docs bundle、staging | full research archive、cold backup、runtime credential、未授权交易文件 | warm manifest mirror + cold snapshot | requires-runtime-authorization |
| `research_archive` | `QUANT_LAB_RESEARCH_ARCHIVE_ROOT` | NAS 4T RAID | `/mnt/quant-lab/archive/research` | run artifact、报告、模型、source attachment pointer、checksum、registry | market data current truth、凭据、broker raw facts、未脱敏账户材料 | warm durable primary，不等于 backup | requires-runtime-authorization |
| `market_data_lake_alias` | `MARKET_DATA_LAKE_ROOT` / `--lake-root`；`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅文档 alias | 既有外置 data lake / NAS data lake | `/mnt/quant-lab/lake` 或 legacy pointer | published market data、catalog pointer、quality report pointer | research run artifact、broker facts、凭据、CR053 内真实迁移 | 沿用数据湖既有备份策略 | logical-only |
| `cold_backup` | `QUANT_LAB_COLD_BACKUP_ROOT` | NAS 14T HDD | `/mnt/quant-lab/cold-backup` | git bundle、warm archive snapshot、manifest snapshot、restore rehearsal evidence、retired project backup | active workspace、未登记临时文件、凭据 | cold durable backup | requires-runtime-authorization |
| `trading_evidence` | `QUANT_LAB_TRADING_EVIDENCE_ROOT` | Windows 交易机 SSD 或后续 broker evidence archive | `quant-lab/trading-evidence` | 脱敏运行摘要、小型证据、checksum pointer | 凭据、未脱敏账户、full research archive、full lake | 后续交易 CR 定义 | logical-only |

## 3. Linux 研究机统一逻辑视图

Linux 研究机是主要研究与归档操作端。允许的表达方式是统一命名空间，禁止把三块 NAS 分区职责混并。

| logical_path | 底层职责 | 允许访问模式 | 当前 CR053 行为 |
|---|---|---|---|
| `/mnt/quant-lab/hot/cache` | NAS 512G SSD hot cache | planned read-write | 只写静态合同；不创建、不挂载、不扫描。 |
| `/mnt/quant-lab/hot/package-exchange` | NAS 512G SSD package exchange | planned read-write on research PC；read-only to trading PC | 只写静态合同；不生成真实 package。 |
| `/mnt/quant-lab/archive/research` | NAS 4T RAID warm archive | planned read-write on research PC | 只写静态合同；不复制研究 artifact。 |
| `/mnt/quant-lab/archive/package-manifest-mirror` | NAS 4T RAID manifest mirror | planned write via manifest-first promote | 只写静态合同；不执行 promote。 |
| `/mnt/quant-lab/cold-backup/git-bundles` | NAS 14T HDD cold backup | planned write after checkpoint | 只写计划；不执行 `git bundle`。 |
| `/mnt/quant-lab/cold-backup/archive-snapshots` | NAS 14T HDD cold backup | planned snapshot target | 只写计划；不执行 snapshot。 |
| `/mnt/quant-lab/lake` | 现有 market data lake pointer | pointer-only | 不替换 `MARKET_DATA_LAKE_ROOT`，不移动 lake。 |

## 4. Windows 交易机窄映射

| 项目 | 允许 | 禁止 | 说明 |
|---|---|---|---|
| package exchange | `Q:\quant-lab\package-exchange` 或等价 UNC read-only share | 写入 package、写入 manifest、读取 full archive | 交易机只消费 zip / manifest / sha256 / docs bundle。 |
| research archive | 不允许默认映射 | full research archive mount | 避免把研究大目录暴露给 runtime 主机。 |
| cold backup | 不允许默认映射 | 14T cold backup mount | cold backup 不是交易主机消费面。 |
| market data lake | 不允许默认映射完整 lake | full lake mount / root replacement | 交易策略包必须通过 manifest / package 输入，不直接消费全量 lake。 |
| trading evidence | 可在后续交易 CR 中定义脱敏 evidence inbox | 未脱敏账户、资金、持仓、委托、成交数据 | CR053 不连接、不查询、不交易。 |

## 5. 数据湖兼容策略

| 规则 | 当前处理 |
|---|---|
| 现有入口 | 保持 `MARKET_DATA_LAKE_ROOT` 和显式 `--lake-root`。 |
| 新 alias | `QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅作为迁移文档 alias / pointer，不作为代码入口。 |
| `.env` | CR053 不读取、不修改、不建议替换。 |
| 真实 lake move | 不在 CR053 范围；若未来需要，必须另起数据湖迁移 CR，先完成 backup / restore drill。 |
| publish / catalog | CR053 不执行 provider fetch、lake write 或 catalog publish。 |

## 6. 备选方案和切换条件

| 方案 | 当前状态 | 优点 | 代价 | 切换条件 |
|---|---|---|---|---|
| A. logical root + manifest-first transfer + warm/cold backup | selected | 权限最小，可审计，不需要扫描 NAS。 | 当前无法证明真实路径存在、容量足够或权限正确。 | 默认保持；CR058/CR060 前补真实路径绑定或 read-only inventory。 |
| B. NAS read-only inventory | not-selected | 可发现真实目录、容量和历史差异。 | 需要 NAS 授权，可能长耗时，需敏感路径白名单。 | 用户明确授权 NAS read-only inventory、给出路径范围、输出位置和脱敏要求。 |
| C. Git-only migration | not-selected | 最低风险、最快。 | 不能回答 NAS 目录、传输和备份问题。 | 用户明确取消 NAS / archive / backup 迁移诉求。 |
| D. Windows 交易机 full archive 映射 | rejected | 交易机可直接读取更多材料。 | 暴露面过大，违背 ADR-CR053-005/007。 | 默认不得切换；仅隔离测试机可在独立授权下临时 read-only checkout。 |

## 7. 不授权边界与 guardrail evidence

| 禁止操作 | CR053 CP6 结果 |
|---|---|
| NAS mount / scan / mkdir / copy / delete / migration | 未执行；本文仅为 Markdown 静态合同。 |
| 真实目录移动、重命名、删除或 repo-local mechanical move | 未执行；CR058 才可能处理 repo-local mechanical move。 |
| `MARKET_DATA_LAKE_ROOT` 替换或真实 data lake 移动 | 未执行；本文明确保持现状。 |
| Windows 交易机 full archive / cold backup / full lake 映射 | 未授权；本文标记 forbidden。 |
| 读取 `.env`、token、账号、密码、session、cookie、private key | 未执行；本文未消费凭据。 |
| provider fetch / lake write / catalog publish | 未执行。 |
| QMT / MiniQMT runtime、连接、查询账户或交易动作 | 未执行。 |
| git push、tag、远端仓库改名或历史重写 | 未执行。 |

