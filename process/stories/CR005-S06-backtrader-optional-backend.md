---
story_id: "CR005-S06"
title: "Backtrader optional backend"
story_slug: "backtrader-optional-backend"
status: "verified"
priority: "P1"
wave: "CR5-W5"
depends_on: ["CR005-S02", "CR005-S03", "CR005-S04"]
dependency_contracts:
  - upstream: "CR005-S02"
    type: "contract"
    required: "PIT 可得性字段、`adj_factor` 与 adjusted price normalization 契约 confirmed"
  - upstream: "CR005-S03"
    type: "runtime"
    required: "多 dataset quality/catalog/readers、PIT as-of gate、复权一致 gate verified 或 contract frozen"
  - upstream: "CR005-S04"
    type: "contract"
    required: "BenchmarkResult schema、benchmark policy 和 resolver status 契约 frozen"
file_ownership:
  primary:
    - "engine/backtrader_adapter.py"
    - "tests/test_backtrader_optional_backend.py"
  shared:
    - "engine/backtest.py"
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "pyproject.toml"
    - "uv.lock"
  merge_owner: "CR005-S06"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "TUSHARE_TOKEN"
    - "data/**"
    - "reports/**"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#22-cr-005-tushare-真实写湖与-backtrader-可选后端增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-016backtrader-作为可选后端不替代轻量主路径"
    - "process/ARCHITECTURE-DECISION.md#adr-017pit-与复权由-pandas-数据层保证backtrader-只消费干净输入"
    - "process/ARCHITECTURE-DECISION.md#adr-015沪深-300-基准优先使用本地-hs300_index"
    - "process/stories/CR005-S02-tushare-dataset-schema-normalization.md"
    - "process/stories/CR005-S03-multidataset-quality-catalog-readers.md"
    - "process/stories/CR005-S04-hs300-local-benchmark.md"
    - "process/stories/CR005-S06-backtrader-optional-backend.md"
  status: "approved"
  batch_id: "CR005-BATCH-D-S06-LLD"
  handoff: "process/handoffs/META-DEV-CR005-S06-LLD-2026-05-17.md"
  expected_lld: "process/stories/CR005-S06-backtrader-optional-backend-LLD.md"
  expected_auto_result: "process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md"
  cp5_manual_review: "checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-18T00:00:56+08:00"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "CR005-S02 PIT as-of and adjusted price contract confirmed"
    - "CR005-S03 quality gate and reader contract verified"
    - "CR005-S04 BenchmarkResult schema and benchmark policy frozen"
    - "CR005-S01 hs300 backfill job spec frozen"
  file_conflict_free: true
  cp5_required: true
  cp5_confirmed: true
  implementation_allowed: true
  implementation_handoff: "process/handoffs/META-DEV-CR005-S06-IMPLEMENT-2026-05-17.md"
created_at: "2026-05-17"
updated_at: "2026-05-18T00:23:10+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-005"
---

# CR005-S06：Backtrader optional backend

## 目标

将 Backtrader 作为 CR-005 的可选回测后端接入，只消费 Pandas 数据层已完成 PIT 对齐、复权价格生成并通过 quality gate 的 factor panel / score / OHLCV feed 以及 CR005-S04 冻结的 `BenchmarkResult`，并输出与轻量 `engine/backtest.py` 主路径的对照结果；未安装、数据不合格或 benchmark unavailable/required_missing 时结构化降级，不影响默认主路径，不触发补数。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR005-AC-011、CR005-AC-014、CR005-AC-015、CR005-AC-017、CR005-AC-019 |
| HLD | §22.6、§22.8、§22.12 |
| ADR | ADR-016、ADR-017 |

## 开发上下文（dev_context）

**背景说明**：当前 `engine/backtest.py` 是轻量主路径；`pyproject.toml` 尚无 `backtrader`；`market_data/readers.py` 在 CR005-S03 之前不具备多 dataset 消费能力。Backtrader 因此必须后置为 optional backend。PIT、复权和 benchmark availability 不得在 Backtrader adapter 内实现；PIT/复权职责必须由 CR005-S02/S03 的 Pandas 数据层完成并通过门控，benchmark availability 必须由 CR005-S04 的 `BenchmarkResult` 表达。

**输入文件**：`engine/backtest.py`、`engine/data_loader.py`、`market_data/readers.py`、`market_data/benchmarks.py`、CR005-S02/S03/S04 Story 与 LLD、`pyproject.toml`。

**输出文件**：`engine/backtrader_adapter.py`、`tests/test_backtrader_optional_backend.py`；必要时修改 `engine/backtest.py` 或 backend selector、`README.md`、`docs/USER-MANUAL.md`、`pyproject.toml`、`uv.lock`。依赖修改只能在 CP5 批次 D 人工确认后执行。

