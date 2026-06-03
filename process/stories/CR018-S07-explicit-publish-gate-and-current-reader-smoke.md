---
story_id: "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
title: "Explicit Publish Gate 与 current reader smoke"
story_slug: "explicit-publish-gate-and-current-reader-smoke"
status: "verified"
priority: "P0"
wave: "CR018-W3-PUBLISH-ROLLBACK"
depends_on:
  - "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
dependency_type:
  - upstream: "CR018-S06-production-quality-readiness-audit-and-rollback-gate"
    type: "runtime"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr018_publish_current_reader_smoke.py"
  shared:
    - "market_data/publish.py"
    - "market_data/catalog.py"
    - "market_data/readers.py"
  merge_owner: "CR018-S07-explicit-publish-gate-and-current-reader-smoke"
  forbidden:
    - "validate auto publish"
    - "parity auto publish"
    - "quality report auto publish"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "catalog current pointer publish before CP5"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.7"
    - "process/HLD-DATA-LAKE.md#19.10"
    - "process/ARCHITECTURE-DECISION.md#ADR-065"
    - "process/stories/CR018-S07-explicit-publish-gate-and-current-reader-smoke.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  current_pointer_publish_allowed: false
created_at: "2026-05-29"
updated_at: "2026-05-29T10:53:06+08:00"
change_id: "CR-018"
---

# CR018-S07：Explicit Publish Gate 与 current reader smoke

## 目标

建立 release-level Explicit Publish Gate、dataset-level 明细、current pointer 读烟测和 publish evidence，确保只有显式发布入口能更新 current truth。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-124、REQ-125、REQ-131、REQ-132 |
| HLD | `process/HLD-DATA-LAKE.md` §19.7、§19.10 |
| ADR | ADR-065 |

## 开发上下文（dev_context）

**背景说明**：CR014/CR018 均要求 Validate / parity PASS 不自动 publish，Normalize / Replay 只生成 candidate。production current truth 必须由 Explicit Publish Gate 单入口更新 current pointer，并能通过 current reader smoke 验证。

**输入文件**：S06 readiness audit / rollback gate、CR018 HLD / ADR、本 Story 卡片、现有 catalog / readers / publish 合同。

**输出文件**：`tests/test_cr018_publish_current_reader_smoke.py`；共享修改 `market_data/publish.py`、`market_data/catalog.py`、`market_data/readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| explicit publish gate | release_id、approval_id、readiness report | publish decision、current pointer update plan | 缺 approval_id 或 P0 fail 必须 blocked |
| current reader smoke | release_id、P0 dataset list | smoke result、row count、policy metadata | 不读取 candidate 替代 current |
| publish evidence | run metadata、manifest、quality report | audit evidence record | validate/parity 不得自动 publish |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S06 | runtime | LLD 可先定义接口和失败路径 | 开发需 S06 readiness/rollback 合同冻结 | 真实 publish 仍需后续授权 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_publish_current_reader_smoke.py` | 当前 Story 独占 |
| shared | `market_data/publish.py`、`market_data/catalog.py`、`market_data/readers.py` | 与 S06/S02/S05 共享，开发默认串行 |
| forbidden | validate/parity/quality 自动 publish，CP5 前 current pointer publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S07-T1 | 修改 | `market_data/publish.py` | 增加 Explicit Publish Gate 和 approval_id 合同 |
| CR018-S07-T2 | 修改 | `market_data/catalog.py` | 定义 release-level current pointer evidence |
| CR018-S07-T3 | 修改 | `market_data/readers.py` | 增加 current reader smoke 的 fail-fast 合同 |
| CR018-S07-T4 | 创建 | `tests/test_cr018_publish_current_reader_smoke.py` | 验证显式发布、禁止自动发布、current reader smoke |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_publish_current_reader_smoke.py`。

**验证方式**：fixture-only 合同测试；不执行真实 publish。

**关键验证场景**：缺 approval_id blocked；P0 fail blocked；validate/parity/quality report 不自动 publish；current reader 不读 candidate。

## 量化验收标准（acceptance_criteria）

- [ ] publish 必须显式审批，缺 approval_id 时 allowed 次数为 0。
- [ ] current reader smoke 覆盖 P0 dataset group。
- [ ] validate/parity/quality 自动 publish 次数为 0。
- [ ] current_pointer_publish、real_lake_write、credential_read 计数均为 0。

## 阻塞说明

CP5 已获批；真实 current pointer publish 必须后续另有 per-run authorization，不由本 Story 卡片授权。
