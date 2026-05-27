---
story_id: "STORY-001"
title: "工程基线与数据契约骨架"
story_slug: "engine-baseline-data-contracts"
status: "verified"
priority: "P0"
wave: "W0"
depends_on: []
created_at: "2026-05-14"
updated_at: "2026-05-14"
approved_by: "meta-po"
approved_at: "2026-05-14"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_path: "process/stories/STORY-001-engine-baseline-data-contracts-LLD.md"
verification_handoff: "process/handoffs/META-QA-VERIFY-W0-STORY-001-2026-05-14.md"
verification_report: "process/VERIFICATION-REPORT.md"
verified_by: "meta-qa"
verified_at: "2026-05-14"
---

# STORY-001：工程基线与数据契约骨架

## 目标

创建本地 Python 研究工具的工程基线、依赖管理入口和共享数据契约骨架，为 M0-M2 主路径提供稳定文件布局。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-001, REQ-013, REQ-036 |
| HLD | §3 推荐方案总览；§5 高层模块；§6 技术选型；§16 M0 |
| ADR | ADR-002 |

## 开发上下文（dev_context）

**背景说明**：HLD 确认第一版采用项目内轻量日频回测层，不引入大型回测框架。后续 Story 需要共享目录、Python 依赖、数据 schema 常量和报告字段常量。

**输入文件**：`process/HLD.md`、`process/REQUIREMENTS.md`、`process/STORY-BACKLOG.md`、`process/ARCHITECTURE-DECISION.md`。

**输出文件**：`pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/__init__.py`、`engine/contracts.py`、`strategies/__init__.py`、`data/.gitkeep`、`reports/.gitkeep`。

**接口约定**：`engine/contracts.py` 只定义 schema、枚举、默认配置名和报告字段名，不执行 I/O，不调用 AKShare，不导入后续实现模块。

**设计约束**：Python 依赖必须通过 uv 管理；不得提交 `.venv/`；不得引入 RQAlpha、Backtrader、vectorbt 或 bt 作为第一版主框架；目录必须保持 `data/`、`engine/`、`strategies/`、`notebooks/`、`reports/` 分层。

**命名规范**：Story 卡片文件名保持 `STORY-001-engine-baseline-data-contracts.md`；后续 Python 模块使用小写 snake_case；配置文件使用 `config/data_prep.yaml`。

**平台目标**：本地 Python 研究工具；不生成平台安装脚本，不写入 `delivery/**`。

### 文件布局边界

```text
<repo>/
├── pyproject.toml
├── uv.lock
├── config/
│   └── data_prep.yaml
├── engine/
│   ├── __init__.py
│   └── contracts.py
├── strategies/
│   └── __init__.py
├── data/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S001-T1 | 创建 | `pyproject.toml` | 声明 Python 3.11+、pandas、pyarrow、akshare、pytest 等最小依赖 |
| S001-T2 | 创建 | `uv.lock` | 通过 `uv lock` 生成锁文件 |
| S001-T3 | 创建 | `config/data_prep.yaml` | 写入默认 `request_interval_seconds=2`、`batch_size=50`、`max_concurrency=1`、`max_retries=3`、`recent_trade_days_backfill=5` |
| S001-T4 | 创建 | `engine/contracts.py` | 定义 parquet 字段、manifest 字段、质量状态、报告字段常量 |
| S001-T5 | 创建 | `engine/__init__.py`、`strategies/__init__.py`、`.gitkeep` | 建立包和空目录基线 |

## 验证上下文（validation_context）

**验证入口**：结构检查、依赖锁文件检查、`uv run --python 3.11 python -c "import engine.contracts"`。

**验证方式**：人工检查 + 后续 meta-qa 执行 uv 入口验证。

**依赖环境**：Python 3.11+、uv；不需要真实行情数据。

**关键验证场景**：空仓库基线可导入；配置默认值与 HLD Q-012/Q-013/Q-015 一致；未引入大型回测框架依赖。

## 量化验收标准（acceptance_criteria）

- [ ] 创建或确认 8 个基线输出路径均存在。
- [ ] `pyproject.toml` 只使用 uv 作为依赖管理入口，且未声明 RQAlpha、Backtrader、vectorbt、bt。
- [ ] `config/data_prep.yaml` 至少包含 6 个默认配置项：`request_interval_seconds`、`batch_size`、`max_concurrency`、`max_retries`、`backoff_policy`、`recent_trade_days_backfill`。
- [ ] `engine/contracts.py` 覆盖 3 类 parquet 必需字段、manifest 必需字段、`pass/warn/fail` 质量状态和 2 个报告 CSV 字段列表。
- [ ] 后续 LLD 明确是否把字段契约实现为 dataclass、TypedDict、常量表或 pydantic model。

## 后续 LLD 输入约束

LLD 必须给出依赖版本范围、`engine/contracts.py` 的具体对象形态、配置解析策略、目录创建策略和回滚方式。LLD 不得把工程基线扩展成安装器或交付脚本。

## 阻塞说明

无。

## 编排状态

Story Plan 已由用户确认通过。本 Story 是 W0 中首个无前置依赖的可执行 Story，已由 `meta-po` 批准进入 LLD 起草。`meta-dev` 已输出 `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md`，用户已明确确认 LLD 通过。`meta-dev` 已报告 STORY-001 实现完成；`meta-po` 已复核实现源文件范围与 Story / LLD 一致，并将当前 Story 状态推进为 `ready-for-verification`。`meta-qa` 已完成 STORY-001 正式 8 维度验收，`process/VERIFICATION-REPORT.md` 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项；`meta-po` 已据此将本 Story 收敛为 `verified`。

实现范围严格限定为本 Story 输出文件：`pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/__init__.py`、`engine/contracts.py`、`strategies/__init__.py`、`data/.gitkeep`、`reports/.gitkeep`。复核未发现 `STORY-002+` 源文件、data fetcher、manifest writer、quality report、回测引擎逻辑、策略逻辑或 `delivery/**` 产物。STORY-001 已满足 W0 下游依赖的前置条件，允许 `STORY-002` 进入 LLD 起草；`STORY-003` 仍依赖 `STORY-002`，不得推进。
