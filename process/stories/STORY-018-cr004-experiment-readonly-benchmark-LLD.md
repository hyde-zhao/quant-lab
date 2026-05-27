---
story_id: "STORY-018"
title: "CR-004 实验十/十二只读接入与真实沪深 300 基准路线"
story_slug: "cr004-experiment-readonly-benchmark"
lld_version: "1.1"
tier: "M"
status: "confirmed"
confirmed: true
implementation_allowed: true
dev_gate: "cp5_approved"
created_by: "meta-dev"
created_at: "2026-05-17"
confirmed_by: "user"
confirmed_at: "2026-05-17T15:53:20+08:00"
shared_fragments:
  - "process/HLD.md#21-cr-004-可迁移市场数据组件增量设计"
  - "process/HLD.md#21.7-关键流程"
  - "process/HLD.md#21.9-风险与应对"
  - "process/ARCHITECTURE-DECISION.md#ADR-009"
  - "process/ARCHITECTURE-DECISION.md#ADR-012"
  - "process/stories/STORY-016-cr004-canonical-validation-readers-LLD.md"
  - "process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md"
  - "process/constraints/CR004-QUALITY-DATALOADER-CONFIRMATION-CONSTRAINTS-2026-05-17.md"
open_items: 1
source_story: "process/stories/STORY-018-cr004-experiment-readonly-benchmark.md"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
cp5_batch: "D"
depends_on:
  - "process/stories/STORY-016-cr004-canonical-validation-readers.md"
  - "process/stories/STORY-016-cr004-canonical-validation-readers-LLD.md"
  - "process/checks/CP7-STORY-016-cr004-canonical-validation-readers-VERIFICATION-DONE.md"
  - "process/stories/STORY-017-cr004-cli-offline-comparison.md"
  - "process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md"
dependency_type: "runtime+contract"
---

# LLD: STORY-018 - CR-004 实验十/十二只读接入与真实沪深 300 基准路线

> 本文档已通过 CP5 Batch D 人工确认。后续只能按本 LLD 限定范围修改实验脚本、`market_data/benchmarks.py` 和专用测试；仍禁止联网抓取真实沪深 300、写真实数据、写真实报告或修改交付目录。
>
> 本 Story 只设计实验十/十二的只读接入与真实沪深 300 基准路线；不得真实抓取数据，不得联网补齐基准，不得静默使用等权代理冒充真实基准。

## 0. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.1 | 2026-05-17 | meta-po | 回填 CP5 Batch D 人工确认结果：用户回复“通过”，允许后续按本 LLD 限定范围实现实验十/十二只读接入与基准 unavailable 路线；仍禁止真实抓取、联网补齐和静默代理基准。 |
| 1.0 | 2026-05-17 | meta-dev | 基于 STORY-018、STORY-016/017 verified/confirmed 事实、HLD §21、ADR-009/012 和 CR-004 Data Loader/quality 约束起草 CP5 Batch D LLD；范围限定实验十/十二只读 reader/canonical/gold 接入、真实沪深 300 缺失结构化 unavailable、旧 `--data-dir` 兼容和 no-network 测试设计。 |

## 1. Goal

为 `experiments/run_experiment_10.py` 和 `experiments/run_experiment_12.py` 设计显式只读 market data 接入路径，使实验可以在不联网、不抓取真实行情、不写数据湖的前提下读取已存在的 `market_data` canonical/gold 或显式本地 fixture。

本 Story 的目标不是生成真实沪深 300 数据，而是固定实验入口如何识别、读取、缺失披露和降级处理真实沪深 300 基准。真实基准缺失时必须结构化返回 `benchmark_status=unavailable` 或按本 LLD 明确跳过基准相对指标；不得静默退回等权代理、不得自动 fetch、不得调用 connector/runtime。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 实验十和实验十二保留旧 `--data-dir` 参数和既有本地 parquet 读取路径，作为兼容回退；不得在本 Story 删除旧参数。
- 新增显式 market_data 只读参数设计，例如 `--market-data-root`、`--market-data-dataset prices`、`--benchmark-dataset hs300_index`、`--benchmark-path`、`--allow-benchmark-unavailable`。
- 启用 `--market-data-root` 后，实验入口只能通过 `market_data.readers` 读取 canonical/gold parquet 或 catalog；不得导入 `market_data.connectors`、`market_data.runtime`、真实 adapter 或网络客户端。
- 真实沪深 300 基准第一版 dataset 名称固定为 `hs300_index`；若从本地 fixture 读取，可通过 `--benchmark-path` 显式指定。
- 基准读取结果必须输出结构化状态：`benchmark_status`、`benchmark_source`、`benchmark_dataset`、`benchmark_path`、`benchmark_unavailable_reason`。
- 缺少真实沪深 300 gold/canonical/fixture 时，不联网、不自动生成、不静默使用等权代理；默认行为是结构化 unavailable，并跳过基准相对指标或按 `--require-benchmark` 失败。
- 实验报告或结果 metadata 必须披露 `data_source_mode`、`market_data_root`、`dataset`、`quality_status`、`quality_source`、`is_pit_universe`、`survivorship_bias_note`（若 reader metadata 提供）。
- 本 Story 允许新增 `market_data/benchmarks.py` 作为只读 benchmark resolver；不修改 Data Loader、CLI、comparison、多源真实比对、market_data connector/runtime/storage、真实数据目录或安装脚本。

