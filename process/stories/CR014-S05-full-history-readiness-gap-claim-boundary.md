---
story_id: "CR014-S05-full-history-readiness-gap-claim-boundary"
title: "full-history readiness audit / gap register / claim boundary"
status: "verified"
priority: "P0"
wave: "CR014-W3-AUDIT-OPS"
depends_on:
  - "CR014-S01-a-share-universe-lifecycle-contract"
  - "CR014-S02-parquet-layout-manifest-catalog-publish-gate"
  - "CR014-S03-p0-plan-run-normalize-validate-publish-contract"
  - "CR014-S04-duckdb-readonly-query-audit-parity-boundary"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T09:08:50+08:00"
change_id: "CR-014"
---

# CR014-S05：full-history readiness audit / gap register / claim boundary

## Story 摘要

定义全 A since-inception readiness matrix、gap register、allowed_claims、blocked_claims 和 required_missing 的输出合同。任一 P0 gate 未通过时，不允许输出 full-A production allowed claim。

## dev_context

**输入依据**：`process/HLD-DATA-LAKE.md` §17.10、§17.13；ADR-048、ADR-049、ADR-050、ADR-051；REQ-088、REQ-095、REQ-096。

**未来实现候选文件**：`market_data/readiness.py`、`market_data/claims.py`、`tests/test_cr014_readiness_claim_boundary.py`。

**开发合同**：

| 对象 | 输入 | 输出 | 失败路径 |
|---|---|---|---|
| readiness matrix | catalog pointer、manifest、quality candidate、lifecycle denominator | dataset/window/source/readiness status | 任一 P0 缺口进入 gap register |
| gap register | readiness matrix、audit evidence | dataset、window、gap_code、evidence_path、remediation、解除条件 | evidence 缺失时 claim blocked |
| claim boundary | gap register、publish status、unsupported register | allowed_claims / blocked_claims / required_missing | P0 gate 未过时 full-A allowed claim=0 |

**调用方向**：读取 S01/S02/S03/S04 输出合同；向 S07/S08 提供消费声明边界；不调用 provider、不写 lake、不 publish。

## validation_context

**验证方式**：fixture readiness / gap register contract test；不读取旧 reports 内容，不覆盖旧 reports。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| P0 dataset 缺口 | blocked_claims 写 gap、证据和解除条件 |
| candidate audit PASS 但未 publish | allowed current truth claim=0 |
| old evidence 存在 | 只作为引用路径，不覆盖 |
| full-A since-inception 未完整 | full-A production allowed claim=0 |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | blocked_claims 100% 包含缺口、证据路径和解除条件 | contract test |
| AC-02 | 任一 P0 gate 未通过时 full-A allowed claim 输出次数为 0 | 单元测试 |
| AC-03 | readiness denominator 使用 S01 lifecycle/current-truth 合同 | LLD 静态检查 |
| AC-04 | provider_fetch=0、lake_write=0、credential_read=0、old_report_overwrite=0 | 门控检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S01、CR014-S02、CR014-S03、CR014-S04 |
| 下游依赖 | CR014-S07、CR014-S08 |
| 主所有权 | `market_data/readiness.py`、`market_data/claims.py` |
| 共享文件 | `market_data/validation.py`、`market_data/audit.py` |
| 禁止范围 | `.env`、`data/**`、`reports/**`、旧 reports 覆盖、真实补数、真实 publish |

## LLD 输入

- S01 lifecycle denominator、S02 publish gate、S03 pipeline state、S04 DuckDB audit evidence。
- HLD-DATA-LAKE §17 claim boundary。
- ADR-050 / ADR-051。
- CP5 前只允许规划与候选合同，不允许真实证据覆盖或真实写入。