**接口约定**：

| 接口 | 输入 | 输出 | 约束 |
|---|---|---|---|
| backend selector | `backend="lightweight"|"backtrader"` | backend result 或 unavailable | 默认 `lightweight` |
| Backtrader adapter | reader 输出且已 PIT/复权清洗的 OHLCV、factor panel、score、calendar、`BenchmarkResult`、quality metadata | optional result / comparison rows | 不联网、不读 env、不导入 connector；不生成 PIT、不计算复权因子；不触发 benchmark backfill |
| unavailable 状态 | 缺依赖、quality fail、dataset missing、benchmark unavailable/required_missing | `backend_unavailable`、`benchmark_unavailable` 或等价结构 | 不影响轻量主路径；只报告对照缺失 |

**设计约束**：

- Backtrader 不得读取 `TUSHARE_TOKEN`。
- Backtrader adapter 不得 import `market_data.connectors`、`market_data.runtime`、`market_data.storage`。
- Backtrader 不得替代 `engine/backtest.py` 默认主路径。
- 未安装 Backtrader 时默认 pytest 和轻量回测必须通过。
- Backtrader 输出是对照报告，不覆盖轻量结果。
- Backtrader 不生成 PIT、不做 as-of join、不计算 `adj_factor`、不选择 `adjustment_policy`、不读取 Tushare、不联网、不判定 quality gate。
- Backtrader 不消费 `remediation_job_spec` 执行动作；benchmark `required_missing` 只能进入报告 metadata 或对照缺失状态。
- Backtrader 只负责调仓、成交、成本、仓位、净值和风险分析。
- CR005-S06 dev_gate 必须等待 CR005-S01 的 hs300 backfill job spec frozen、CR005-S02 的 PIT/复权契约 confirmed、CR005-S03 的 quality/readers gate verified 或 contract frozen、CR005-S04 的 BenchmarkResult schema 和 benchmark policy frozen。

**命名规范**：backend enum 使用 `lightweight` / `backtrader` 或 LLD 确认的等价 exact 值；错误状态使用 `backend_unavailable`。

