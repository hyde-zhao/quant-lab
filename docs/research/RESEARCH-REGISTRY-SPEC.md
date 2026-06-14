---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S04-registry-and-evidence-contracts"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
runtime_authorized: false
---

# Research Registry Spec

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 RunManifest、ValidationEvidence、ProjectIdentity、MigrationInventory 和 ArchivePointer 合同 |

## 目标

Research registry 保存研究证据索引和最小可复验字段，不保存凭据、账户、broker facts 原文或大 artifact 内容。CR051 只定义 schema 文档，不写真实 registry 数据、不扫描文件系统、不执行 runtime。

## RunManifest

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `run_id` | string | 是 | 研究运行 ID |
| `manifest_version` | string | 是 | `run_manifest_v1` |
| `commit` | string | 是 | Git commit |
| `data_release` | string | 是 | 指向 FEAT-02 current truth release 或 structured missing |
| `config_hash` | string | 是 | 复验配置 hash |
| `seed` | int / string | 条件必填 | 随机过程必须记录；确定性流程可写 `n/a` |
| `protocol_ref` | string | 是 | ResearchProtocol |
| `artifact_refs[]` | list | 是 | 外部 artifact pointer |
| `archive_manifest_ref` | string | 是 | ResearchArchiveManifest |

## ValidationEvidence

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `evidence_id` | string | 是 | 验证证据 ID |
| `run_refs[]` | list | 是 | 关联 run_id |
| `metric_summary` | mapping | 是 | 只保存摘要 |
| `bias_checks` | mapping | 是 | 泄露、PIT、成本、稳定性等检查 |
| `claim_boundary` | list | 是 | allowed / blocked claims |
| `runtime_claim_level` | enum | 是 | `none` / `paper_candidate` / `delivery_candidate` / `runtime_candidate_blocked` |
| `blocked_claims[]` | list | 是 | 默认包含 runtime / trade-ready 相关未授权 claim |

## ProjectIdentity

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `canonical_name` | string | 是 | 固定 `quant-lab` |
| `legacy_aliases[]` | list | 是 | 至少包含 `local_backtest` |
| `repo_name_target` | string | 是 | 默认 `quant-lab`，真实改名另行授权 |
| `doc_alias_policy` | string | 是 | 新文档用 canonical，历史审计保留 alias |
| `env_aliases` | mapping | 是 | `QUANT_LAB_REPO_ROOT` / `LOCAL_BACKTEST_REPO_ROOT` |

## MigrationInventory

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `path` | string | 是 | 计划路径，不执行移动 |
| `path_class` | enum | 是 | code / docs / process / artifact / sensitive / external |
| `owner_feature` | string | 是 | 文件 owner |
| `move_action` | enum | 是 | `keep` / `move_later` / `externalize_later` / `blocked_sensitive` |
| `verification_rule` | string | 是 | 验证方式 |
| `rollback_ref` | string | 是 | Git commit 或 inventory row |
| `authorization_id` | string | 条件必填 | 真实移动时必须有 |

## ArchivePointer

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `archive_manifest_ref` | string | 是 | 指向 ResearchArchiveManifest |
| `pointer_type` | enum | 是 | relative_path / URI / catalog_ref |
| `redaction_status` | enum | 是 | `n/a` / `redacted` / `blocked-sensitive` |
| `checksum_ref` | string | 条件必填 | 可校验 artifact 必填 |

## 错误模型

| 错误码 | 触发条件 | 行为 |
|---|---|---|
| `missing_required_field` | 必填字段缺失 | 阻断 registry pass |
| `artifact_not_externalized` | 大 artifact 写入 Git | 阻断 |
| `runtime_claim_not_authorized` | 声明 runtime verified / trade-ready | fail closed |
| `historical_rewrite_blocked` | 批量改写历史 `local_backtest` 审计证据 | blocked |
| `credential_field_blocked` | registry 出现凭据 / 账户原文 | fail closed |

## Guardrail

任何 registry 或 evidence 文档出现以下 claim 必须阻断：`runtime verified`、`trade-ready`、`live-ready`、`QMT-ready`、`MiniQMT-ready`，除非后续独立 CR 明确授权并形成 runtime evidence。

