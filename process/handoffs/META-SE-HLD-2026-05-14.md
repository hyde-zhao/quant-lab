---
handoff_type: "phase-transition"
from_agent: "meta-po"
to_agent: "meta-se"
from_phase: "requirement-clarification"
to_phase: "solution-design"
status: "ready_for_hld_design"
created_at: "2026-05-14"
created_by: "meta-po"
source_artifacts:
  - "process/STATE.md"
  - "process/REQUEST.md"
  - "process/USE-CASES.md"
  - "process/REQUIREMENTS.md"
  - "process/CLARIFICATION-LOG.md"
  - "checkpoints/REQUIREMENTS-CHECKPOINT.md"
blocked: false
allowed_outputs:
  - "process/HLD.md"
  - "process/ARCHITECTURE-DECISION.md"
forbidden_outputs:
  - "process/STORY-BACKLOG.md"
  - "process/DEVELOPMENT-PLAN.yaml"
  - "process/stories/STORY-*.md"
  - "process/stories/STORY-*-LLD.md"
  - "delivery/**"
---

# meta-se HLD 交接说明

## 当前决策

用户已明确回复“确认通过”，接受：

- `process/USE-CASES.md` v1.3。
- `process/REQUIREMENTS.md` v1.3。
- Q-004 至 Q-019 按当前默认边界进入 HLD。

`meta-po` 已将工作流从 `requirement-clarification` 推进到 `solution-design`。当前阶段只允许输出 HLD 草稿并准备 HLD 确认检查点；不得进入 `story-planning`，不得生成 Story、LLD 或代码。

## meta-se 必读上下文

| 文件 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、门控状态和禁止越界范围 |
| `process/REQUEST.md` | 用户原始目标与交付预期 |
| `process/USE-CASES.md` | 已确认 v1.3 使用场景、边界、成功指标和 Out of Scope |
| `process/REQUIREMENTS.md` | 已确认 v1.3 结构化需求、数据契约、报告 schema、风险假设和里程碑 |
| `process/CLARIFICATION-LOG.md` | Q-004 至 Q-019 的 HLD 必答项 |
| `checkpoints/REQUIREMENTS-CHECKPOINT.md` | 需求确认范围与用户确认结果 |

## 不应加载或生成

- 不加载历史失败轮次之外的无关草稿。
- 不生成 `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml` 或任何 `process/stories/` 文件。
- 不写入 `delivery/`，不实现代码，不输出安装脚本。
- 不把 Q-004 至 Q-019 当作已完成设计决策；它们只是已获准进入 HLD，必须在 HLD 中明确结论。

## 可直接转发给 meta-se 的任务说明

你是 `meta-se`。请基于已确认的 `process/USE-CASES.md` v1.3、`process/REQUIREMENTS.md` v1.3、`process/CLARIFICATION-LOG.md` 和本交接文件，在 `solution-design` 阶段输出 `process/HLD.md` 草稿，并将 HLD frontmatter 标记为 `status: ready-for-review`。如需要记录关键架构决策，可同步输出 `process/ARCHITECTURE-DECISION.md`，但不得拆解 Story、不得生成 LLD、不得实现代码。

HLD 必须覆盖以下内容：

1. 轻量本地日频回测架构：坚持项目内轻量回测层，不默认引入 RQAlpha、Backtrader、vectorbt、bt 或完整事件驱动交易系统。
2. 数据准备层与回测引擎隔离：联网数据准备/更新流程与回测、扫描、候选筛选、本地差异分析主路径物理隔离；主路径离线只读本地 parquet、manifest 和质量报告摘要。
3. AKShare/本地 parquet 数据链路：定义 raw 缓存、标准化 parquet、manifest/checkpoint、质量报告之间的派生关系；明确 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet` 的 schema 与失败行为。
4. 限速、退避和断点续传：明确 `request_interval_seconds`、`batch_size`、`max_concurrency`、`max_retries`、`backoff_policy`、`force_refresh`、`recent_trade_days_backfill` 的默认值、配置位置、状态记录和验证方式。
5. manifest 与质量报告：定义 manifest 文件格式、字段、状态枚举、批次 ID、恢复算法、质量报告字段、质量阈值、`quality_status` 枚举和数据新鲜度披露规则。
6. 回测边界：明确复权口径默认值与配置项、T 日收盘后信号/T+1 或之后成交、成交价口径、成本扣除、收益归属、`available_at <= decision_time` 校验层级与失败策略。
7. 偏差与真实性限制：明确固定当前沪深 300 非 PIT 股票池、幸存者偏差、完整停牌状态、涨跌停撮合、新股上市初期规则、退市整理/摘牌、ST 历史状态、财报披露日、历史成分变化等第一版限制如何进入报告 metadata。
8. 缺失数据与不可交易处理：定义历史窗口不足、端点价格缺失、成交价缺失、无成交、停牌或未知交易状态在数据加载、信号排名、组合成交三层的处理表。
9. 参数扫描与报告：覆盖 60 组动量参数扫描、`reports/momentum_param_sweep_local.csv`、`reports/momentum_candidates_local.csv`、候选不超过 4 组、样本内过拟合警示、扫描失败记录和报告 metadata。
10. 后续增强路线：按 PIT universe provider、交易状态表、涨跌停约束、事件级 `available_at`、偏差审计报告、RSI/MACD 策略扩展组织演进路线，并说明每类增强对 raw/manifest/质量报告/离线读取契约的影响。

HLD 还必须满足项目设计评审规则：

- 成功标准必须量化。
- 集成契约必须显式说明调用方向、调用时机、输入、输出、降级策略和调用方同步修改范围。
- 每个阶段必须有前置条件校验和失败路径。
- ADR、风险矩阵、NFR、模块职责和流程图不得自相矛盾。
- 对 Q-004 至 Q-019 逐项给出 HLD 结论或明确设计默认值。

## HLD 完成后的门控

HLD 完成后，`meta-se` 应停止在 `solution-design` 阶段，由 `meta-po` 发起 HLD 检查点。HLD 未经用户确认前，不得进入 Story 拆解。