**平台目标**：本地可选后端；无默认依赖激活。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR005-S06-T1 | 创建 | `engine/backtrader_adapter.py` | 设计本地 reader 的干净 feed 到 Backtrader feed 的适配和 unavailable 降级 |
| CR005-S06-T2 | 修改 | `engine/backtest.py` | 如需要，仅增加可选 selector，不改变默认主路径 |
| CR005-S06-T3 | 修改 | `pyproject.toml`, `uv.lock` | 仅 CP5 批次 D 批准后，通过 `uv add --group backtrader backtrader==1.9.78.123` 增加 dependency group；默认 lightweight 路径必须 lazy import 且不依赖 Backtrader |
| CR005-S06-T4 | 创建 | `tests/test_backtrader_optional_backend.py` | 覆盖未安装降级、no connector import、quality fail/PIT fail/复权 fail 阻断、benchmark required_missing 不补数 |
| CR005-S06-T5 | 修改 | `README.md`, `docs/USER-MANUAL.md` | 说明 optional backend 和禁用边界 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_backtrader_optional_backend.py`；默认全量测试不应依赖 Backtrader 安装。

**验证方式**：依赖缺失模拟、本地 reader fixture、静态导入扫描、结果对照断言。

**依赖环境**：Python 3.11、uv、pytest；Backtrader 作为 dependency group `backtrader` 固定为 `backtrader==1.9.78.123`，仅在 CP5 批准后安装，默认 lightweight 路径不依赖该 group。

**关键验证场景**：

- 未安装 Backtrader 返回 `backend_unavailable`。
- 默认 `engine/backtest.py` 行为不变。
- adapter 静态扫描中 connector/runtime/storage import 命中数为 0。
- quality fail 阻断 Backtrader 运行。
- PIT gate fail 或 `available_at > decision_time` 阻断 Backtrader 运行。
- 复权 gate fail、adjusted price 缺失或 `adjustment_policy` 混用阻断 Backtrader 运行。
- benchmark unavailable 时报告对照缺失，不联网补数。
- benchmark `required_missing` 时不执行 `remediation_job_spec`，只在结果 metadata 中记录 next action。
- CP6 必须执行 Python 3.11 import + tiny Cerebro smoke；若真实 Backtrader smoke 失败，则降级为 `backend_unavailable` + fake smoke，不在本 Story 临时切换 fork。

## 量化验收标准（acceptance_criteria）

- [x] 默认 backend 为轻量主路径，Backtrader 启用需要显式参数。
- [x] 未安装 Backtrader 时默认轻量回测和默认 pytest 不受影响。
- [x] Backtrader adapter 对 `TUSHARE_TOKEN` 的读取次数为 0。
- [x] Backtrader adapter 对 `market_data.connectors` / `runtime` / `storage` 的导入次数为 0。
- [x] quality fail 时 Backtrader 成功运行次数为 0。
- [x] PIT gate fail 或 `available_at > decision_time` 时 Backtrader 成功运行次数为 0。
- [x] adjusted price 缺失、`adj_factor` 冲突或 `adjustment_policy` 混用时 Backtrader 成功运行次数为 0。
- [x] Backtrader adapter 中 PIT 生成、复权因子计算、Tushare 读取和联网补数职责出现次数为 0。
- [x] benchmark `unavailable` / `required_missing` 时 Backtrader 触发 fetch/backfill/write 的次数为 0。
- [x] Backtrader 输出可记录 `BenchmarkResult.status` 和 `missing_reason`，但不得填充 `hs300_index` 为 proxy；旧代理如展示只能命名为 `proxy_baseline`。
- [x] Backtrader 运行职责限定为调仓、成交、成本、仓位、净值和风险分析。
- [x] 不写真实 `data/**`、`reports/**`，不提交凭据，不写 `delivery/**`。

## 阻塞说明

`CR5-Q3` 已由用户确认：S06 使用 dependency group `backtrader`，版本固定为 `backtrader==1.9.78.123`；实现阶段必须 lazy import，默认 lightweight 不依赖 Backtrader；CP6 必须验证 Python 3.11 import + tiny Cerebro smoke test；若真实 Backtrader smoke 失败，则降级为 `backend_unavailable` + fake smoke，不在本 Story 临时切换 fork。

`CR5-BLK-004` 为 CR005-S06 的 dev_gate 阻塞：CR005-S02/S03 的 PIT、复权和 quality gate 契约未 confirmed/verified 前，不得实现 Backtrader adapter。

`CR5-Q2` 仍为 OPEN：沪深 300 benchmark 口径未确认。CR005-S06 可以设计 benchmark unavailable 处理，但真实 hs300 对照报告必须等待 CR005-S04 benchmark policy 冻结。

## LLD / CP5 自动预检记录

| 项目 | 路径 / 状态 | 说明 |
|---|---|---|
| LLD | `process/stories/CR005-S06-backtrader-optional-backend-LLD.md` | 已生成并经 CP5 Batch D 人工确认，`confirmed=true`。 |
| CP5 自动预检 | `process/checks/CP5-CR005-S06-backtrader-optional-backend-LLD-IMPLEMENTABILITY.md` | 结论 `PASS`；无阻断 LLD 审查的问题。 |
| CP5 人工审查 | `checkpoints/CP5-CR005-BATCH-D-S06-LLD-BATCH.md` | 结论 `approved`；`CR5-Q3` 与 selector 形态均 accepted-with-constraints。 |
| 实现门控 | `implementation_allowed=true` | 已允许创建 S06 实现 handoff 并由 meta-dev 子 agent 执行；仍禁止联网、真实写 lake、读取 token、导入 connector/runtime/storage。 |

## CP6 编码完成记录

| 项目 | 路径 / 状态 | 说明 |
|---|---|---|
| CP6 编码完成 | `process/checks/CP6-CR005-S06-backtrader-optional-backend-CODING-DONE.md` | 结论 `PASS`；专项测试、全量测试和真实 Backtrader Cerebro smoke 均通过。 |
| 实现 handoff | `process/handoffs/META-DEV-CR005-S06-IMPLEMENT-2026-05-17.md` | 已回填 `completed`；下一步交给 meta-qa 执行 CP7。 |
| Story 状态 | `ready-for-verification` | 已完成实现与 CP6 自检，已进入 CP7 验证。 |

## CP7 验证完成记录

| 项目 | 路径 / 状态 | 说明 |
|---|---|---|
| CP7 验证完成 | `process/checks/CP7-CR005-S06-backtrader-optional-backend-VERIFICATION-DONE.md` | 结论 `PASS`；专项测试、全量测试、真实 Backtrader Cerebro smoke 和 forbidden import/token/network scan 均通过。 |
| QA handoff | `process/handoffs/META-QA-CR005-S06-CP7-VERIFY-2026-05-17.md` | 已回填 `completed`；meta-qa/qa-cao the 2nd 完成独立验证。 |
| Story 状态 | `verified` | S06 已通过 CP5、CP6、CP7。 |
