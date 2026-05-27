---
story_id: "CR006-S02-canonical-gold-lightweight-engine-adapter"
title: "canonical/gold 到轻量 engine 适配"
story_slug: "canonical-gold-lightweight-engine-adapter"
status: "lld-ready"
priority: "P0"
wave: "CR006-BATCH-A"
depends_on: ["CR006-S01-tushare-first-data-acquisition-runbook", "CR005-S03"]
dependency_contracts:
  - upstream: "CR006-S01-tushare-first-data-acquisition-runbook"
    type: "contract"
    required: "Tushare-first raw/manifest 审计边界、canonical/gold lineage 和 quality gate 已冻结"
  - upstream: "CR005-S03"
    type: "contract"
    required: "market_data readers、quality gate、PIT/复权 gate 已冻结"
file_ownership:
  primary:
    - "tests/test_cr006_lightweight_engine_adapter.py"
  shared:
    - "engine/data_loader.py"
    - "engine/backtest.py"
    - "experiments/run_experiment_06_07.py"
    - "experiments/run_experiment_08.py"
    - "experiments/run_experiment_09.py"
    - "experiments/run_experiment_10.py"
    - "experiments/run_experiment_12.py"
    - "experiments/run_experiment_13.py"
    - "market_data/readers.py"
  merge_owner: "CR006-S02-canonical-gold-lightweight-engine-adapter"
  forbidden:
    - "market_data/connectors/**"
    - "market_data/runtime.py"
    - "market_data/storage.py"
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "data/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#236-集成契约"
    - "process/ARCHITECTURE-DECISION.md#adr-018tushare-first-structured-lake-与运行时消费面分离"
    - "process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md"
    - "process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md"
  status: "ready"
  cp5_batch: "CR006-BATCH-A"
dev_gate:
  lld_confirmed: false
  dependencies_satisfied: false
  required_contracts:
    - "CR006-S01 canonical/gold and quality gate contract frozen"
    - "external legacy_flat derivation policy frozen if used"
    - "repo data reference-only behavior frozen"
  file_conflict_free: false
  cp5_required: true
  implementation_allowed: false
created_at: "2026-05-18"
updated_at: "2026-05-18T22:33:23+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-006"
---

# CR006-S02：canonical/gold 到轻量 engine 适配

## 目标

为当前轻量回测框架建立 Tushare-first 运行时输入契约：轻量 engine 应消费 `market_data` canonical/gold reader，或在兼容期消费由 canonical/gold 派生到仓库外 external `legacy_flat` 的 flat parquet。S02 禁止默认 fallback 到 repo `data/`，也禁止把 raw/manifest 当作回测运行时输入。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR006-AC-004、CR006-AC-005、CR006-AC-006、CR006-AC-010 |
| HLD | §23.3、§23.4、§23.6、§23.7、§23.8 |
| ADR | ADR-018 |

## 开发上下文（dev_context）

**背景说明**：当前轻量 engine 历史上习惯读取 flat parquet。新方案不再使用旧 repo `data/` 作为默认 fallback。若短期必须保留 flat 文件名契约，应从 canonical/gold 派生 external `legacy_flat`，并保留 lineage，而不是读取旧数据。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、S01 Story/LLD、CR005-S03 Story/LLD、`engine/data_loader.py`、`engine/backtest.py`、`experiments/run_experiment_06_07.py`、`experiments/run_experiment_08.py`、`experiments/run_experiment_09.py`、`experiments/run_experiment_10.py`、`experiments/run_experiment_12.py`、`experiments/run_experiment_13.py`、`market_data/readers.py`。

**输出文件**：后续实现可修改 engine / experiments 的输入适配调用点、`market_data/readers.py` 的消费接口，以及 `tests/test_cr006_lightweight_engine_adapter.py`。本规划阶段不修改这些业务文件。

**接口约定**：

