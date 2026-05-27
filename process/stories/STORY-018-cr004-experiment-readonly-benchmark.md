---
story_id: "STORY-018"
title: "CR-004 实验十/十二只读接入与真实沪深 300 基准路线"
story_slug: "cr004-experiment-readonly-benchmark"
status: "lld-approved"
priority: "P1"
wave: "CR4-W4"
depends_on: ["STORY-016", "STORY-017"]
dependency_contracts:
  - upstream: "STORY-016"
    type: "runtime"
    required: "reader 可只读 canonical/gold parquet"
  - upstream: "STORY-017"
    type: "contract"
    required: "CLI/comparison contract frozen for operational smoke and diagnostics"
file_ownership:
  primary:
    - "market_data/benchmarks.py"
    - "experiments/run_experiment_10.py"
    - "experiments/run_experiment_12.py"
    - "tests/test_market_data_experiment_readers.py"
  shared: []
  merge_owner: "STORY-018"
  forbidden:
    - "engine/**"
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "delivery/**"
    - "data/**"
    - "reports/**"
    - "real data"
    - "credentials"
lld_gate:
  required_inputs:
    - "process/HLD.md#217-关键流程"
    - "process/HLD.md#2112-cp3cp4cp5-门控建议与开放问题"
    - "process/ARCHITECTURE-DECISION.md#adr-009回测与实验主路径只读-market_data-数据湖"
    - "process/ARCHITECTURE-DECISION.md#adr-012多源校验先稳定接口真实多源比对后置启用"
    - "process/stories/STORY-018-cr004-experiment-readonly-benchmark.md"
  status: "approved"
  lld_path: "process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md"
  cp5_precheck: "process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md"
  cp5_review: "checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  cp5_status: "approved"
  dev_gate: "cp5_approved"
  implementation_allowed: true
  confirmed_by: "user"
  confirmed_at: "2026-05-17T15:53:20+08:00"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
---

# STORY-018：CR-004 实验十/十二只读接入与真实沪深 300 基准路线

## 目标

为实验十和实验十二设计并实现 `market_data` reader 只读接入路径，同时定义真实沪深 300 基准数据的 gold/canonical 只读契约；默认实验入口不联网，旧 `--data-dir` 路径可回退。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR-004-AC-008；继承 REQ-016、REQ-034、REQ-057 |
| HLD | §21.7 关键流程；§21.9 风险与应对；§21.12 CP3/CP4/CP5 门控建议与开放问题 |
| ADR | ADR-009, ADR-012 |

## 开发上下文（dev_context）

**背景说明**：`experiments/run_experiment_10.py` 和 `experiments/run_experiment_12.py` 当前通过既有 `engine.data_loader` 读取 `data/` 下 parquet。CR-004 不要求立即删除旧路径；本 Story 只新增或调整只读 reader 接入，使实验可以显式读取 `market_data` canonical/gold，同时不在实验入口触发 connector/runtime。

**输入文件**：STORY-016/017 Story 与 LLD、`market_data/readers.py`、`market_data/catalog.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`。

**输出文件**：`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`tests/test_market_data_experiment_readers.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| `load_market_data_for_backtest(...)` 或等价 reader adapter | lake_root、dataset、date range、symbols | `close_df` + metadata | 只读 canonical；不得调用 connector |
| `load_hs300_benchmark(...)` | gold/canonical benchmark dataset path、date range | benchmark series/metrics input | 缺失时结构化返回 unavailable，不联网下载 |
| 实验十参数 | 保留旧 `--data-dir`，可新增 `--market-data-root` 或等价显式开关 | 实验报告 | 默认不改变旧行为；启用新 reader 时只读 |
| 实验十二参数 | 同上 | 分段报告 | 市场状态标签仍不由联网自动识别 |

**设计约束**：

- 实验入口不得 import `market_data.connectors` 或 `market_data.runtime`。
- 真实沪深 300 基准数据由 gold/canonical 文件或显式本地 fixture 提供，缺失时结构化提示或按 LLD 明确降级；不得静默等权代理，不得联网下载。
- 不删除旧 `--data-dir` 和 `quality_report` 兼容路径，除非用户在 CP5 明确批准。
- 不修改 `engine/**`。
- 不提交真实基准 parquet。

