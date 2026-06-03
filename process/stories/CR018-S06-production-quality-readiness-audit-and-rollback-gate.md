---
story_id: "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
title: "production quality / readiness / rollback gate"
story_slug: "production-quality-readiness-audit-and-rollback-gate"
status: "verified"
priority: "P0"
wave: "CR018-W3-PUBLISH-ROLLBACK"
depends_on:
  - "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
  - "CR018-S03-real-benchmark-index-components-weights-backfill"
  - "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
dependency_type:
  - upstream: "CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill"
    type: "contract"
  - upstream: "CR018-S03-real-benchmark-index-components-weights-backfill"
    type: "contract"
  - upstream: "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
    type: "validation-contract"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr018_readiness_rollback_gate.py"
  shared:
    - "market_data/validation.py"
    - "market_data/catalog.py"
    - "market_data/publish.py"
  merge_owner: "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
  forbidden:
    - "dataset-level rollback only"
    - "delete raw manifest candidate or historical release evidence"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "real lake write"
    - "catalog current pointer publish before CP5"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.9"
    - "process/HLD-DATA-LAKE.md#19.10"
    - "process/HLD-DATA-LAKE.md#19.11"
    - "process/ARCHITECTURE-DECISION.md#ADR-065"
    - "process/stories/CR018-S06-production-quality-readiness-audit-and-rollback-gate.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  current_pointer_publish_allowed: false
created_at: "2026-05-29"
updated_at: "2026-05-29T10:24:36+08:00"
change_id: "CR-018"
---

# CR018-S06：production quality / readiness / rollback gate

## 目标

聚合 P0/P1 readiness、audit evidence、blocked claims 和 release-level rollback contract，形成 Explicit Publish Gate 前的 production quality 总门。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-124、REQ-130、REQ-132、REQ-137 |
| HLD | `process/HLD-DATA-LAKE.md` §19.9-§19.11 |
| ADR | ADR-065 |

## 开发上下文（dev_context）

**背景说明**：production publish 不能只看某个 dataset pass，而应按 release 汇总 P0 readiness、P1 blocked claims、审计证据和 rollback target。rollback 粒度必须是 release-level，禁止只回滚单 dataset 导致 current truth 不一致。

**输入文件**：S02/S03/S05 readiness 合同、S04 claim boundary、CR018 HLD / ADR、本 Story 卡片。

**输出文件**：`tests/test_cr018_readiness_rollback_gate.py`；共享修改 `market_data/validation.py`、`market_data/catalog.py`、`market_data/publish.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| readiness audit aggregator | dataset readiness、quality status、blocked claims | release readiness report | P0 fail 时 publish blocked |
| rollback contract | release_id、previous_release_id | rollback target、evidence ref | 禁止 dataset-only rollback |
| audit evidence registry | manifest/run metadata/quality report | evidence completeness | 不删除 raw manifest 或历史 release evidence |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S02 | contract | 可基于 S02 Story/LLD 合同起草 | 开发需 S02 合同冻结 | PIT / tradability readiness 输入 |
| CR018-S03 | contract | 可基于 S03 Story/LLD 合同起草 | 开发需 S03 合同冻结 | benchmark readiness 输入 |
| CR018-S05 | validation-contract | 可基于 S05 Story/LLD 合同起草 | 开发需 S05 合同冻结 | adjustment readiness 输入 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_readiness_rollback_gate.py` | 当前 Story 独占 |
| shared | `market_data/validation.py`、`market_data/catalog.py`、`market_data/publish.py` | 与 S02/S03/S05/S07 共享，开发默认串行 |
| forbidden | dataset-only rollback、删除历史证据、CP5 前 publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S06-T1 | 修改 | `market_data/validation.py` | 汇总 P0/P1 readiness 与 blocked claims |
| CR018-S06-T2 | 修改 | `market_data/catalog.py` | 增加 release-level rollback metadata |
| CR018-S06-T3 | 修改 | `market_data/publish.py` | 增加 publish 前 readiness audit hook |
| CR018-S06-T4 | 创建 | `tests/test_cr018_readiness_rollback_gate.py` | 验证 P0 fail、P1 blocked claims 和 rollback 粒度 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_readiness_rollback_gate.py`。

**验证方式**：fixture-only 合同测试。

**关键验证场景**：P0 fail 时 publish allowed=0；release-level rollback target 必填；dataset-only rollback blocked；历史 evidence 不删除。

## 量化验收标准（acceptance_criteria）

- [ ] readiness audit 字段覆盖 release、dataset、quality、blocked_claims、rollback_target。
- [ ] P0 fail 时 publish allowed 次数为 0。
- [ ] dataset-level rollback-only 通过次数为 0。
- [ ] real_lake_write、current_pointer_publish、credential_read 计数均为 0。

## 阻塞说明

CP5 已获批；真实 rollback 或 publish 必须在后续 Explicit Publish Gate 和 per-run authorization 下执行。
