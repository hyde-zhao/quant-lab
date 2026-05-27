---
story_id: "STORY-015"
title: "CR-004 connector runtime 与 raw/manifest 写入"
story_slug: "cr004-connector-runtime-raw-manifest"
status: "verified"
priority: "P0"
wave: "CR4-W1"
depends_on: ["STORY-014"]
dependency_contracts:
  - upstream: "STORY-014"
    type: "contract"
    required: "market_data schema/source registry/lake layout frozen"
file_ownership:
  primary:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "tests/test_market_data_runtime_storage.py"
  shared:
    - "market_data/contracts.py"
    - "market_data/source_registry.py"
  merge_owner: "STORY-015"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "delivery/**"
    - "real data"
    - "credentials"
lld_gate:
  required_inputs:
    - "process/HLD.md#216-真实-adapter-边界"
    - "process/ARCHITECTURE-DECISION.md#adr-010真实联网-adapter-默认关闭fakeoffline-为默认测试路径"
    - "process/stories/STORY-015-cr004-connector-runtime-raw-manifest.md"
  status: "approved-with-constraints"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  cp5_status: "approved-with-constraints"
  implementation_status: "completed"
  verification_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-STORY-015-cr004-connector-runtime-raw-manifest-VERIFICATION-DONE.md"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
---

# STORY-015：CR-004 connector runtime 与 raw/manifest 写入

## 目标

实现 `market_data` 的 fake/offline connector、真实 TickFlow/AkShare/Tushare adapter 边界、限速/重试/熔断 runtime 和 raw/manifest 写入闭环。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR-004-AC-002, CR-004-AC-003；继承 REQ-047 至 REQ-055 |
| HLD | §21.3 推荐架构总览；§21.6 真实 adapter 边界；§21.7 关键流程 |
| ADR | ADR-010, ADR-011 |

## 开发上下文（dev_context）

**背景说明**：CR-004 的默认获取路径必须完全 fake/offline；真实 adapter 只允许提供协议边界、显式启用和 fail-fast，不能在默认测试或实验入口中联网。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/stories/STORY-014-cr004-market-data-package-lake-contracts.md`、`market_data/contracts.py`、`market_data/source_registry.py`、`market_data/lake_layout.py`。

**输出文件**：`market_data/connectors/__init__.py`、`market_data/connectors/protocol.py`、`market_data/connectors/fake.py`、`market_data/connectors/akshare.py`、`market_data/connectors/tushare.py`、`market_data/connectors/tickflow.py`、`market_data/runtime.py`、`market_data/storage.py`、`tests/test_market_data_runtime_storage.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `ConnectorProtocol.fetch(interface, params)` | interface、params | `ConnectorResult` 或 `ConnectorError` | 错误含 `error_type`、`error_message`、`retryable`、`source`、`interface` |
| fake connector | seed、symbols、date_range、failure_plan | deterministic rows / partial failure | 不联网，不读取真实数据 |
| real adapter boundary | source config、allowlist、credentials ref | 结构化 fail-fast 或显式真实结果 | 默认 disabled；缺凭据、未 allowlist、unresolved 均非重试失败 |
| runtime | batch plan、connector、policy、clock/sleeper | batch execution result | `max_retries` 有上限；熔断打开后停止后续请求 |
| storage | batch result、lake layout | raw file、manifest record | 写入前检查父路径；不写真实生产行情 fixture |

**设计约束**：

- 默认测试和 CLI 示例只使用 fake connector。
- `akshare.py` 可延迟导入 AkShare，但不得在模块 import 时联网或加载真实接口。
- `tushare.py`、`tickflow.py` 在缺少已确认接口和凭据时必须 fail fast。
- raw 写入建议为 JSONL 或 parquet 之外的原始响应格式，第一行或 metadata 必须包含 batch 信息。
- manifest 必须 append-only 或等价可审计，记录 status、attempts、raw_path、canonical_path 或空占位。