| 消费方 | 输入 | 期望行为 | 错误 / 限制 |
|---|---|---|---|
| Lightweight reader mode | dataset、date range、adjustment_policy、quality policy | 返回轻量 engine 可用的 in-memory prices/universe/calendar/metadata | required_missing / quality_failed 返回 typed error；不触发 fetch |
| External `legacy_flat` derivation | canonical/gold、quality pass/warn、lineage metadata、目标外置目录 | 生成 `prices.parquet`、`index_members.parquet`、`trade_calendar.parquet` 兼容面 | 输出必须带 lineage；不得从 repo `data/` 复制 |
| Experiments adapter | reader result 或 external `legacy_flat` | 实验入口离线运行 | 不读取 `MARKET_DATA_LAKE_ROOT/raw` 或 manifest 作为行情输入 |

**设计约束**：

- 轻量 engine 运行时只消费 canonical/gold reader 或 external `legacy_flat`。
- external `legacy_flat` 是由 canonical/gold 派生的新兼容面，不是旧 repo `data/`。
- repo `data/` 不作为默认 fallback；缺数据时返回 required_missing/remediation spec。
- raw/manifest 不作为运行时行情输入。
- 不导入 `market_data.connectors`、不触发 Tushare fetch、不联网。
- 测试只使用 tmp_path/fake canonical/gold fixture。

**命名规范**：若出现兼容 flat 输出，使用 `legacy_flat` 表示格式兼容，不使用 `data` 表示事实源；错误状态使用 `required_missing`、`quality_failed`、`lineage_missing`。

**平台目标**：本地 Python 研究工具；默认离线；uv 管理测试入口。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR006-S02-T1 | 修改 | `market_data/readers.py` | 暴露轻量 engine 所需 canonical/gold reader 或 adapter contract |
| CR006-S02-T2 | 修改 | `engine/data_loader.py` / `engine/backtest.py` | 接入 canonical/gold reader 或 external `legacy_flat`，禁止默认 fallback repo `data/` |
| CR006-S02-T3 | 修改 | `experiments/run_experiment_*.py` | 统一实验入口的 Tushare-first reader / external `legacy_flat` 输入策略 |
| CR006-S02-T4 | 创建 | `tests/test_cr006_lightweight_engine_adapter.py` | 覆盖 quality gate、required_missing、external `legacy_flat` lineage、repo `data/` 不参与 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr006_lightweight_engine_adapter.py`。

**验证方式**：tmp canonical/gold fixture、quality pass/fail fixture、adapter 单元测试、静态扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要 token、不需要真实 NAS、不联网。

**关键验证场景**：

- quality pass 时轻量 engine 可从 canonical/gold reader 获得输入。
- quality fail 时回测启动被阻断。
- external `legacy_flat` 仅从 canonical/gold 派生，含 lineage。
- 缺数据返回 required_missing/remediation spec，不 fallback 到 repo `data/`。
- raw/manifest 不作为运行时行情输入。

## 量化验收标准（acceptance_criteria）

- [ ] 轻量 engine 默认运行输入来自 canonical/gold reader 或 external `legacy_flat` 的次数为 100%。
- [ ] repo `data/` 被用作默认 fallback 或新链路可用性证明的次数为 0。
- [ ] raw/manifest 被轻量 engine 当作行情运行输入的次数为 0。
- [ ] external `legacy_flat` 若存在，必须可追溯到 canonical/gold lineage。
- [ ] quality fail 阻断回测启动；required_missing 返回 typed remediation spec。
- [ ] Tushare fetch/backfill 由轻量 engine 触发的次数为 0。
- [ ] 不修改真实 `data/**`、`.env`、README、docs、`delivery/**`。

## 阻塞说明

无 BLOCKING。external `legacy_flat` 是否作为必须产物仍为 OPEN；默认设计允许 adapter 直接消费 canonical/gold，只有当前 engine 兼容需要时才派生 external `legacy_flat`。
