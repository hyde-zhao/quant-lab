---
story_id: "STORY-014"
title: "CR-004 market_data 包骨架与数据湖契约"
story_slug: "cr004-market-data-package-lake-contracts"
status: "verified"
priority: "P0"
wave: "CR4-W0"
depends_on: []
dependency_contracts: []
file_ownership:
  primary:
    - "market_data/__init__.py"
    - "market_data/contracts.py"
    - "market_data/config.py"
    - "market_data/source_registry.py"
    - "market_data/lake_layout.py"
    - "market_data/py.typed"
    - "tests/test_market_data_contracts.py"
  shared:
    - "pyproject.toml"
    - "uv.lock"
  merge_owner: "STORY-014"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "delivery/**"
    - "data/**/*.parquet"
    - "data/market_data/raw/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#21-cr-004-可迁移市场数据组件增量设计"
    - "process/ARCHITECTURE-DECISION.md#adr-008market_data-作为独立可迁移市场数据包"
    - "process/ARCHITECTURE-DECISION.md#adr-011parquet-数据湖-canonical-schema-与-manifest-契约"
    - "process/stories/STORY-014-cr004-market-data-package-lake-contracts.md"
  status: "approved-with-constraints"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  cp5_required: true
  cp5_status: "approved-with-constraints"
  implementation_status: "completed"
  verification_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-STORY-014-cr004-market-data-package-lake-contracts-VERIFICATION-DONE.md"
created_at: "2026-05-17"
updated_at: "2026-05-17"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-004"
---

# STORY-014：CR-004 market_data 包骨架与数据湖契约

## 目标

创建独立可迁移 `market_data/` 包骨架，固化 Parquet 数据湖 raw / manifest / canonical / gold / quality / catalog 分层、canonical schema、manifest schema、source registry 和配置边界。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR-004-AC-001, CR-004-AC-003；继承 REQ-016、REQ-047 至 REQ-058 |
| HLD | §21.1 问题与边界；§21.3 推荐架构总览；§21.4 数据湖分层；§21.8 非功能需求 |
| ADR | ADR-008, ADR-011 |

## 开发上下文（dev_context）

