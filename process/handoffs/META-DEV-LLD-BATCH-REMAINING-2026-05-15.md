---
handoff_id: "META-DEV-LLD-BATCH-REMAINING-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-dev"
created_at: "2026-05-15"
phase: "story-planning"
task_type: "lld-batch-draft"
workflow_id: "local_backtest"
change_id: null
story_id: "LLD-BATCH-REMAINING"
wave_id: "W1-W4"
status: "ready-to-dispatch"
governance: "LLD 批量输出门控；不得实现"
fork_context: false
implementation_allowed: false
delivery_write_allowed: false
---

# meta-dev 交接：剩余 Story LLD 批量起草

## 1. 任务目标

请根据已确认的 Story Backlog、Development Plan、HLD 和 ADR，补齐剩余 Story 的 LLD。当前工作流已纠偏为：Story 分解完成后先输出 LLD 包，人工确认后再进入对应 Story 开发。

本 handoff 不授权实现代码、生成数据、写入 `delivery/**` 或生成安装脚本。

## 2. 必须读取的最小上下文

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前纠偏状态、LLD 盘点、禁止范围、agent lifecycle |
| `process/STORY-STATUS.md` | Story 状态、缺失 LLD 清单和当前批量门控 |
| `process/LLD-BATCH-PLAN.md` | 本轮 LLD 批量输出计划、并行策略和检查点要求 |
| `process/STORY-BACKLOG.md` | 13 个 Story 的范围、依赖、验收摘要、REQ/HLD/ADR 映射 |
| `process/DEVELOPMENT-PLAN.yaml` | Wave、依赖 DAG、输出文件边界和完成准则 |
| `process/HLD.md` | 架构、流程、模块职责、NFR 和阶段落地依据 |
| `process/ARCHITECTURE-DECISION.md` | ADR 约束，尤其是离线隔离、uv、复权、交易约束、质量降级和报告边界 |
| `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` | 已有 W1 loader LLD；下游 STORY-005/006 需引用其接口，若 open_items 影响下游需状态化 |
| `process/stories/STORY-005-momentum-portfolio-engine.md` 至 `process/stories/STORY-013-strategy-extension-rsi-macd.md` | 本轮 9 个目标 Story 卡片 |
| `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md` 至 `process/stories/STORY-003-parquet-quality-report-LLD.md` | 已确认上游 LLD，可作为接口和边界依据 |

不要加载完整会话历史、无关失败轮次、交付目录内容或未被列为输入的草稿。

## 3. 必须输出的 LLD

| Story ID | 目标路径 | 主要文件范围 |
|---|---|---|
| STORY-005 | `process/stories/STORY-005-momentum-portfolio-engine-LLD.md` | `strategies/momentum.py`, `engine/portfolio.py`, `engine/contracts.py` |
| STORY-006 | `process/stories/STORY-006-backtest-metrics-report-metadata-LLD.md` | `engine/backtest.py`, `engine/metrics.py`, `engine/reporting.py`, `engine/contracts.py` |
| STORY-007 | `process/stories/STORY-007-parameter-sweep-report-LLD.md` | `engine/scanner.py`, `reports/momentum_param_sweep_local.csv` |
| STORY-008 | `process/stories/STORY-008-candidate-report-jq-template-LLD.md` | `engine/candidates.py`, `reports/momentum_candidates_local.csv` |
| STORY-009 | `process/stories/STORY-009-pit-universe-provider-contract-LLD.md` | `engine/universe.py`, `engine/normalizer.py`, `engine/quality.py` |
| STORY-010 | `process/stories/STORY-010-trade-status-constraints-LLD.md` | `engine/trade_status.py`, `engine/portfolio.py`, `engine/quality.py` |
| STORY-011 | `process/stories/STORY-011-limit-event-available-at-LLD.md` | `engine/trading_constraints.py`, `engine/events.py`, `engine/data_loader.py` |
| STORY-012 | `process/stories/STORY-012-bias-audit-report-LLD.md` | `engine/bias_audit.py`, `reports/bias_audit_report.*` |
| STORY-013 | `process/stories/STORY-013-strategy-extension-rsi-macd-LLD.md` | `strategies/base.py`, `strategies/rsi.py`, `strategies/macd.py`, `engine/scanner.py` |

如发现 `STORY-004` 已有 LLD 与下游接口存在矛盾，只允许最小修订 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md` 并在 `open_items` / 修订记录中说明；不得将其标记为 confirmed。

## 4. 并行许可

允许在 LLD 文档层并行起草，但必须保持依赖显式化：

- STORY-005/006 可同批输出；STORY-006 对 STORY-005 的接口假设必须写入 `shared_fragments` 或 `open_items`。
- STORY-007/008 可同批输出；STORY-008 对扫描报告 schema 的依赖必须明确。
- STORY-009/010/011/012 可同批输出；STORY-010/011/012 对 STORY-009、STORY-010、STORY-011 的依赖必须明确。
- STORY-013 可同批输出；依赖 STORY-008，不得要求 W3 已实现。

并行不代表可并行实现。实现调度仍由后续人工确认后的 Story/Wave 门控决定。

## 5. 每个 LLD 的硬性要求

每个 LLD 必须：

1. 保持 14 个可见章节：Goal、Requirements、模块拆分、文件影响范围、数据模型、API/Interface、核心流程、技术细节、安全与性能、测试设计、实施步骤、风险、回滚与发布、Definition of Done。
2. frontmatter 包含 `story_id`、`title`、`story_slug`、`tier`、`status: "ready-for-review"`、`confirmed: false`、`source_story`、`source_hld`、`source_adr`、`shared_fragments`、`open_items`、`depends_on`。
3. 明确文件影响范围，且不得扩大到 Story 卡片未授权的实现文件。
4. 明确输入/输出接口、异常类型、失败行为、测试策略和回滚策略。
5. 将不确定依赖写入 `open_items`，不得用隐含假设替代。
6. 使用确定性动词和量化条件，避免“尽可能”“视情况”等不可验收描述。

## 6. 禁止范围

本 handoff 明确禁止：

- 实现任何代码。
- 生成或写入真实数据。
- 写入 `data/**`、`reports/**` 的真实运行产物。
- 写入 `delivery/**`。
- 生成安装脚本。
- 创建仓库级 guardrail 脚本。
- 修改 `pyproject.toml`、`uv.lock` 或实现源文件。
- 把任一 Story 推进到 `in-development`。
- 将任一未确认 LLD 写为 `confirmed=true`。

## 7. 允许回写的运行态文件

允许回写：

- 本 handoff 第 3 节列出的 9 个 LLD 文件。
- `process/stories/STORY-005-*.md` 至 `process/stories/STORY-013-*.md` 的状态，从 `package-draft` 推进到 `package-ready-for-review`。
- `process/STORY-STATUS.md` 的 LLD 盘点和门控状态。
- `process/STATE.md` 的 `phase_artifacts`、history 和 next_action。
- 必要时最小修订 `process/LLD-BATCH-PLAN.md` 的盘点状态。

不允许写 `checkpoints/**`；批量检查点由 meta-po 在复核 LLD 后创建。

## 8. 交回条件

交回时必须说明：

1. 已输出哪些 LLD。
2. 是否存在未完成 LLD。
3. 每个 LLD 的 `open_items` 数量。
4. 是否修改了 STORY-004 LLD，以及修改原因。
5. 已确认未实现代码、未生成数据、未写 `delivery/**`、未生成安装脚本、未创建 guardrail 脚本。

meta-po 收到交回后将创建批量 LLD / Story Package 人工确认检查点。
