---
story_id: "CR018-S04-industry-market-cap-liquidity-and-exposure-data"
title: "P1 行业 / 市值 / 风格 / 流动性 / 容量合同"
story_slug: "industry-market-cap-liquidity-and-exposure-data"
status: "verified"
priority: "P1"
wave: "CR018-W2-P0-P1-READINESS"
depends_on:
  - "CR018-S01-production-current-truth-definition-and-dataset-groups"
dependency_type:
  - upstream: "CR018-S01-production-current-truth-definition-and-dataset-groups"
    type: "claim-boundary"
cp5_batch: "CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "tests/test_cr018_p1_auxiliary_claim_boundary.py"
  shared:
    - "engine/research_dataset.py"
    - "market_data/readers.py"
  merge_owner: "CR018-S04-industry-market-cap-liquidity-and-exposure-data"
  forbidden:
    - "claim industry neutral or capacity ready without data"
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - "credential files or secret values"
    - "provider fetch"
    - "real lake write"
    - "QMT API operation"
lld_gate:
  required_inputs:
    - "process/HLD-DATA-LAKE.md#19.4"
    - "process/HLD-DATA-LAKE.md#19.12"
    - "process/ARCHITECTURE-DECISION.md#ADR-063"
    - "process/stories/CR018-S04-industry-market-cap-liquidity-and-exposure-data.md"
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

# CR018-S04：P1 行业 / 市值 / 风格 / 流动性 / 容量合同

## 目标

建立行业、市值、风格、流动性和容量等 P1 auxiliary availability 与 blocked claim 规则。P1 缺失不阻断 core current truth release，但必须阻断行业中性、独立 alpha、容量、scale_up 和资金放大声明。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-14 |
| 需求 | REQ-135、REQ-136 |
| HLD | `process/HLD-DATA-LAKE.md` §19.4、§19.12 |
| ADR | ADR-063 |

## 开发上下文（dev_context）

**背景说明**：低波动策略后续需要解释是否来自行业、市值、低 beta、流动性或容量暴露。但用户当前优先级是 production current truth，因此这些数据先作为 P1：缺失时不阻断 P0 release，但阻断相关研究和 QMT scale-up 声明。

**输入文件**：CR018 HLD / ADR、S01 claim matrix、本 Story 卡片、`engine/research_dataset.py`、`market_data/readers.py`。

**输出文件**：`tests/test_cr018_p1_auxiliary_claim_boundary.py`；共享修改 `engine/research_dataset.py`、`market_data/readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| auxiliary availability | industry、market_cap、float_market_cap、liquidity、style fields | availability matrix、missing reason | 缺失不得静默填充 |
| research claim boundary | requested claim、availability matrix | allowed / blocked claim | P1 缺失时中性化 / capacity / scale_up blocked |
| reader metadata | release_id、dataset availability | research metadata flags | 不扫描未发布 lake |

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR018-S01 | claim-boundary | S01 claim matrix 已声明即可起草 LLD | 需要 S01 合同冻结且 CP5 approved | S04 不阻断 P0 core release |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `tests/test_cr018_p1_auxiliary_claim_boundary.py` | 当前 Story 独占 |
| shared | `engine/research_dataset.py`、`market_data/readers.py` | 与 S08/S02/S05/S07 共享，开发默认串行 |
| forbidden | 缺数据仍声明行业中性 / 容量 ready / scale_up ready | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR018-S04-T1 | 修改 | `market_data/readers.py` | 输出 P1 availability metadata 和 blocked reason |
| CR018-S04-T2 | 修改 | `engine/research_dataset.py` | 将 P1 缺失映射到 research claim boundary |
| CR018-S04-T3 | 创建 | `tests/test_cr018_p1_auxiliary_claim_boundary.py` | 验证 P1 缺失不阻断 core release 但阻断相关 claims |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr018_p1_auxiliary_claim_boundary.py`。

**验证方式**：fixture-only 合同测试。

**关键验证场景**：P1 缺失时 core release 可继续评估；行业中性 / pure alpha / capacity / scale_up allowed 次数为 0；reader 不扫未发布 lake。

## 量化验收标准（acceptance_criteria）

- [ ] P1 缺失时中性化、pure alpha、capacity、scale_up allowed claim 输出次数为 0。
- [ ] P1 缺失时 P0 core current truth readiness 不被错误标 fail。
- [ ] 未发布 lake 被研究 reader 扫描次数为 0。
- [ ] provider_fetch、lake_write、credential_read、QMT operation 计数均为 0。

## 阻塞说明

CP5 已获批；当前仍按 DAG 等待上游 verified。若用户后续要求行业中性、容量或 scale_up 变成准入条件，应另起 CR 或在 CP5 中把 P1 升级为 P0。
