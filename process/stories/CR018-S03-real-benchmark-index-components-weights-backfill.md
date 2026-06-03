---
story_id: "CR018-S03-real-benchmark-index-components-weights-backfill"
title: "四类 benchmark 行情 / 成分 / 权重 readiness"
story_slug: "real-benchmark-index-components-weights-backfill"
status: "verified"
priority: "P0"
wave: "CR018-W2-P0-P1-READINESS"
depends_on:
  - "CR018-S01-production-current-truth-definition-and-dataset-groups"
dependency_type:
  - upstream: "CR018-S01-production-current-truth-definition-and-dataset-groups"
    type: "contract"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "market_data/benchmarks.py"
    - "tests/test_cr018_benchmark_group_readiness.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/validation.py"
  merge_owner: "CR018-S03-real-benchmark-index-components-weights-backfill"
  forbidden:
    - "proxy benchmark fields as real benchmark"
    - "market_data/connectors/**"
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
    - "process/HLD-DATA-LAKE.md#19.8"
    - "process/ARCHITECTURE-DECISION.md#ADR-064"
    - "process/stories/CR018-S03-real-benchmark-index-components-weights-backfill.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
created_at: "2026-05-29"
updated_at: "2026-05-29T09:19:23+08:00"
change_id: "CR-018"
---

# CR018-S03：四类 benchmark 行情 / 成分 / 权重 readiness

## 目标

覆盖沪深300、中证500、中证1000、中证全指的指数日行情、历史成分和权重 readiness，禁止用同股票池等权代理基准冒充真实 benchmark。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-13、UC-14 |
| 需求 | REQ-128、REQ-130、REQ-133 |
| HLD | `process/HLD-DATA-LAKE.md` §19.4、§19.8 |
| ADR | ADR-064 |

## 开发上下文（dev_context）

**背景说明**：阶段研究曾使用代理基准，不能支持“跑赢沪深300”“指数增强”“真实超额收益”等结论。production current truth 必须把四类 benchmark 的行情、成分和权重纳入 P0 readiness。

**输入文件**：CR018 HLD / ADR、S01 dataset group、本 Story 卡片、现有 benchmark / validation 合同。

**输出文件**：`market_data/benchmarks.py`、`tests/test_cr018_benchmark_group_readiness.py`；共享修改 `market_data/contracts.py`、`market_data/validation.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| benchmark registry | index_code、dataset_type | prices/components/weights readiness | 未覆盖四类 benchmark 时 fail |
| component readiness | effective_date、available_at、symbol weights | point-in-time component coverage | 当前成分不得回填历史 |
| benchmark claim boundary | proxy_benchmark、real_benchmark | claim allowed / blocked reason | proxy 字段不得写入 real benchmark |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S01 | contract | S01 Story 合同已声明即可起草 LLD | 需要 S01 合同冻结且 CP5 approved | 消费 P0 dataset group 和 release claim matrix |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `market_data/benchmarks.py`、`tests/test_cr018_benchmark_group_readiness.py` | 当前 Story 独占 |
| shared | `market_data/contracts.py`、`market_data/validation.py` | 与 S02/S06 共享，开发默认串行 |
| forbidden | proxy benchmark 冒充真实 benchmark、provider fetch、lake write、publish | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S03-T1 | 创建 | `market_data/benchmarks.py` | 定义 benchmark group、dataset type 和 readiness contract |
| CR018-S03-T2 | 修改 | `market_data/contracts.py` | 增加 benchmark readiness schema |
| CR018-S03-T3 | 修改 | `market_data/validation.py` | 增加四类 benchmark 完整性校验 |
| CR018-S03-T4 | 创建 | `tests/test_cr018_benchmark_group_readiness.py` | 验证四类 benchmark 与 proxy 隔离 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_benchmark_group_readiness.py`。

**验证方式**：fixture-only 合同测试。

**关键验证场景**：四类 benchmark 均需 prices/components/weights readiness；缺任何一类时 production benchmark claim blocked；proxy 写入 real 字段次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] HS300、ZZ500、ZZ1000、中证全指 4 类 benchmark 均输出 prices/components/weights readiness。
- [ ] proxy benchmark 写入真实 benchmark 字段次数为 0。
- [ ] benchmark 缺失时 production excess-return / index-enhancement claim allowed 次数为 0。
- [ ] provider_fetch、lake_write、credential_read、current_pointer_publish 计数均为 0。

## 阻塞说明

CP5 已获批；真实 benchmark 回补需要后续真实运行授权，不在 Story 卡片阶段执行。
