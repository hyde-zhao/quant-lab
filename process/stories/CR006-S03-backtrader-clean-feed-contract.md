---
story_id: "CR006-S03-backtrader-clean-feed-contract"
title: "Backtrader clean feed contract"
story_slug: "backtrader-clean-feed-contract"
status: "lld-ready"
priority: "P1"
wave: "CR006-BATCH-A"
depends_on:
  - "CR006-S01-tushare-first-data-acquisition-runbook"
  - "CR006-S02-canonical-gold-lightweight-engine-adapter"
  - "CR005-S06"
dependency_contracts:
  - upstream: "CR006-S01-tushare-first-data-acquisition-runbook"
    type: "contract"
    required: "canonical/gold lineage、quality gate 和 raw/manifest 审计边界已冻结"
  - upstream: "CR006-S02-canonical-gold-lightweight-engine-adapter"
    type: "contract"
    required: "轻量运行时消费面和 repo data reference-only 行为已冻结"
  - upstream: "CR005-S06"
    type: "contract"
    required: "Backtrader optional backend 边界、PIT/复权职责和未安装降级策略已冻结"
file_ownership:
  primary:
    - "tests/test_cr006_backtrader_clean_feed.py"
  shared:
    - "engine/backtrader_adapter.py"
    - "engine/backtest.py"
    - "market_data/readers.py"
  merge_owner: "CR006-S03-backtrader-clean-feed-contract"
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
    - "process/ARCHITECTURE-DECISION.md#adr-016backtrader-作为可选后端不替代轻量主路径"
    - "process/ARCHITECTURE-DECISION.md#adr-017pit-与复权由-pandas-数据层保证backtrader-只消费干净输入"
    - "process/ARCHITECTURE-DECISION.md#adr-018tushare-first-structured-lake-与运行时消费面分离"
    - "process/stories/CR006-S03-backtrader-clean-feed-contract.md"
  status: "ready"
  cp5_batch: "CR006-BATCH-A"
dev_gate:
  lld_confirmed: false
  dependencies_satisfied: false
  required_contracts:
    - "clean OHLCV/factor/score feed schema frozen"
    - "PIT/as-of and adjustment policy gate frozen"
    - "Backtrader optional dependency strategy frozen"
    - "no connector/runtime/token/raw/manifest consumption boundary frozen"
  file_conflict_free: false
  cp5_required: true
  implementation_allowed: false
created_at: "2026-05-18"
updated_at: "2026-05-18T22:33:23+08:00"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-006"
---

# CR006-S03：Backtrader clean feed contract

## 目标

为 Backtrader optional backend 定义 Tushare-first clean feed contract。Backtrader 只能消费经过 quality gate、PIT as-of、复权一致检查后的 clean OHLCV / factor / score feed；不得读取 raw/manifest、不得读取 `TUSHARE_TOKEN`、不得导入 connector/runtime/storage、不得触发补数，也不得替代轻量主路径。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | CR006-AC-007、CR006-AC-008、CR006-AC-011 |
| HLD | §23.3、§23.6、§23.8、§23.10 |
| ADR | ADR-016、ADR-017、ADR-018 |

## 开发上下文（dev_context）

**背景说明**：Backtrader 的价值在交易模拟和风险分析，不在数据获取、PIT 生成或复权计算。CR-006 明确新数据主线来自 Tushare structured lake，因此 Backtrader feed 必须在数据层完成清洗与质量门后再消费。

**输入文件**：`process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、S01/S02 Story/LLD、CR005-S06 Story/LLD、`engine/backtrader_adapter.py`、`engine/backtest.py` 或 selector、`market_data/readers.py`。

**输出文件**：后续实现可修改 `engine/backtrader_adapter.py`、`engine/backtest.py` 或 selector、`market_data/readers.py` 和 `tests/test_cr006_backtrader_clean_feed.py`。本规划阶段不修改这些业务文件。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| `build_backtrader_clean_feed` 或等价 | clean OHLCV、calendar、factor panel、score、benchmark status、quality policy | Backtrader data feed 或 feed bundle | quality fail、PIT fail、复权冲突时拒绝 |
| backend selector | backend name、dependency availability、feed contract | `backtrader_result` 或 `backend_unavailable` | 未安装 Backtrader 时不影响轻量主路径 |
| unavailable contract | required_missing、quality_failed、backend_unavailable | structured status、next_action/remediation spec | 不自动执行 Tushare fetch/backfill |

**设计约束**：

- Backtrader feed 不读取 raw/manifest。
- Backtrader adapter 不读取 `TUSHARE_TOKEN`，不导入 `market_data.connectors`、`runtime`、`storage`。
- PIT as-of join、复权价格、quality gate 在 Pandas 数据层完成。
- Backtrader 只负责调仓、成交、成本、仓位、净值和风险分析。
- Backtrader 输出仅作为 optional 对照报告，不覆盖轻量回测结果。
- 默认测试不安装真实外部依赖时必须能返回 `backend_unavailable` 或跳过 optional backend，不影响轻量主路径。

**命名规范**：使用 `clean_feed`、`backend_unavailable`、`quality_failed`、`pit_failed`、`adjustment_policy_mismatch` 等显式状态。

**平台目标**：本地 Python 研究工具；Backtrader 为 optional backend；依赖变更必须等 CP5 LLD 确认后通过 uv 管理。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR006-S03-T1 | 修改 | `market_data/readers.py` | 暴露 Backtrader clean feed 所需 reader contract 或 feed bundle |
| CR006-S03-T2 | 修改 | `engine/backtrader_adapter.py` | 接入 clean feed contract，禁止 connector/runtime/token/raw/manifest |
| CR006-S03-T3 | 修改 | `engine/backtest.py` 或 selector | 未安装 Backtrader 时返回 backend_unavailable，不影响轻量主路径 |
| CR006-S03-T4 | 创建 | `tests/test_cr006_backtrader_clean_feed.py` | 覆盖 quality/PIT/复权 gate、optional dependency、no connector import、no fetch |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr006_backtrader_clean_feed.py`。

**验证方式**：clean feed fixture、dependency monkeypatch、静态 import 扫描、quality gate 测试。

**依赖环境**：Python 3.11、uv、pytest；默认不需要真实 Backtrader 安装、不需要 token、不联网。

**关键验证场景**：

- clean feed quality pass 时可进入 optional backend。
- quality fail、PIT fail、复权冲突均阻断 Backtrader。
- 未安装 Backtrader 时返回 `backend_unavailable`。
- Backtrader adapter 不导入 connector/runtime/storage。
- Backtrader adapter 不读取 raw/manifest/token，不触发 fetch/backfill。

## 量化验收标准（acceptance_criteria）

- [ ] Backtrader 运行输入 100% 来自 quality gate 后 clean OHLCV/factor/score feed。
- [ ] Backtrader adapter 读取 raw/manifest 的次数为 0。
- [ ] Backtrader adapter 读取 `TUSHARE_TOKEN` 或导入 connector/runtime/storage 的次数为 0。
- [ ] Backtrader 触发 Tushare fetch/backfill 的次数为 0。
- [ ] quality/PIT/复权 gate fail 时 Backtrader 被阻断。
- [ ] 未安装 Backtrader 时轻量主路径仍可用，并返回结构化 `backend_unavailable`。
- [ ] 不修改真实 `data/**`、`.env`、README、docs、`delivery/**`。

## 阻塞说明

无 BLOCKING。Backtrader 依赖版本和 optional dependency 分组仍为 OPEN；该问题不阻塞 feed contract 设计，但阻塞后续依赖落地和 CP5 实现范围。
