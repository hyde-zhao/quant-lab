---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S02-repository-archive-and-data-lake-governance"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
---

# Research Archive Manifest Spec

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 ResearchArchiveManifest 字段、错误模型、redaction 和 rollback 合同 |

## 目标

ResearchArchiveManifest 只保存外部 artifact 的索引、校验和治理信息。manifest 可以进入 Git；artifact 内容默认不进入 Git。

## 字段合同

| 字段 | 类型 | 必填 | 约束 |
|---|---|---:|---|
| `archive_id` | string | 是 | 全局唯一 |
| `manifest_version` | string | 是 | 首版 `research_archive_manifest_v1` |
| `storage_tier` | enum | 是 | `workspace_hot` / `nas_hot` / `nas_warm` / `nas_cold` / `trading_local` |
| `logical_type` | enum | 是 | `run_artifact` / `report` / `model` / `source_attachment` / `package_exchange` |
| `artifact_refs[]` | list | 是 | 只保存 pointer / relative path / URI，不保存内容 |
| `checksum.sha256` | string | 条件必填 | artifact 可读取且非敏感 blocked 时必填 |
| `size_class` | enum | 是 | `small` / `medium` / `large` / `blocked-sensitive` |
| `retention_policy` | string | 是 | `active` / `important` / `cold` / `expire-review` |
| `redaction_status` | enum | 是 | `n/a` / `redacted` / `blocked-sensitive` |
| `owner` | string | 是 | 责任方 |
| `created_at` | datetime | 是 | ISO-8601 |
| `rollback_ref` | string | 条件必填 | migration / externalize 时必须指向 commit 或 inventory row |
| `source_commit` | string | 条件必填 | Git 相关 artifact 必填 |
| `notes` | string | 否 | 只允许脱敏摘要 |

## 示例

```yaml
archive_id: research-archive-20260614-example
manifest_version: research_archive_manifest_v1
storage_tier: nas_warm
logical_type: run_artifact
artifact_refs:
  - pointer: archives/runs/example/report.parquet
    pointer_type: relative_path
checksum:
  sha256: "<sha256>"
size_class: large
retention_policy: important
redaction_status: n/a
owner: research
created_at: "2026-06-14T09:00:24+08:00"
rollback_ref: "git:24e2743"
source_commit: "24e2743"
```

## 错误模型

| 错误码 | 触发条件 | 处理 |
|---|---|---|
| `checksum_missing` | artifact 可校验但缺 checksum | 阻断 manifest register |
| `artifact_not_externalized` | 大 artifact 被写入 Git | 阻断 CP7 / CP8 |
| `blocked_sensitive_in_git` | 凭据、账户、broker facts 原文进入 Git | fail closed |
| `rollback_ref_missing` | migration / externalize 缺 rollback_ref | 阻断 migration |
| `storage_tier_unknown` | storage_tier 非枚举值 | 阻断 |
| `redaction_required` | source attachment 未脱敏 | 阻断 Git 保存 |

## 与其他合同的关系

| 合同 | 消费方式 |
|---|---|
| `ARCHIVE-GOVERNANCE.md` | 提供 storage tier、禁止内容和迁移 gate |
| `RESEARCH-REGISTRY-SPEC.md` | 通过 `archive_manifest_ref` 引用本 manifest |
| `HOST-WORKFLOW.md` | package exchange 和交易主机消费前必须校验 checksum |

