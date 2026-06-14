---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S03-research-pc-and-trading-pc-workflow"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
transfer_authorized: false
runtime_authorized: false
---

# Research PC and Trading PC Workflow

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版研究主机、NAS 和交易主机职责边界与 package exchange 合同 |

## 目标

本文定义研究主机、NAS 热 / 温 / 冷层和交易主机之间的文件流边界。交易主机是 strategy package consumer，不是 research workspace。CR051 不执行 package transfer、import、QMT / MiniQMT connection 或 runtime。

## 主机职责

| HostRole | 设备现状 | 默认职责 | 禁止职责 |
|---|---|---|---|
| `research_pc` | 主力研究主机 2T SSD | 完整 Git checkout、开发环境、active research workspace、近期 run/cache | 直接作为交易 runtime 授权来源 |
| `nas_hot` | NAS 512G SSD | 热缓存、package exchange、manifest index | 保存凭据、账户原文、broker facts 原文 |
| `nas_warm` | NAS 4T RAID | `RESEARCH_ARCHIVE_ROOT` 主体、长期可复跑证据 | market data current truth publish |
| `nas_cold` | NAS 14T HDD | cold archive、旧项目、备份 | active workspace |
| `trading_pc` | 交易主机 512G SSD | 消费 strategy package、checksum、manifest、docs bundle、小型运行证据 | full research archive、研究开发、研究脚本运行 |

## 文件流

| 流向 | 对象 | 当前状态 | 解除条件 |
|---|---|---|---|
| research_pc -> Git | code / docs / schema / manifest spec | allowed | 常规 review / tests |
| research_pc -> research archive | run artifact / report / model pointer | planned only | 后续 archive authorization |
| research_pc -> package exchange | package manifest plan | planned only | 后续 package CR 和 checksum |
| package exchange -> trading_pc | zip / manifest / checksum / docs bundle | blocked | 后续 runtime / package import authorization |
| trading_pc -> archive | runtime evidence summary | blocked | 后续 trading evidence redaction gate |
| trading_pc -> Git | 脱敏小型证据摘要 | blocked by default | 后续 review 确认无敏感信息 |

## Package Exchange Contract

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `package_id` | string | 是 | strategy package ID |
| `package_manifest_ref` | string | 是 | package manifest 路径或 pointer |
| `checksum_sha256` | string | 是 | 交易主机消费前必须校验 |
| `docs_bundle_ref` | string | 是 | 用户可审查说明 |
| `source_commit` | string | 是 | Git commit |
| `transfer_status` | enum | 是 | CR051 只允许 `planned` / `blocked` |
| `target_host_role` | enum | 是 | 默认 `trading_pc` |

## 失败行为

| 触发条件 | 错误码 | 行为 |
|---|---|---|
| 交易主机挂载 full research archive | `trading_pc_archive_mount_blocked` | fail closed |
| 交易主机运行研究脚本 | `research_runtime_on_trading_pc_blocked` | fail closed |
| package 缺 checksum | `package_checksum_missing` | 阻断传输 |
| package 缺 manifest | `package_manifest_missing` | 阻断导入 |
| CR051 出现 transfer/import 命令 | `operation_not_authorized` | 阻断 CP7 |

## 当前不授权项

- 不真实传输 package。
- 不导入交易主机。
- 不连接或运行 QMT / MiniQMT。
- 不读取凭据、账户、token 或 `.env`。
- 不将交易主机作为研究 archive 或研究开发环境。