**命名规范**：connector source 使用 exact 字符串：`fake`、`akshare`、`tushare`、`tickflow`；状态枚举与 STORY-014 契约一致；测试 fixture 使用 `tmp_path`。

**平台目标**：本地 offline 默认数据准备运行时。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| STORY-014 | contract | `market_data` schema/source registry 已在 Story 或 LLD 中冻结 | STORY-014 CP5 通过，且共享契约修改由 STORY-015 合并 | 本 Story 消费包骨架、source registry 和 lake layout |

### 文件系统布局

```text
market_data/
├── connectors/
│   ├── __init__.py
│   ├── protocol.py
│   ├── fake.py
│   ├── akshare.py
│   ├── tushare.py
│   └── tickflow.py
├── runtime.py
└── storage.py
tests/
└── test_market_data_runtime_storage.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S015-T1 | 创建 | `market_data/connectors/protocol.py` | 定义 connector result/error/protocol |
| S015-T2 | 创建 | `market_data/connectors/fake.py` | 实现 deterministic fake rows、失败、部分成功和 reference 数据 |
| S015-T3 | 创建 | `market_data/connectors/akshare.py`, `tushare.py`, `tickflow.py` | 实现真实 adapter 边界、显式启用校验和 fail-fast |
| S015-T4 | 创建 | `market_data/runtime.py` | 实现限速、有限重试、熔断和 fake clock/sleeper 注入 |
| S015-T5 | 创建 | `market_data/storage.py` | 实现 raw 写入、manifest append 和路径父级校验 |
| S015-T6 | 创建 | `tests/test_market_data_runtime_storage.py` | 覆盖 fake 成功/失败/重试/熔断/raw/manifest/真实源默认关闭 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_runtime_storage.py`；静态扫描确认默认测试不调用真实网络。

**验证方式**：单元测试 + fake clock/sleeper + 临时目录。

**依赖环境**：Python 3.11、uv、pytest；不需要真实 AkShare/Tushare/TickFlow 账号。

**关键验证场景**：

- fake connector 成功写出 raw + manifest。
- retryable error 最多重试 `max_retries` 次。
- non-retryable error 不重试。
- 熔断打开后后续批次不调用 connector。
- AkShare/Tushare/TickFlow 默认 disabled 时 fail fast。

## 量化验收标准（acceptance_criteria）

- [ ] fake connector 在相同 seed、symbols、date_range 下输出 deterministic raw。
- [ ] 每个批次 manifest 至少记录 12 个字段，含 source/interface/params/status/attempts/raw_path/canonical_path。
- [ ] runtime 对同一批次最多执行 `1 + max_retries` 次请求。
- [ ] 熔断状态可由测试触发，且触发后剩余批次状态为 skipped 或 failed 等明确状态。
- [ ] 默认测试网络调用次数为 0，且不需要任何 token/API key。
- [ ] 真实 adapter 未显式启用时返回非重试结构化错误。
- [ ] 不修改 `engine/**`、`experiments/**`、`delivery/**`，不写真实数据。

## 后续 LLD 输入约束

LLD 必须明确 retry/backoff/circuit breaker 状态机、manifest 写入原子性、raw 文件格式、真实 adapter 配置字段和错误枚举。真实 TickFlow/Tushare exact API 未确认前，LLD 只能设计 fail-fast adapter boundary。

## 阻塞说明

`TickFlow` exact API、Tushare token 策略和真实接口配额仍为 OPEN；该问题不阻塞 fake/offline runtime，实现中不得猜测真实接口。

## 开发状态记录

| 日期 | 状态 | 说明 |
|---|---|---|
| 2026-05-17 | ready-for-verification | CP5 批次 A 已带约束通过；已按 LLD 实现 connector protocol、fake connector、真实 adapter fail-fast、runtime、raw/manifest storage、resume/幂等和运行时测试，等待 CP7 验证。 |
