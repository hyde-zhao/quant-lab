---
story_id: "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
title: "raw / adj_factor / qfq / hfq / returns_adjusted publish readiness"
story_slug: "adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
status: "verified"
priority: "P0"
wave: "CR018-W2-P0-P1-READINESS"
depends_on:
  - "CR018-S01-production-current-truth-definition-and-dataset-groups"
  - "CR017-S05-validation-quality-parity-and-leakage-tests"
dependency_type:
  - upstream: "CR018-S01-production-current-truth-definition-and-dataset-groups"
    type: "contract"
  - upstream: "CR017-S05-validation-quality-parity-and-leakage-tests"
    type: "validation-contract"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr018_adjustment_publish_readiness.py"
  shared:
    - "market_data/adjustment_policy.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
  merge_owner: "CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness"
  forbidden:
    - "use adjusted price as QMT execution price"
    - "overwrite old qfq baseline"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "provider fetch"
    - "real lake write"
    - "catalog current pointer publish"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.4"
    - "process/HLD-DATA-LAKE.md#19.9"
    - "process/HLD.md#32"
    - "process/ARCHITECTURE-DECISION.md#ADR-063"
    - "process/ARCHITECTURE-DECISION.md#ADR-065"
    - "process/stories/CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
created_at: "2026-05-29"
updated_at: "2026-05-29T09:59:41+08:00"
change_id: "CR-018"
---

# CR018-S05：raw / adj_factor / qfq / hfq / returns_adjusted publish readiness

## 目标

将 CR017 复权双视图和 raw 执行价边界并入 P0 production quality gate，确保 raw、adj_factor、qfq、hfq、returns_adjusted 可追溯且不会混用为 QMT 执行价。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-129、REQ-130 |
| HLD | `process/HLD-DATA-LAKE.md` §19.4、§19.9；`process/HLD.md` §32 |
| ADR | ADR-063、ADR-065 |

## 开发上下文（dev_context）

**背景说明**：用户已明确要求前复权和后复权同时支持。当前 production publish 需要确认 raw + `adj_factor` 事实源、qfq/hfq 派生视图、returns_adjusted 和 QMT raw execution price 的边界，不允许旧 qfq baseline 被覆盖。

**输入文件**：CR017 复权合同、CR018 HLD / ADR、本 Story 卡片、`market_data/adjustment_policy.py`、`market_data/validation.py`、`market_data/readers.py`。

**输出文件**：`tests/test_cr018_adjustment_publish_readiness.py`；共享修改 `market_data/adjustment_policy.py`、`market_data/validation.py`、`market_data/readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| adjustment readiness | raw prices、adj_factor、qfq/hfq views | readiness status、factor coverage、policy metadata | 缺 factor 或混用 policy fail |
| adjusted view reader | policy、as_of_trade_date | qfq/hfq/returns_adjusted data | QMT execution consumer 只能 raw |
| publish quality hook | release_id、adjustment readiness | publish allowed / blocked | readiness fail 不得 publish |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S01 | contract | S01 dataset group 已声明即可起草 LLD | 需要 S01 合同冻结且 CP5 approved | 消费 P0 readiness group |
| CR017-S05 | validation-contract | 已 verified，可作为质量合同输入 | 开发需避免覆盖 CR017 既有合同 | 复用 CR017 quality / parity / leakage gate |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_adjustment_publish_readiness.py` | 当前 Story 独占 |
| shared | `market_data/adjustment_policy.py`、`market_data/validation.py`、`market_data/readers.py` | 与 CR017/S02/S06/S07 共享，开发默认串行 |
| forbidden | adjusted price 用作 QMT 执行价、覆盖旧 qfq、真实写湖或 publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S05-T1 | 修改 | `market_data/validation.py` | 增加复权 readiness 和 factor coverage 检查 |
| CR018-S05-T2 | 修改 | `market_data/readers.py` | 暴露 raw/qfq/hfq/returns_adjusted 读取 policy metadata |
| CR018-S05-T3 | 修改 | `market_data/adjustment_policy.py` | 衔接 CR017 policy 与 publish readiness |
| CR018-S05-T4 | 创建 | `tests/test_cr018_adjustment_publish_readiness.py` | 验证复权双视图、QMT raw-only 和 publish fail-closed |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_adjustment_publish_readiness.py`。

**验证方式**：fixture-only 合同测试。

**关键验证场景**：raw/adj_factor/qfq/hfq/returns_adjusted readiness 可追溯；复权价不能进入 QMT execution feed；缺 factor 时 publish blocked。

## 量化验收标准（acceptance_criteria）

- [ ] raw、adj_factor、qfq、hfq、returns_adjusted 5 类 readiness 字段覆盖率为 100%。
- [ ] QMT execution consumer 使用 qfq/hfq/returns_adjusted 的 allowed 次数为 0。
- [ ] 旧 qfq baseline overwrite 次数为 0。
- [ ] provider_fetch、lake_write、credential_read、current_pointer_publish 计数均为 0。

## 阻塞说明

CP5 已获批；真实发布 readiness 只可在后续 Explicit Publish Gate 中执行，不在本 Story 卡片阶段执行。
