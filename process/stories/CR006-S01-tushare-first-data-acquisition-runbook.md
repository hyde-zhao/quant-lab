---
story_id: "CR006-S01-tushare-first-data-acquisition-runbook"
title: "Tushare-first 数据获取与 runbook"
story_slug: "tushare-first-data-acquisition-runbook"
status: "lld-ready"
priority: "P0"
wave: "CR006-BATCH-A"
depends_on: ["CR005-S01", "CR005-S02", "CR005-S03"]
dependency_contracts:
  - upstream: "CR005-S01"
    type: "contract"
    required: "Tushare connector、显式 job、plan/dry-run、raw/manifest 写入边界已冻结"
  - upstream: "CR005-S02"
    type: "contract"
    required: "Tushare dataset schema、exact interface mapping、PIT 字段和复权 normalization 契约已冻结"
  - upstream: "CR005-S03"
    type: "contract"
    required: "quality/catalog/readers、PIT as-of gate、复权一致 gate 已冻结"
file_ownership:
  primary:
    - "tests/test_cr006_tushare_first_acquisition.py"
  shared:
    - "market_data/cli.py"
    - "market_data/connectors/tushare.py"
    - "market_data/storage.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/catalog.py"
  merge_owner: "CR006-S01-tushare-first-data-acquisition-runbook"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "data/**"
    - ".env"
    - "credentials"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#23-cr-006-tushare-first-数据方案增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-018tushare-first-structured-lake-与运行时消费面分离"
    - "process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md"
  status: "ready"
  cp5_batch: "CR006-BATCH-A"
dev_gate:
  lld_confirmed: false
  dependencies_satisfied: false
  required_contracts:
    - "Tushare dataset/runbook scope frozen"
    - "raw/manifest audit-only boundary frozen"
    - "canonical/gold lineage and quality gate contract frozen"
    - "no old data read/list/migrate/delete boundary frozen"
  file_conflict_free: false
  cp5_required: true
  implementation_allowed: false
created_at: "2026-05-18"
updated_at: "2026-05-18T22:33:23+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-006"
---

# CR006-S01：Tushare-first 数据获取与 runbook

## 目标

建立 Tushare-first 数据获取与审计方案，明确 raw 和 manifest 仍然需要保留，但只属于采集、审计、断点续传、复现、replay 和质量追溯层。S01 不让轻量回测、experiments 或 Backtrader 直接消费 raw/manifest，也不读取、列出、迁移、复制或删除旧 repo `data/**`。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR006-AC-001、CR006-AC-002、CR006-AC-003、CR006-AC-009 |
| HLD | §23.1、§23.4、§23.6、§23.7、§23.8 |
| ADR | ADR-018 |

## 开发上下文（dev_context）

**背景说明**：用户已明确旧 `data/` 数据来源不明，不能承诺 Tushare 完全覆盖旧数据。CR-006 的新主线必须绕开旧数据，以 Tushare structured lake 为事实源。raw/manifest 需要存在，但它们不是回测运行时依赖，而是数据层 replay、quality 和 lineage 的依据。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`、CR005-S01/S02/S03 Story/LLD、`market_data/cli.py`、`market_data/connectors/tushare.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py`。

**输出文件**：后续实现可修改 `market_data/cli.py` 或等价 job、`market_data/connectors/tushare.py`、`market_data/storage.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/catalog.py` 和 `tests/test_cr006_tushare_first_acquisition.py`。本 Story 不修改 `engine/**`、`experiments/**`、README、docs、真实 `data/**`、`.env` 或 `delivery/**`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| Tushare plan/dry-run | dataset、source/interface、date range、lake root、dry-run、resume policy | planned batches、target raw/manifest/canonical/quality/catalog/gold paths、error enum | dry-run 不联网、不写数据；不得读取旧 `data/**` |
| Tushare fetch | 显式命令、enabled source、allowlist、env var name | raw response、manifest run、fetch status | 缺 token/env/source allowlist 时 fail fast；不得打印 token 值 |
| normalization / quality | raw_path、manifest_run_id、schema_version、dataset mapping | canonical、quality、catalog、gold | schema 或 quality fail 时阻断运行时消费面 |
| lineage contract | run_id、source、interface、raw checksum 或等价 lineage | canonical/gold 可追溯元数据 | 不记录真实私有路径、NAS 用户名、密码 |

**设计约束**：

- Tushare 只能由用户显式执行的数据层 job 调用。
- raw/manifest 是审计与复现层，不是轻量回测或 Backtrader 的 runtime input。
- canonical/gold 必须可以追溯到 manifest run。
- 旧 repo `data/` 不参与 plan、fetch、normalize、validate、catalog 或 gold 生成。
- 不承诺 Tushare 完全覆盖旧 `data/`。
- 默认测试使用 fake/offline fixture 和 `tmp_path`；不需要真实 token、不需要 NAS、不联网。

**命名规范**：保留 `market_data` structured lake 语义；字段命名优先 `run_id`、`manifest_run_id`、`source_interface`、`dataset`、`quality_status`、`lineage`。

**平台目标**：本地 Python 研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR006-S01-T1 | 修改 | `market_data/cli.py` 或等价 job | 明确 Tushare-first plan/dry-run/fetch/runbook 行为和 no-old-data 边界 |
| CR006-S01-T2 | 修改 | `market_data/storage.py` | 确认 raw/manifest 写入和 lineage 字段，不记录凭据或真实私有路径 |
| CR006-S01-T3 | 修改 | `market_data/normalization.py` / `validation.py` / `catalog.py` | 确认 canonical/gold 可从 manifest run 追溯，quality gate 可阻断消费 |
| CR006-S01-T4 | 创建 | `tests/test_cr006_tushare_first_acquisition.py` | 覆盖 dry-run 不联网、raw/manifest 审计字段、canonical/gold lineage、旧 `data/` 不参与 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr006_tushare_first_acquisition.py`。

**验证方式**：fake connector、tmp lake、manifest fixture、静态扫描、错误枚举测试。

**依赖环境**：Python 3.11、uv、pytest；不需要 Tushare token、不需要 NAS、不联网。

**关键验证场景**：

- plan/dry-run 网络调用次数为 0，写入次数为 0。
- fetch 缺 token/env/source allowlist 时 fail fast 且不打印敏感值。
- raw/manifest 写入只发生在显式数据层 job。
- canonical/gold 可追溯到 manifest run。
- 旧 repo `data/` 读取、列出、迁移、复制、删除次数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] raw 和 manifest 均保留，但 Story/LLD 明确其职责为采集审计、复现、质量追溯和 replay。
- [ ] 轻量回测、experiments、Backtrader 直接消费 raw/manifest 的次数为 0。
- [ ] canonical/gold 至少包含 run/source/interface/quality lineage，能追溯到 manifest run。
- [ ] Tushare job 只能由用户显式执行；回测运行时触发 fetch/backfill 的次数为 0。
- [ ] 旧 repo `data/**` 读取、列出、迁移、复制、删除次数为 0。
- [ ] token、NAS 用户名、密码、真实私有路径记录次数为 0。
- [ ] 不修改 `engine/**`、`experiments/**`、README、docs、真实 `data/**`、`.env`、`delivery/**`。

## 阻塞说明

无 BLOCKING。Tushare P0 dataset 是否覆盖下一轮策略研究所需字段仍为 OPEN；该问题不阻塞 Tushare-first 架构确认，但阻塞具体字段完整性验收和真实回补范围确认。
