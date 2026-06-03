---
story_id: "CR018-S01-production-current-truth-definition-and-dataset-groups"
title: "production current truth 定义与 dataset group"
story_slug: "production-current-truth-definition-and-dataset-groups"
status: "verified"
priority: "P0"
wave: "CR018-W1-SCOPE-CONTRACT"
depends_on:
  - "CR014-S09-windowed-real-fetch-lake-write-run"
dependency_type:
  - upstream: "CR014-S09-windowed-real-fetch-lake-write-run"
    type: "runtime-evidence"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/release_scope.py"
    - "market_data/dataset_groups.py"
    - "tests/test_cr018_release_scope_dataset_groups.py"
  shared:
    - "market_data/catalog.py"
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR018-S01-production-current-truth-definition-and-dataset-groups"
  forbidden:
    - "process/REQUIREMENTS.md"
    - "process/USE-CASES.md"
    - "process/HLD.md"
    - "process/HLD-DATA-LAKE.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "provider fetch"
    - "real lake write"
    - "catalog current pointer publish"
    - "QMT API operation"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.1"
    - "process/HLD-DATA-LAKE.md#19.3"
    - "process/ARCHITECTURE-DECISION.md#ADR-062"
    - "process/ARCHITECTURE-DECISION.md#ADR-063"
    - "process/stories/CR018-S01-production-current-truth-definition-and-dataset-groups.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  provider_fetch_allowed: false
  lake_write_allowed: false
  current_pointer_publish_allowed: false
  qmt_operation_allowed: false
created_at: "2026-05-29"
updated_at: "2026-05-29T08:53:20+08:00"
change_id: "CR-018"
---

# CR018-S01：production current truth 定义与 dataset group

## 目标

冻结 CR018 production current truth 的 scoped release、P0/P1 dataset group、release claim matrix 和 readiness summary 合同，作为后续 P0 readiness、publish、rollback、research rerun 与 QMT admission 的共同输入。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-123、REQ-124、REQ-125、REQ-135、REQ-136、REQ-137 |
| HLD | `process/HLD-DATA-LAKE.md` §19.1-§19.6 |
| ADR | ADR-062、ADR-063 |

## 开发上下文（dev_context）

**背景说明**：CR014 S14 已有 2015-01-05..2026-05-28 的 full-A `prices` / `adj_factor` candidate，但 candidate 不等于 production current truth。本 Story 先冻结 release 范围、dataset group、allowed/blocked claims 与 readiness summary schema，防止后续 publish gate 使用含糊口径。

**输入文件**：`process/HLD-DATA-LAKE.md`、`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、本 Story 卡片。

**输出文件**：`market_data/release_scope.py`、`market_data/dataset_groups.py`、`tests/test_cr018_release_scope_dataset_groups.py`；共享文件仅允许按 LLD 明确范围更新 `market_data/catalog.py`、`README.md`、`docs/USER-MANUAL.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| release scope resolver | release_id、start_date、end_date、latest_closed_trade_date | scoped release window、blocked pre-2015 flag、coverage denominator | 2015 前 since-inception 完整声明必须 blocked |
| dataset group registry | dataset id、priority | P0/P1 group、required_for_publish、blocked_claims | 未登记 dataset 不得进入 publish readiness |
| claim matrix | readiness status、P1 availability | allowed claims、blocked claims、reason code | P1 缺失不阻断 core release，但阻断中性化 / 容量 / scale_up 声明 |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR014-S09 | runtime-evidence | 可读取 S09 candidate evidence 作为现状输入 | CP5 已获批；开发时不得改写 S09 candidate | 只消费候选数据湖事实和检查报告，不 publish |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `market_data/release_scope.py`、`market_data/dataset_groups.py`、`tests/test_cr018_release_scope_dataset_groups.py` | 当前 Story 独占 |
| shared | `market_data/catalog.py`、`README.md`、`docs/USER-MANUAL.md` | merge owner 为当前 Story |
| forbidden | HLD / ADR / 需求正文、凭据、真实 provider / lake / publish / QMT 操作 | 禁止修改或执行 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S01-T1 | 创建 | `market_data/release_scope.py` | 定义 scoped release window、latest closed trade date 和 pre-2015 blocked reason |
| CR018-S01-T2 | 创建 | `market_data/dataset_groups.py` | 定义 P0/P1 dataset group 和 claim matrix |
| CR018-S01-T3 | 创建 | `tests/test_cr018_release_scope_dataset_groups.py` | 验证 D1-D4 决策到合同字段的覆盖 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_release_scope_dataset_groups.py`。

**验证方式**：离线合同测试；不联网、不读凭据、不写真实 lake、不 publish。

**关键验证场景**：release scope 覆盖 2015-01-05..latest closed trade date；2015 前完整声明 blocked；P0/P1 group 完整；P1 缺失只阻断指定 claims。

## 量化验收标准（acceptance_criteria）

- [ ] D1-D4 的 release scope、P0/P1 group、allowed/blocked claims 字段覆盖率为 100%。
- [ ] `current_truth_publish`、`provider_fetch`、`lake_write`、`credential_read`、`qmt_operation` 计数均为 0。
- [ ] 2015 前 since-inception 完整声明 allowed 次数为 0。
- [ ] 未登记 dataset 进入 publish readiness 的通过次数为 0。

## 阻塞说明

CP5 已获批；本 Story 不授权真实抓取、真实写湖、catalog publish、凭据读取、DuckDB 写入或 QMT 操作。
