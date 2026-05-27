---
artifact: "CR-004 CP5 Batch A STORY-014/STORY-015 Review Summary"
round: 1
status: final
decision: revise
blocking_count: 0
required_count: 8
optional_count: 4
created_at: "2026-05-17"
owner: "meta-po"
---

# Review Summary

## 1. 输入清单

- findings_files:
  - `process/reviews/CR004-BATCH-A-SE-FINDINGS-2026-05-17.md`
  - `process/reviews/CR004-BATCH-A-QA-FINDINGS-2026-05-17.md`

## 2. 严重度汇总

| Severity | Count | Owner |
|----------|-------|-------|
| 严重 | 0 | `meta-po` |
| 一般 | 8 | `meta-dev` |
| 轻微 | 4 | `meta-dev` |

## 3. 决策

- decision: `revise`
- rationale: 两个 reviewer lane 均认为架构方向成立，`market_data/` 独立边界、fake/offline 默认、真实 adapter fail-fast、限速/重试/熔断、raw/manifest 基础追溯、路径可配置和依赖最小化总体充分；但 CP5 批准前必须修订断点续跑、run_id/source_run_id 血缘、错误枚举一致性、available_at/adjustment_policy 来源、raw/manifest 原子性和 Batch A 数据契约范围。
- next_checkpoint: `CP5-CR004-BATCH-A-LLD-REVIEW`

## 4. 后续动作

1. `meta-dev` 修订 STORY-014 / STORY-015 LLD，优先处理所有“一般” findings。
2. `meta-dev` 在 LLD 中补充或明确：
   - `source_unresolved` 错误枚举或统一映射策略。
   - `run_id` / `source_run_id` 在 request、raw metadata、manifest、后续 canonical 之间的血缘闭环。
   - manifest resume policy：已成功批次跳过、失败/部分成功批次处理、幂等键。
   - raw 写入临时文件 + 原子 rename、raw checksum / row count、manifest 失败补偿或 orphan raw 策略。
   - fake raw 中 `available_at`、`adjustment_policy` 的来源或 deterministic derivation rule。
   - Batch A 只冻结 `prices` + raw/manifest 基础契约，其余 `index_members`、`trade_calendar`、quality gate、多源比对延期到 STORY-016/017，或在 STORY-014 增加显式占位契约。
   - retry/throttle/circuit 边界测试和缓存/pycache 扫描要求。
3. `meta-po` 复核修订后的 LLD，重新生成或刷新 CP5 批次 A 自动预检与人工审查稿。
4. 用户确认 CP5 后，才允许 `meta-dev` 实现 STORY-014，再实现 STORY-015。