### 2.2 Non-Functional

- 默认实验入口网络调用次数为 0；测试必须用 `tmp_path` 下的 fake/offline canonical、gold 或 fixture。
- 不提交真实沪深 300 parquet、真实行情、凭据、token、缓存、`__pycache__` 或 `*.pyc`。
- 不修改 `engine/**`、`market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`data/**`、`reports/**`、`delivery/**`、`pyproject.toml`、`uv.lock`。
- CP5 批准前不得实现；若实现阶段发现需要新增 `market_data/benchmarks.py`、真实数据准备或 CLI 参数改动超出本 LLD，必须回到 CP5 修订。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| Experiment 10 Adapter / `experiments/run_experiment_10.py` | 在实验十参数层新增显式只读数据源选择，复用已有实验逻辑输入形态 | 保留旧 `--data-dir`；不联网 |
| Experiment 12 Adapter / `experiments/run_experiment_12.py` | 在实验十二参数层新增同等只读数据源选择和基准状态披露 | 保留旧 `--data-dir`；不自动识别市场状态 |
| Market Data Reader Boundary | 只读调用 `market_data.readers` 已验证 API | 本 Story 不修改 reader；只消费 |
| Benchmark Resolver / `market_data/benchmarks.py` | 定义 `resolve_hs300_benchmark(...)` 等只读 resolver：优先显式 `--benchmark-path`，其次 `hs300_index` gold/canonical，缺失则 unavailable | 不联网、不调用 connector/runtime、不生成真实基准文件 |
| Tests / `tests/test_market_data_experiment_readers.py` | 设计只读边界、旧参数兼容、缺基准 unavailable、无网络和缓存扫描测试 | 本轮只设计，不创建测试实现 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `market_data/benchmarks.py` | 设计本地只读沪深 300 benchmark resolver、状态对象和 unavailable/required_missing 错误边界 |
| 修改 | `experiments/run_experiment_10.py` | 设计新增显式 `market_data` 只读入口、参数解析、reader adapter、基准 resolver 和 metadata 披露 |
| 修改 | `experiments/run_experiment_12.py` | 设计新增同款只读入口、分段实验 metadata 披露和基准 unavailable 处理 |
| 创建 | `tests/test_market_data_experiment_readers.py` | 设计覆盖第 10 节测试场景 |

明确不修改：`market_data/readers.py`、`market_data/catalog.py`、`market_data/cli.py`、`market_data/comparison.py`、`market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`engine/**`、`data/**`、`reports/**`、`delivery/**`、`pyproject.toml`、`uv.lock`。

## 5. 数据模型与持久化设计

### 5.1 ExperimentDataSourceConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `data_source_mode` | str | `legacy_data_dir` | `legacy_data_dir` 或 `market_data_readonly` |
| `data_dir` | Path | 既有默认值 | 旧 `--data-dir` 兼容入口 |
| `market_data_root` | Path \| None | `None` | 显式启用只读 market_data reader |
| `dataset` | str | `prices` | 第一版只读 prices canonical |
| `start_date` / `end_date` | str | 实验既有参数 | 传给 reader 和基准 resolver |
| `symbols` | list[str] | 实验既有股票池 | 可为空；为空时沿用实验既有逻辑 |

### 5.2 BenchmarkConfig

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `benchmark_dataset` | str | `hs300_index` | 真实沪深 300 本地 dataset 名称 |
| `benchmark_path` | Path \| None | `None` | 显式本地 fixture/gold/canonical 路径，优先级最高 |
| `require_benchmark` | bool | `false` | true 时缺基准结构化失败；false 时 unavailable 并跳过相对基准指标 |
| `allow_benchmark_unavailable` | bool | `true` | 只影响是否继续实验；不允许静默代理 |

### 5.3 BenchmarkStatus

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `benchmark_status` | str | 是 | `available`、`unavailable`、`required_missing` |
| `benchmark_source` | str | 是 | `explicit_path`、`market_data_gold`、`market_data_canonical`、`none` |
| `benchmark_dataset` | str | 是 | 固定默认 `hs300_index` |
| `benchmark_path` | str | 可空 | 实际读取路径或空 |
| `benchmark_unavailable_reason` | str | 可空 | 缺文件、缺 dataset、reader error 等结构化原因 |
| `benchmark_is_proxy` | bool | 是 | 本 Story 真实基准路径必须为 `false`；不得静默代理 |

持久化说明：本 Story 不新增持久化数据模型，不写真实数据湖，不生成真实 reports。实验运行若已有输出报告，后续实现只能在既有实验输出中追加 metadata 字段；测试写入必须使用 `tmp_path`。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `parse_experiment_data_args(parser)` | argparse parser | parser | 两个实验脚本 | 追加兼容参数；不删除旧 `--data-dir` |
| `load_experiment_prices(config)` | `ExperimentDataSourceConfig` | `close_df` + metadata | 实验十/十二 | `legacy_data_dir` 走旧路径；`market_data_readonly` 调 reader |
| `resolve_hs300_benchmark(config)` | `BenchmarkConfig` + date range | benchmark series + `BenchmarkStatus` | `market_data/benchmarks.py`、实验十/十二 | 只读本地 path/gold/canonical；缺失 unavailable |
| `build_experiment_data_metadata(...)` | reader metadata + benchmark status | dict | 实验输出层 | 披露质量、PIT、survivorship、benchmark 状态 |
| 实验十 CLI | 旧参数 + 新只读参数 | 实验十结果 | 用户/测试 | 默认不改变旧行为 |
| 实验十二 CLI | 旧参数 + 新只读参数 | 实验十二结果 | 用户/测试 | 默认不改变旧行为 |

错误暴露策略：

- `ExperimentDataSourceError`：reader 缺失 canonical、dataset 不存在、字段不满足实验输入时触发；不自动 fetch。
- `BenchmarkUnavailable`：`require_benchmark=false` 时作为结构化状态返回，不抛出阻断错误。
- `BenchmarkRequiredMissingError`：`require_benchmark=true` 且基准缺失时触发，错误包含 dataset/path/reason。
- `ExperimentNetworkBoundaryError`：测试发现导入 connector/runtime/网络客户端或发生网络调用时触发。

## 7. 核心处理流程

1. 实验脚本解析参数；若未传 `--market-data-root`，保留旧 `--data-dir` 读取路径和既有行为。
2. 若传入 `--market-data-root`，构造 `ExperimentDataSourceConfig(data_source_mode="market_data_readonly")`。
3. `load_experiment_prices` 只读调用 `market_data.readers.read_canonical(dataset="prices", ...)` 或等价 verified reader API，转换为实验既有 `close_df` 输入形态。
4. `resolve_hs300_benchmark` 先检查显式 `--benchmark-path`，再尝试本地 `hs300_index` gold/canonical；所有路径都缺失时返回 `benchmark_status=unavailable`。
5. 缺基准且 `--require-benchmark=true` 时结构化失败；缺基准且未 require 时继续运行非基准相对指标，并在 metadata 中标明 unavailable。
6. 实验输出 metadata 追加 reader quality/PIT/non-PIT 披露和 benchmark status。
7. 全流程不调用 connector/runtime，不写数据湖，不联网，不真实抓取数据。

异常路径：

- `--market-data-root` 指向不存在路径：结构化失败或 unavailable，不回退真实联网。
- canonical prices 缺失：结构化失败，不自动 fetch/normalize。
- hs300 基准缺失：结构化 unavailable；不静默使用等权代理。
- 旧 `--data-dir` 路径：继续使用旧逻辑，不强制走 market_data reader。

## 8. 技术设计细节

- 参数兼容：
  - 保留旧 `--data-dir`，默认行为不变。
  - 新增 `--market-data-root` 作为显式 opt-in；传入后才启用 reader。
  - 新增 `--benchmark-path` 支持测试 fixture 或用户本地 gold 文件。
  - 新增 `--require-benchmark` 用于要求基准必须存在；默认不要求，但缺失必须披露 unavailable。
- 基准 dataset：
  - 默认名称固定为 `hs300_index`。
  - 第一版不区分价格指数、全收益指数或复权口径的真实选择；该问题保留 OPEN，不得宣称真实基准已接入。
- 不静默代理：
  - 等权组合、同股票池均值或旧实验 proxy 可以作为旧逻辑指标存在，但不得在 `benchmark_status` 中标记为真实沪深 300。
  - 若旧逻辑仍输出 proxy 字段，必须与 `hs300_index` benchmark 字段分离。
- reader 边界：
  - 实验脚本不得 import `market_data.connectors`、`market_data.runtime`、`market_data.storage` 或真实 adapter。
  - 不允许调用 `market_data.cli fetch/normalize/validate` 自动补齐数据。
- quality 披露：
  - 实验只消费 reader/catalog/quality metadata，不重新判定 Data Loader 质量门。
  - 若 metadata 中存在 `quality_status=fail`，实验应结构化提示数据不可用；是否阻断由后续实现按实验既有错误路径处理，不能自动修复。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 实验入口不导入 connector/runtime/storage/真实 adapter/网络客户端 | 静态扫描 + monkeypatch |
| 安全 | 不记录凭据、不读取环境 token、不输出绝对隐私路径 | stderr/stdout metadata 断言 |
| 只读 | market_data 模式只读 canonical/gold/fixture，不写数据湖 | `tmp_path` 文件快照 |
| 可追溯 | metadata 输出 `data_source_mode`、dataset、quality、benchmark status | 单元测试断言 |
| 性能 | 只读取请求日期/列/symbols 范围；不做真实远程查询 | 小样本 fixture smoke |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| `T018-HELP-01` 参数兼容 | 实验脚本可导入 | 运行 help/parser 构造 | 旧 `--data-dir` 和新参数同时存在 | 单元测试 |
| `T018-LEGACY-DATADIR-01` 旧路径保留 | `tmp_path` legacy parquet fixture | 调用旧 `--data-dir` 路径 | 不要求 `market_data_root`，旧行为可用 | 单元测试 |
| `T018-READER-PRICE-01` reader 只读价格 | `tmp_path` canonical prices fixture | 启用 `--market-data-root` | 返回实验输入 `close_df`，metadata `data_source_mode=market_data_readonly` | 单元测试 |
| `T018-BENCHMARK-PATH-01` 显式本地基准 | `tmp_path` benchmark fixture | 传 `--benchmark-path` | `benchmark_status=available`、source=`explicit_path` | 单元测试 |
| `T018-BENCHMARK-MISSING-01` 缺真实基准 | 无 hs300 gold/canonical/fixture | 调用 resolver | `benchmark_status=unavailable`，不联网，不静默代理 | 单元测试 |
| `T018-BENCHMARK-REQUIRED-01` 缺基准且 require | 无基准，`--require-benchmark=true` | 调用 resolver | 结构化 `BenchmarkRequiredMissingError` | 单元测试 |
| `T018-NO-CONNECTOR-IMPORT-01` 禁止 connector/runtime | 源码存在 | 静态扫描实验脚本 | 不导入 `market_data.connectors`、`runtime`、`storage` | 静态测试 |
| `T018-NO-NETWORK-01` 无网络 | monkeypatch 网络客户端为失败 | 运行 reader/benchmark 路径 | 网络调用次数 0 | 单元测试 |
| `T018-NO-WRITE-LAKE-01` 不写数据湖 | `tmp_path` lake 快照 | 运行实验只读路径 | canonical/gold/catalog 未新增或修改 | 文件系统断言 |
| `T018-METADATA-01` 披露字段 | reader metadata 含 quality/non-PIT | 构造实验结果 metadata | 输出 quality、PIT、survivorship、benchmark status 字段 | 单元测试 |
| `T018-CACHE-SCAN-01` 缓存扫描 | 仓库工作区 | 扫描 `__pycache__`、`*.pyc`、`.ipynb_checkpoints` | 不因本 Story 引入缓存文件 | CP6/CP7 检查 |

本轮不运行测试；以上仅为实现后的可执行测试设计。

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| S018-T1 | 创建 | `market_data/benchmarks.py` | 实现只读 `resolve_hs300_benchmark(...)`、`BenchmarkStatus`、`BenchmarkUnavailable` / `BenchmarkRequiredMissingError`；不联网、不生成真实数据 | `T018-BENCHMARK-PATH-01`, `T018-BENCHMARK-MISSING-01`, `T018-BENCHMARK-REQUIRED-01`, `T018-NO-CONNECTOR-IMPORT-01`, `T018-NO-NETWORK-01` |
| S018-T2 | 修改 | `experiments/run_experiment_10.py` | 追加只读数据源参数、reader adapter、基准 resolver 调用和 metadata 披露；保留旧 `--data-dir` | `T018-HELP-01`, `T018-LEGACY-DATADIR-01`, `T018-READER-PRICE-01`, `T018-METADATA-01` |
| S018-T3 | 修改 | `experiments/run_experiment_12.py` | 追加同款只读数据源参数、分段输出 metadata、缺基准 unavailable 处理；保留旧 `--data-dir` | `T018-HELP-01`, `T018-LEGACY-DATADIR-01`, `T018-BENCHMARK-MISSING-01` |
| S018-T4 | 创建 | `tests/test_market_data_experiment_readers.py` | 实现旧路径兼容、reader 只读、显式基准、缺基准、no-network、no-import、no-write 和缓存扫描测试 | 第 10 节全部测试 |

## 12. 风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 真实沪深 300 基准口径未最终确定 | 无法宣称真实基准已接入 | 先固定 dataset 名称和 unavailable 结构；真实数据准备后再确认口径 |
| 实验脚本当前输入形态可能与 reader DataFrame 不完全一致 | 实现时需要轻量转换 | 转换仅在实验脚本内完成，不修改 reader，不改 Data Loader |
| 旧 proxy 指标可能被误读为真实沪深 300 | 结果解释错误 | 强制 `benchmark_is_proxy=false` 仅用于真实路径；proxy 字段必须另名披露 |
| 缺基准继续运行可能弱化比较结论 | 用户误判实验有效性 | metadata 和报告必须输出 unavailable，并跳过基准相对指标 |

### OPEN / Spike 跟踪

| ID | 类型 | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| O-01 | OPEN | 真实沪深 300 基准采用价格指数、全收益指数、复权指数或其他本地 gold 口径尚未确认 | CP5 可接受本 Story 先交付只读路线和 unavailable 结构；真实基准数据准备与口径确认后再实现 available 路径 | meta-po / 用户 |

## 13. 回滚与发布策略

- 发布方式：CP5 批准后才允许按第 11 节限定文件实现；默认通过 `python experiments/run_experiment_10.py ...` / `python experiments/run_experiment_12.py ...` 既有入口使用，不新增安装脚本。
- 回滚触发条件：旧 `--data-dir` 兼容破坏、实验入口联网、导入 connector/runtime、缺基准静默代理、写真实数据湖或修改禁止文件。
- 回滚动作：撤回 `market_data/benchmarks.py`，撤回两个实验脚本中的 STORY-018 新参数和 adapter，删除 `tests/test_market_data_experiment_readers.py` 中本 Story 测试；保留 STORY-016/017 已验证实现和真实数据目录不变。
- 降级策略：若 market_data reader 不可用，用户仍可使用旧 `--data-dir`；若基准不可用，输出 structured unavailable，不输出真实基准相对指标。

## 14. Definition of Done

- [x] 14 个章节全部填写完成，且包含人工确认区。
- [x] frontmatter 包含 `tier`、`shared_fragments`、`open_items`、`change_id`、`cp5_batch`、`confirmed=true`、`implementation_allowed=true`、`dev_gate=cp5_approved`。
- [x] 文件影响范围只包含 `market_data/benchmarks.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`tests/test_market_data_experiment_readers.py`。
- [x] 明确实验入口不得联网，不得调用 connector/runtime，不得自动 fetch/normalize/validate。
- [x] 明确真实沪深 300 基准不抓取，缺失时结构化 unavailable，不静默代理基准。
- [x] 明确旧 `--data-dir` 兼容保留。
- [x] 测试设计覆盖只读 reader、旧路径、缺基准、no-network、no-import、no-write、metadata 和缓存扫描。
- [x] CP5 Batch D 已于 2026-05-17T15:53:20+08:00 经用户回复“通过”确认；后续仅允许按本 LLD 限定范围实现。

## 人工确认区

> **元工作流检查点 CP5 - CR-004 Batch D STORY-018 LLD 确认**
> meta-po 发起，用户确认后方可进入实现。

**确认选项**：

1. **批准** - LLD 设计合理，允许后续按限定范围实现。
2. **需要修改** - 指出具体修改点后由 meta-dev 更新重提。
3. **拒绝** - 设计方向有根本问题，需重新设计。
