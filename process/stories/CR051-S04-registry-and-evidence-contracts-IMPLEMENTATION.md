---
story_id: "CR051-S04-registry-and-evidence-contracts"
status: "implemented-cp6"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
cp6_check: "process/checks/CP6-CR051-S04-registry-and-evidence-contracts-CODING-DONE.md"
---

# CR051-S04 Implementation

## 实现对象

| 对象 | 路径 | 结果 |
|---|---|---|
| research registry spec | `docs/research/RESEARCH-REGISTRY-SPEC.md` | 已创建 |

## 设计契约映射

| LLD 契约 | 实现位置 | 验证 |
|---|---|---|
| RunManifest 字段 | `RESEARCH-REGISTRY-SPEC.md` §RunManifest | 静态 review |
| ValidationEvidence 字段 | `RESEARCH-REGISTRY-SPEC.md` §ValidationEvidence | 静态 review |
| ProjectIdentity / MigrationInventory / ArchivePointer | `RESEARCH-REGISTRY-SPEC.md` 对应章节 | 静态 review |
| runtime claim blocked | `RESEARCH-REGISTRY-SPEC.md` §Guardrail | guardrail review |

## 验证摘要

- 本 Story 只定义 schema 文档，不写真实 registry 数据。
- 凭据、账户、broker facts 原文、大 artifact 内容均不进入 Git。