**命名规范**：benchmark dataset 建议命名 `hs300_index` 或 `benchmark_hs300`，最终名称需在 LLD 中固定；实验参数使用明确名称，避免与旧 `--data-dir` 混淆。

**平台目标**：本地研究实验脚本的只读数据源接入。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| STORY-016 | runtime | reader API、catalog 和 quality 输出已冻结 | STORY-016 verified 后开发 | 实验只读依赖 reader 实际可用 |
| STORY-017 | contract | CLI/comparison 诊断口径已冻结 | STORY-017 contract frozen；因共享实验文件，开发不得与其他实验改造并行 | 实验可引用 CLI/quality 诊断输出 |

### 文件系统布局

```text
market_data/
└── readers.py  # 只读消费，不修改
experiments/
├── run_experiment_10.py
└── run_experiment_12.py
tests/
└── test_market_data_experiment_readers.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S018-T1 | 修改 | `experiments/run_experiment_10.py` | 新增显式 market_data reader/canonical/gold 只读入口，保留旧 `--data-dir` 回退 |
| S018-T2 | 修改 | `experiments/run_experiment_12.py` | 新增显式 market_data reader/canonical/gold 只读入口，保留旧 `--data-dir` 回退 |
| S018-T3 | 创建 | `tests/test_market_data_experiment_readers.py` | 覆盖实验入口不导入 connector/runtime、缺基准结构化降级、旧路径兼容、无网络和缓存扫描 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_experiment_readers.py`；必要时运行实验脚本的 `--help` 或小样本 dry-run。

**验证方式**：单元测试 + monkeypatch 确认 no-network/no-connector + 小样本 canonical fixture。

**依赖环境**：Python 3.11、uv、pytest、pandas、pyarrow；不需要真实沪深 300 数据。

**关键验证场景**：

- 实验十启用 market_data reader 时只读 canonical。
- 实验十二启用 market_data reader 时只读 canonical。
- 缺少真实沪深 300 基准 gold/canonical 时，不联网，输出结构化 unavailable 或按 LLD 显式降级；不得静默等权代理。
- 旧 `--data-dir` 路径仍可用。

## 量化验收标准（acceptance_criteria）

- [ ] 两个实验入口均不存在对 connector/runtime 的直接导入。
- [ ] 启用 `market_data` reader 的测试网络调用次数为 0。
- [ ] 旧 `--data-dir` 参数或等价兼容入口仍保留。
- [ ] 真实沪深 300 基准缺失时不会联网下载，且报告或返回对象明确标记 `benchmark_status=unavailable` 或等价状态。
- [ ] 至少 1 个小样本 canonical fixture 可驱动实验 reader 路径。
- [ ] 不修改 `engine/**`、`delivery/**`，不提交真实行情或凭据。

## 后续 LLD 输入约束

LLD 必须明确实验参数命名、兼容策略、真实基准 dataset 名称、缺失基准降级文案、对现有报告字段的影响和回滚方式。本轮 LLD 允许设计新增 `market_data/benchmarks.py` 作为只读 benchmark resolver，但不得在其中联网、抓取真实数据或生成 benchmark 文件。

## 阻塞说明

真实沪深 300 基准采用指数收盘价、全收益指数还是其他可复现本地 gold 数据仍为 OPEN。该问题不阻塞只读接入框架，但阻塞“真实基准已接入”的表述和验收；LLD 必须禁止静默等权代理。

## CP5 Batch D 状态

2026-05-17，meta-dev 已起草 `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md`，并已由用户在 CP5 Batch D 回复“通过”。后续实现只允许按 LLD 限定范围修改 `market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py` 和 `tests/test_market_data_experiment_readers.py`；不得联网抓取真实沪深 300，不得静默使用代理基准，不得写真实 `data/**`、`reports/**`、`delivery/**`。
