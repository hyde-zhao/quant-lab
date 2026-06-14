---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S02-repository-archive-and-data-lake-governance"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
real_migration_authorized: false
nas_operation_authorized: false
---

# Research Archive Governance

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版仓库、研究归档、数据湖、broker archive 和硬件冷热分层治理合同 |

## 目标

本文冻结 quant-lab 的 Git 仓库、research archive、market data lake、broker archive、package exchange 和硬件冷热分层边界。本文只定义合同，不执行 scan、mount、copy、delete、migration 或 publish。

## 存储域职责

| 存储域 | 逻辑 root | 允许内容 | 禁止内容 | owner |
|---|---|---|---|---|
| Git repository | repo root | 代码、docs、schema、manifest spec、脱敏摘要、小型 fixture | raw data、大 artifact、凭据、账户原文、broker facts 原文 | quant-lab repo |
| Research hot cache | `RESEARCH_HOT_CACHE_ROOT` | 近期 run cache、package exchange staging、manifest index | 当前市场数据事实源、broker raw facts | research archive owner |
| Research archive | `RESEARCH_ARCHIVE_ROOT` | run artifact、报告、模型、source attachment 指针、checksum | 凭据、未脱敏账户、broker raw facts | research archive owner |
| Research cold archive | `RESEARCH_COLD_ARCHIVE_ROOT` | 冷归档、旧项目副本、备份 | active workspace、未登记 artifact | archive owner |
| Market data lake | `MARKET_DATA_LAKE_ROOT` | published current truth、candidate data、catalog pointer | 研究 run artifact、broker facts | FEAT-02 / market data owner |
| Broker / trading archive | `BROKER_LAKE_ROOT` 或 trading archive | 脱敏后运行证据、broker facts 指针 | 未脱敏账户、凭据、研究大 artifact | trading evidence owner |
| Package exchange | `STRATEGY_PACKAGE_EXCHANGE_ROOT` | strategy package、checksum、manifest、docs bundle | full research archive、未授权 runtime 文件 | package owner |

## 硬件冷热分层

| 设备 / 层 | 默认职责 | 水位策略 | CR051 授权 |
|---|---|---|---|
| 研究主机 2T SSD | 完整 Git checkout、active workspace、近期研究 cache | active / hot | 只允许文档计划 |
| NAS 512G SSD | hot cache、package exchange、manifest index | hot / exchange | 不授权 mount / copy |
| NAS 4T RAID | `RESEARCH_ARCHIVE_ROOT` 主体 | warm / durable | 不授权 migration |
| NAS 14T HDD | cold archive、旧项目、备份 | cold / backup | 不授权 copy / delete |
| 交易主机 512G SSD | strategy package 消费、小型运行证据 | consumer only | 不授权 import / runtime |

## 分类规则

| artifact class | 默认路由 | Git 是否允许 | 必需证据 |
|---|---|---|---|
| code / docs / schema | Git repository | 是 | review / tests |
| small fixture | Git repository | 是 | 脱敏说明 |
| run artifact | Research archive | 否 | archive manifest、checksum |
| source attachment | Research archive pointer | 否 | redaction_status、usage_boundary |
| market data current truth | Market data lake | 否 | data release / catalog pointer |
| broker facts | Broker / trading archive | 否 | redaction_status、runtime authorization |
| credentials / account raw | blocked-sensitive | 否 | 不保存 |
| package bundle | Package exchange | 仅 manifest / checksum 可进 Git | package manifest、checksum |

## 禁止路径

- Research archive 不得成为 market data current truth。
- Market data lake 不得保存研究 run artifact。
- Git 不得保存 raw data、大 artifact、凭据、账户原文或 broker facts 原文。
- 交易主机不得挂载 full research archive 或承担研究 workspace 职责。
- CR051 不执行真实路径探测、NAS 挂载、复制、删除、迁移、provider fetch、lake write 或 publish。

## 后续迁移 gate

| Gate | 进入条件 | 输出 | 当前状态 |
|---|---|---|---|
| inventory dry-run | CR051 CP8 approved，用户单独授权 inventory | MigrationInventory draft | not-authorized |
| forbidden content scan | inventory 授权后 | forbidden content report | not-authorized |
| archive migration dry-run | inventory pass，rollback_ref 齐备 | dry-run move plan | not-authorized |
| physical migration | 用户单独授权源、目标、窗口和 rollback | migration evidence | not-authorized |