**背景说明**：CR-004 需要把市场数据获取与治理能力从既有 `engine/` 中抽出，形成后续可迁移的 `market_data/` 包。首个 Story 只创建契约与包骨架，不实现真实获取、不写真实数据。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/changes/CR-004-MARKET-DATA-COMPONENT-2026-05-17.md`、`pyproject.toml`。

**输出文件**：`market_data/__init__.py`、`market_data/contracts.py`、`market_data/config.py`、`market_data/source_registry.py`、`market_data/lake_layout.py`、`market_data/py.typed`、`tests/test_market_data_contracts.py`。若实现需要新增依赖，必须通过 uv 更新 `pyproject.toml` / `uv.lock`；默认应优先复用现有 pandas/pyarrow/PyYAML。

**接口约定**：

| 对象 | 契约 |
|---|---|
| `LakeLayout` 或等价对象 | 根据 `lake_root` 返回 `raw`、`manifest`、`canonical`、`gold`、`quality`、`catalog` 路径，不创建真实生产数据 |
| `CanonicalSchema` 或常量表 | 至少定义 prices 的 `trade_date`、`symbol`、`close`、`source`、`source_run_id`，并记录 `adjustment_policy`、`available_at` 的条件必需规则 |
| `ManifestSchema` 或常量表 | 至少定义 `schema_version`、`run_id`、`batch_id`、`source`、`interface`、`params`、`requested_at`、`attempts`、`status`、`raw_path`、`canonical_path`、错误字段和时间字段 |
| `SourceRegistry` | fake 默认 resolved；AkShare/Tushare/TickFlow 默认 disabled 或 unresolved，必须 exact 命中，禁止模糊匹配 |

**设计约束**：

- `market_data/` 不得 import `engine.*`、`experiments.*` 或 `reports.*`。
- 不提交真实行情、凭据、token、cookie、session。
- 不改写 STORY-001..013 的 verified 状态。
- 不写 `delivery/**`。
- 所有路径必须支持自定义 `lake_root`，默认建议为 `data/market_data`。

**命名规范**：模块名使用 snake_case；Story 文件名保持 `STORY-014-cr004-market-data-package-lake-contracts.md`；source 值建议为 `fake`、`akshare`、`tushare`、`tickflow`；未知真实源必须显式 `disabled` / `UNRESOLVED`，不得猜测。

**平台目标**：本地 Python 研究工具内的独立数据组件；不生成安装脚本；不发布包。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| 无 | N/A | 可作为 CR-004 首个 LLD | CP3/CP4 通过后才可进入 CP5 | 本 Story 是 CR-004 contract root |

### 文件系统布局

```text
<repo>/
├── market_data/
│   ├── __init__.py
│   ├── py.typed
│   ├── contracts.py
│   ├── config.py
│   ├── lake_layout.py
│   └── source_registry.py
└── tests/
    └── test_market_data_contracts.py
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S014-T1 | 创建 | `market_data/__init__.py`, `market_data/py.typed` | 建立可导入包，导出版本与核心契约对象 |
| S014-T2 | 创建 | `market_data/contracts.py` | 定义 canonical schema、manifest 字段、质量状态、source 状态枚举 |
| S014-T3 | 创建 | `market_data/lake_layout.py` | 定义数据湖六层路径解析与父路径校验策略 |
| S014-T4 | 创建 | `market_data/source_registry.py` | 定义 fake resolved、真实源 disabled/unresolved 的 exact registry |
| S014-T5 | 创建 | `market_data/config.py` | 定义 offline 默认配置、真实 adapter 显式启用字段和配置加载边界 |
| S014-T6 | 创建 | `tests/test_market_data_contracts.py` | 覆盖导入边界、schema 字段、路径解析、真实源默认关闭 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_market_data_contracts.py`；静态检查 `rg -n "from engine|import engine|from experiments|import experiments" market_data` 应无命中。

**验证方式**：单元测试 + 静态扫描 + 人工审查。

**依赖环境**：Python 3.11、uv、pytest；不需要网络、不需要真实行情数据。

**关键验证场景**：

- 导入 `market_data.contracts` 不触发 pandas/pyarrow 外部 I/O 或网络。
- `LakeLayout(lake_root="tmp")` 能返回 6 个层级路径。
- fake source resolved；AkShare/Tushare/TickFlow 默认 disabled/unresolved。
- source/interface 未 exact 注册时 fail fast。

## 量化验收标准（acceptance_criteria）

- [ ] `market_data/` 至少创建 6 个包内文件，且 `market_data` 不 import `engine` / `experiments`。
- [ ] 数据湖 6 层 raw / manifest / canonical / gold / quality / catalog 均有路径契约。
- [ ] manifest 字段表覆盖不少于 12 个必需字段，至少包含 source、interface、params、attempts、status、raw_path、canonical_path。
- [ ] canonical prices schema 覆盖不少于 5 个必需字段：`trade_date`、`symbol`、`close`、`source`、`source_run_id`。
- [ ] fake source 默认启用；AkShare/Tushare/TickFlow 默认关闭或 unresolved，未显式启用时不可发起真实请求。
- [ ] 不新增真实数据文件、凭据、`delivery/**` 或 `engine/**` 修改。

## 后续 LLD 输入约束

LLD 必须明确契约对象采用 dataclass、TypedDict、常量表还是普通函数；必须列出 exact source registry；必须说明是否需要修改 `pyproject.toml`。未确认真实 TickFlow/Tushare 接口前，不得把它们标记为 resolved。

## 阻塞说明

无 BLOCKING；OPEN 问题为真实 TickFlow/Tushare 接口与凭据策略，阻塞真实 adapter 启用，不阻塞 fake/offline 契约。

## 开发状态记录

| 日期 | 状态 | 说明 |
|---|---|---|
| 2026-05-17 | ready-for-verification | CP5 批次 A 已带约束通过；已按 LLD 实现 `market_data` 包骨架、contracts/config/source_registry/lake_layout 和契约测试，等待 CP7 验证。 |
