---
check_id: "CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21"
status: "PASS-ROUTED"
checked_at: "2026-05-21T07:00:40+08:00"
agent_role: "meta-po"
agent_name: "po-sun"
workflow_id: "local_backtest"
active_change: "CR-007"
secondary_change: "CR-008"
---

# CR007 / CR008 集成受理与调度路由

## 结论

用户已明确要求将 `CR-008` 纳入开发计划，且 CR007/CR008 冲突时以 CR008 为主。本轮 meta-po 正式将 `CR-008` 从 `draft-pending-intake` 推进到 `intake-accepted-parallel-design-routing`。

路由策略：

- `CR-007` 保持当前 story-execution 主线，当前可继续调度 `CR007-S02-benchmark-calendar-backfill` 离线实现。
- `CR-008` 不直接进入实现，先并行进入 solution-design 影响分析与设计刷新，必须经过 CP3 / CP4 / CP5 后才允许实现。
- `CR007-S04` 与 `CR007-S05` 与 CR008 的报告字段、benchmark 语义、研究 metadata、旧报告 / 文档护栏高度重叠，在 CR008 设计影响结论输出前应保持 queued，不建议提前实现。
- 如 CR008 影响 CR007 已确认合同，以 CR008 的研究级数据口径为主，并由 meta-se / meta-dev / meta-qa 给出回滚或修订清单。

## CR007 当前开发事实

| Story | 当前状态 | 证据 | 下一步 |
|---|---|---|---|
| `CR007-S01-prices-long-horizon-backfill-planner` | verified | CP6 PASS：`process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md`；CP7 PASS：`process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md` | 已完成，无需重跑 |
| `CR007-S02-benchmark-calendar-backfill` | dev_ready | `process/STATE.md.parallel_execution.dev_ready`；LLD confirmed=true；CP5 PASS；S01 CP6/CP7 PASS | 可由主线程真实 resume/send_input `meta-dev/dev-zhang` 执行既有 handoff |
| `CR007-S03-index-members-stock-basic-datasets` | blocked | blocked_by=`CR007-S02`；依赖类型 `contract+file-conflict`；冲突文件 `market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py` | 等 S02 CP6 PASS 且文件冲突清理后再判定 |
| `CR007-S04-experiment-real-benchmark-consumption` | blocked / hold-for-CR008-impact | 依赖 S02/S03，且与 CR008 benchmark/report 字段拆分直接重叠 | 等 CR008 设计影响结论后再实现 |
| `CR007-S05-data-quality-report-and-doc-guardrail` | blocked / hold-for-CR008-impact | 依赖 S04，且与 CR008 research metadata、legacy report 和文档说明重叠 | 等 CR008 设计影响结论后再实现 |

## 禁止动作

本轮调度和后续子 agent 均不得执行：

- 真实 Tushare 抓取或真实联网 backfill。
- 真实 `<configured-lake-root>` 写入或大规模真实 lake 读写。
- 读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码、私有真实路径或任何凭据。
- 读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 读取、打开、覆盖或把旧 `reports/data_quality_report.csv` 作为 current quality truth、coverage proof 或 fixture。

## CR007 / CR008 冲突矩阵

| 冲突面 | CR007 当前口径 | CR008 草案口径 | 冲突等级 | 决策 |
|---|---|---|---|---|
| benchmark 字段 | S02/S04 强化真实 `hs300_index`，缺失时保留 `proxy_baseline` | 新报告必须拆分 `proxy_*` 与 `hs300_*`，不得把代理写成真实超额 | 高 | CR008 为主；CR007-S04 实现前必须消费 CR008 字段语义 |
| 研究入口 | CR007 以数据生产和实验 13 消费为主 | CR008 要新增 `research_input_v1` / `research_dataset_builder` | 高 | CR008 为主；CR007-S02/S03 可作为生产前置，CR008 统一消费侧合同 |
| PIT / 股票池 | CR007-S03 定义 readiness 与 PIT/non-PIT 状态 | CR008 要严肃因子报告 PIT 缺失时失败或显式降级 | 高 | CR008 为主；S03 输出必须能支撑 CR008 门禁 |
| label window | CR007 不主攻未来收益标签窗口 | CR008 要把 `forward_return_horizon` 与 `label_available_end` 变成准入门禁 | 中 | 纳入 CR008 设计，不阻塞 CR007-S02 |
| 复权口径 | CR007-S01/S03 涉及 qfq / adj_factor / quality gate | CR008 要复权口径单一和 lineage 成为硬门禁 | 中 | CR008 为主；若要求改变 S01/S03 输出，必须走设计修订 |
| 旧质量报告 | CR007-S05 标记 legacy old report | CR008 同样要求旧报告不能作为 current truth，且新报告 metadata 强制披露 | 中 | 合并到 CR008 设计；CR007-S05 暂缓到 CR008 影响结论后 |
| 文件所有权 | CR007-S02/S03 共享 `normalization.py` / `validation.py` / `readers.py` | CR008-S03/S04/S05 可能新增 `engine/research_dataset.py` 并读 `market_data/readers.py` | 高 | CR007-S02 可先做；CR007-S03 与 CR008 实现需等 meta-dev 冲突分析 |
| 文档 | CR007-S05 改 README / USER-MANUAL | CR008 也需要研究级数据口径说明 | 高 | CR008 为主；避免 CR007-S05 提前写文档后返工 |

## 并行调度判断

当前允许的并行：

- `CR007-S02` 离线实现可以与 `CR008` solution-design 影响分析并行。
- `meta-se`、`meta-dev`、`meta-qa` 三条 CR008/合并影响分析 lane 可以并行。

当前禁止的并行：

- `CR007-S02` 与 `CR007-S03` 不得并行开发。
- `CR008` 任何实现不得在 CP3 / CP4 / CP5 前开始。
- `CR007-S04` / `CR007-S05` 不建议在 CR008 设计影响结论前实现。

## 子 Agent Handoff

| Agent | handoff | 调度状态 |
|---|---|---|
| `meta-se` | `process/handoffs/META-SE-CR008-RESEARCH-DATA-LAYER-DESIGN-2026-05-21.md` | handoff-only，等待主线程真实调度 |
| `meta-dev` | `process/handoffs/META-DEV-CR007-CR008-PARALLEL-DEV-ANALYSIS-2026-05-21.md` | handoff-only，等待主线程真实调度 |
| `meta-qa` | `process/handoffs/META-QA-CR007-CR008-MERGED-VALIDATION-STRATEGY-2026-05-21.md` | handoff-only，等待主线程真实调度 |
| `meta-dev` S02 实现 | `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md` | 既有 handoff，S02 dev_ready，等待主线程真实 resume/send_input |

## 下一步

主线程应并行调度：

1. `meta-dev/dev-zhang`：执行 `CR007-S02` 既有实现 handoff。
2. `meta-se`：执行 CR008 design impact / refresh handoff。
3. `meta-dev`：执行 CR007/CR008 文件所有权与并行实现分析 handoff。
4. `meta-qa`：执行 CR007/CR008 合并验证策略 handoff。

CR008 若经 meta-se 刷新 HLD/ADR/Story Plan 后产出 CP3/CP4，则必须先回到用户人工确认；CR008-BATCH-A 全量 LLD 与 CP5 批次确认完成前，不得进入 CR008 实现。
