---
status: "implemented-cp6-static"
version: "1.0"
change_id: "CR-053"
title: "Manifest-first Transfer and Backup Plan"
created_by: "meta-dev"
created_at: "2026-06-14T12:19:53+08:00"
source_story: "process/stories/CR053-S04-manifest-transfer-and-backup-plan.md"
source_lld: "process/stories/CR053-S04-manifest-transfer-and-backup-plan-LLD.md"
backup_execute_authorized: false
restore_execute_authorized: false
nas_copy_authorized: false
---

# Backup Plan CR053

## 1. 结论摘要

本文定义 manifest-first transfer、warm archive、cold backup 和 restore rehearsal 的静态计划。CR053 不执行备份、不执行恢复、不复制 NAS、不计算真实 checksum、不移动 data lake。

| 项目 | 结论 |
|---|---|
| transfer 模型 | durable transfer 必须走 `stage -> checksum -> promote -> record`，失败 fail closed。 |
| Git checkpoint | CR058 前需要 commit checkpoint + git bundle 计划；CR053 不执行 bundle。 |
| warm archive | NAS 4T RAID 是 research archive 主层，不是备份。 |
| cold backup | NAS 14T HDD 是 cold backup / retired projects / restore rehearsal 层。 |
| package exchange | NAS 512G SSD 只承载 package zip / manifest / sha256 / docs bundle 的窄交换面。 |
| data lake | 保持 `MARKET_DATA_LAKE_ROOT` 和既有数据湖备份策略，不由 CR053 移动或备份。 |

## 2. Manifest-first Transfer 合同

| 字段 | 要求 | 说明 |
|---|---|---|
| `transfer_id` | required | 稳定 ID，例如 `CR058-repo-docs-rename-001`。 |
| `source_root` | required | 引用 S01 root_id，不写真实路径。 |
| `target_root` | required | 引用 S01 root_id，不写真实路径。 |
| `staging_id` | required_before_execute | 真实执行前的 staging 批次号。 |
| `file_count` | required_before_execute | 真实执行前生成。 |
| `total_size` | required_before_execute | 真实执行前生成。 |
| `checksum_policy` | required | `sha256 + manifest_hash`。 |
| `promote_rule` | required | checksum 全部通过后才能 promote。 |
| `record_rule` | required | final manifest 写入 repo / archive pointer。 |
| `rollback_ref` | required_before_cr058 | CR058 启动前必须存在。 |
| `failure_action` | required | checksum mismatch、缺 manifest 或缺 rollback_ref 均阻断。 |

## 3. Transfer Lane 计划

| lane_id | 流向 | 对象 | 推荐机制 | 当前 CR053 行为 | 失败处理 |
|---|---|---|---|---|---|
| `TL-01` | research_pc -> Git | code / docs / schema / manifest spec | local commit checkpoint | 不提交、不 push；仅写计划 | 缺 diff check / rollback_ref 则阻断 CR058。 |
| `TL-02` | research_pc -> hot cache | 可重建 cache / staging | 后续授权 mount / sync | 不执行 mount / sync | staging 失败不 promote。 |
| `TL-03` | hot cache -> warm archive | durable report / model / package manifest mirror | manifest-first promote | 不复制、不计算 checksum | checksum mismatch 阻断 promote。 |
| `TL-04` | warm archive -> cold backup | archive snapshot / manifest snapshot / git bundle | snapshot manifest + restore sample | 不执行 snapshot | restore rehearsal 失败阻断真实迁移。 |
| `TL-05` | package exchange -> Windows trading PC | package zip / sha256 / manifest / docs bundle | read-only package consumption | 不映射交易机、不导入 package | 缺 manifest / checksum 阻断导入。 |
| `TL-06` | trading_pc -> archive | 脱敏 evidence summary | 后续 trading evidence gate | 不连接、不查询、不写入 | redaction 缺失则阻断。 |

## 4. Backup Class 策略

| object_class | primary_location | backup_location | frequency_plan | retention_plan | restore_acceptance | 当前状态 |
|---|---|---|---|---|---|---|
| `git_bundle` | repo workspace | cold backup `git-bundles/` | 每个真实迁移 gate 前 | 至少保留到 CR058 CP8 + 30 天 | `git bundle verify` | planned-only |
| `manifest_registry` | warm archive / Git pointer | cold backup manifest snapshots | 每日增量或每次 promote 后 | daily 14 天、weekly 8 周、monthly 12 月 | 随机读取 manifest + hash 比对 | planned-only |
| `research_reports_models` | warm archive 4T RAID | cold backup snapshots | 每周完整或增量 | weekly 8 周、monthly 12 月 | 恢复 1 个 run 报告样本 | planned-only |
| `package_manifest` | package exchange + warm mirror | cold snapshot | 每次 package promote 后 | 与 package 生命周期一致 | sha256 复验 | planned-only |
| `hot_cache` | NAS 512G SSD | 无强制 durable backup | TTL / optional short snapshot | TTL 7-14 天 | 可重建证明 | no-durable-backup |
| `market_data_lake_policy` | existing external lake | existing lake backup / restore policy | 不由 CR053 定义 | 沿用数据湖策略 | 后续数据湖 gate | out-of-scope |
| `trading_evidence` | trading PC / broker archive | 后续交易 evidence backup | 后续交易 CR 定义 | 后续交易 CR 定义 | redaction + checksum | out-of-scope |

## 5. Restore Rehearsal 计划

| check_id | 验收点 | 输入 | 期望输出 | CR058 前置状态 |
|---|---|---|---|---|
| `RR-01` | manifest sample restore | cold backup manifest snapshot | 可读取 manifest，并能匹配 manifest hash | required-before-real-migration |
| `RR-02` | small report sample restore | 1 个小型报告样本 | sha256 复验通过，路径回写到 restore evidence | required-before-real-migration |
| `RR-03` | git bundle verify | pre-migration git bundle | bundle 可验证，包含 rollback commit | required-before-real-migration |
| `RR-04` | package manifest verify | package zip + manifest + sha256 | package checksum 与 manifest 一致 | required-before-package-import |
| `RR-05` | lake policy boundary check | `MARKET_DATA_LAKE_ROOT` policy pointer | 确认未由 CR053 移动或替换 | required-before-data-lake-change |

## 6. Rollback 计划

| 场景 | rollback_ref | 回退动作 | 当前 CR053 状态 |
|---|---|---|---|
| CR058 repo-local docs / path rewrite 失败 | pre-CR058 commit + git bundle | 回到 pre-migration commit，保留 failure manifest | planned-only |
| package promote 失败 | previous package manifest | 不 promote，保留 staging failure manifest | planned-only |
| warm archive promote 后发现损坏 | previous warm manifest + cold snapshot | 按 manifest 恢复目标对象 | planned-only |
| cold backup restore rehearsal 失败 | failure evidence | 阻断 CR058 / CR060，补备份策略 | planned-only |
| lake root 变更需求出现 | data lake migration CR rollback_ref | 停止 CR053，发起独立数据湖迁移 CR | out-of-scope |

## 7. 不授权边界与 guardrail evidence

| 禁止操作 | CR053 CP6 结果 |
|---|---|
| real backup execute | 未执行。 |
| real restore execute | 未执行。 |
| NAS copy / delete / migration | 未执行。 |
| real checksum over external archive / lake | 未执行。 |
| `MARKET_DATA_LAKE_ROOT` replacement or real lake move | 未执行。 |
| `.env` / credential read | 未执行。 |
| git push / tag / history rewrite | 未执行。 |

