---
checkpoint_type: "hld"
status: confirmed
version: "1.0.1"
source_hld: "process/HLD.md"
source_requirements_version: "1.3"
source_use_cases_version: "1.3"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-05-14"
created_at: "2026-05-14"
created_by: "meta-po"
issued_at: "2026-05-14"
issued_by: "meta-po"
coverage_verified: "process/HLD.md §7 与 §20 均完整覆盖 Q-004 至 Q-019"
---

# HLD 确认检查点

> 本检查点由 meta-po 发起，供用户确认 `process/HLD.md` 是否可作为后续 Story 拆解输入。当前 HLD 已确认通过；后续进入 Story 计划阶段，但 Story 计划未确认前不得进入 `story-execution`、不得生成 LLD、代码或 `delivery/**`。

## 待确认产物

| 文件 | 状态 | 说明 |
|---|---|---|
| `process/HLD.md` | confirmed / confirmed=true | §7 与 §20 均完整覆盖 Q-004 至 Q-019；用户已确认可作为后续 Story 拆解输入 |

## 当前检查点状态

本检查点已确认通过。`meta-se` 已将 `process/HLD.md` §20 修订为 Q-004 至 Q-019 逐项确认口径；`meta-po` 已复核 `process/HLD.md` §7 与 §20 均完整覆盖 Q-004 至 Q-019。

用户已明确回复“确认通过，让自agent继续推行”。该回复视为 HLD 人工确认通过。HLD 当前为 `status=confirmed`、`confirmed=true`，允许进入 `story-planning`。下一阶段仍需保持 Story 计划确认门控；在 Story 计划确认前，不得进入 `story-execution`，不得生成 LLD、代码或 `delivery/**`。

## 设计范围确认

| 检查项 | HLD 覆盖情况 |
|---|---|
| 轻量本地日频回测架构 | 已覆盖；推荐方案 A，不默认引入 RQAlpha、Backtrader、vectorbt、bt |
| 数据准备层与回测引擎隔离 | 已覆盖；data_prep 可联网，backtest/scan/candidate/report 主路径离线只读 |
| AKShare/本地 parquet 数据链路 | 已覆盖；raw、标准 parquet、manifest、质量报告均有契约 |
| 限速、节流、退避、断点续传 | 已覆盖；给出默认值、状态记录和恢复算法 |
| raw 缓存、标准化 parquet、manifest、质量报告 | 已覆盖；定义路径、schema、状态枚举和质量阈值 |
| 复权、未来函数、幸存者偏差 | 已覆盖；默认前复权、`available_at` 校验、非 PIT 披露 |
| 停牌、涨跌停、新股、退市、ST、财报披露日、指数历史成分边界 | 已覆盖；第一版限制项进入 metadata，后续增强路线明确 |
| 参数扫描与报告 | 已覆盖；60 组扫描、候选不超过 4 组、失败行保留、过拟合警示 |
| 后续增强路线 | 已覆盖；PIT、交易状态、涨跌停、事件 `available_at`、偏差审计、RSI/MACD |
| Q-004 至 Q-019 | 已逐项给出 HLD 默认决策，状态为已确认 |

## 需人工确认的 HLD 决策

| 问题 ID | 待确认决策 | HLD 默认值 | 影响范围 | 确认状态 |
|---|---|---|---|---|
| Q-004 | 是否接受默认复权口径为 `adjustment_policy=qfq` 前复权，并要求同一次回测、扫描、候选筛选和聚宽对照不得混用复权口径 | 默认前复权 `qfq`；报告记录实际 `adjustment_policy`；同一次研究链路必须使用一致复权口径 | 数据契约、动量排名、收益计算、候选筛选、聚宽对照、报告 metadata、ADR-003 | 已确认 |
| Q-005 | 是否接受默认成交假设为 T 日收盘后生成信号，T+1 收盘价成交，并按 HLD 口径归属成本和收益 | T 日收盘后生成信号；T+1 收盘价成交；成本在 T+1 调仓后从组合净值扣除；新持仓从 T+1 收盘后承担后续收益 | 回测流程、组合层、成本模型、净值归属、差异解释、ADR-004 | 已确认 |
| Q-006 | 是否接受第一版 `index_members.parquet` 使用固定当前沪深 300 快照，并明确披露非 PIT 股票池 | 使用固定当前沪深 300 快照；必含 `symbol`，建议含 `snapshot_date`、`is_pit_universe=false`；PIT provider 后续增强 | 股票池 schema、偏差披露、报告 metadata、增强路线 | 已确认 |
| Q-007 | 是否接受历史窗口不足、端点价格缺失、成交价缺失、无成交、停牌或未知交易状态的分层处理策略 | 历史窗口不足和信号端点价格缺失在信号层剔除；成交价缺失、无成交、停牌或未知交易状态在组合层留现金并记录未成交原因；关键输入完全缺失则失败 | 缺失处理表、信号层、组合层、失败降级、审计报告 | 已确认 |
| Q-008 | 是否接受最小 price schema、`adjustment_policy` 记录位置，以及 `available_at` 缺失时的日线收盘价推导规则 | 最小 price schema 为 `trade_date`、`symbol`、`close`；`adjustment_policy` 可作为列或 manifest 数据集 metadata；`available_at` 缺失时仅日线收盘价可按“交易日 T 收盘后可用”推导 | parquet schema、manifest metadata、未来函数校验、报告限制项 | 已确认 |
| Q-009 | 是否接受涨跌停字段第一版不强制进入 schema，但必须进入报告 metadata 限制项并作为 P1 增强 | 第一版不强制 `limit_up`、`limit_down` 入 schema；报告 metadata 必须披露涨跌停限制；P1 增强补齐涨跌停约束 | price schema、报告 metadata、真实性增强路线 | 已确认 |
| Q-010 | 是否接受未来函数校验覆盖数据加载层、信号层、股票池层和报告审计层，且事件层第一版禁用 | 校验覆盖数据加载层、信号层、股票池层和报告审计层；事件层第一版禁用；后续事件字段必须提供字段级 `available_at` | 校验策略、未来函数防护、NFR、事件增强边界 | 已确认 |
| Q-011 | 是否接受财报披露日、财报/公告事件和 ST 事件字段第一版 Out of Scope，且后续必须事件级 `available_at` | 财报披露日、财报/公告事件和 ST 事件字段第一版不进入策略输入；后续纳入时必须提供事件级 `available_at` | 非目标、相邻边界、事件增强路线、报告限制项 | 已确认 |
| Q-012 | 是否接受数据准备默认限速参数 `request_interval_seconds=2`、`batch_size=50`、`max_concurrency=1` | 默认请求间隔 2 秒、批大小 50、最大并发 1；配置位置建议为 `config/data_prep.yaml` 或等价 CLI 参数 | 数据准备链路、节流策略、数据源压力、运行耗时 | 已确认 |
| Q-013 | 是否接受默认重试和退避策略 `max_retries=3`、`backoff_policy=exponential_jitter`、基础等待 2 秒、最大单次等待 60 秒 | 最多 3 次重试；指数抖动退避；基础等待 2 秒；最大单次等待 60 秒；每次重试写入 manifest `retry_events` | 失败恢复、退避策略、manifest、数据准备可追溯性 | 已确认 |
| Q-014 | 是否接受 `data/manifests/data_prep_manifest.jsonl` 作为 checkpoint 事实源，并采用完整批次状态枚举 | `data/manifests/data_prep_manifest.jsonl` 是 checkpoint 事实源；批次状态枚举为 `pending`、`running`、`success`、`partial_success`、`failed`、`skipped` | 断点续传、批次审计、失败降级、质量报告输入 | 已确认 |
| Q-015 | 是否接受默认 `recent_trade_days_backfill=5`，并按 HLD 范围回补价格、复权相关日线、固定成分股快照和交易日历 | 默认回补最近 5 个交易日；价格和复权相关日线数据使用该窗口；固定成分股快照不滚动回补；交易日历按目标区间缺口补齐 | 增量更新、数据新鲜度、交易日历覆盖、回补成本 | 已确认 |
| Q-016 | 是否接受 raw 缓存第一版长期保留、不自动清理，并按 `source/interface/date/batch_id` 组织 | raw 缓存长期保留且不自动清理；路径按 `source/interface/date/batch_id` 组织；清理只允许用户显式执行 | raw 缓存、可复现性、磁盘空间、用户清理操作 | 已确认 |
| Q-017 | 是否接受 manifest 使用 JSONL、包含 `schema_version`，并通过 `manifest_run_id` 关联质量报告 | manifest 使用 JSONL；schema 版本字段为 `schema_version`；质量报告通过 `manifest_run_id` 关联对应数据准备运行 | manifest schema、质量报告关联、schema 升级、审计追溯 | 已确认 |
| Q-018 | 是否接受 `quality_status=pass/warn/fail`，并按 HLD 阈值处理 schema 缺失、覆盖缺口、重复键、异常价格和缺失率 | `quality_status` 为 `pass`、`warn`、`fail`；schema 缺失、覆盖缺口、未解决重复键、异常价格或请求区间缺失率 > 5% 为 `fail`；0 < 缺失率 <= 5% 为 `warn` | 质量报告、数据准备阻塞/告警策略、回测启动前校验 | 已确认 |
| Q-019 | 是否接受同时披露交易日新鲜度和自然日新鲜度，并按 HLD 字段和计算口径执行 | 同时披露 `data_freshness_trade_days` 与 `data_freshness_calendar_days`；前者按目标结束日与 `data_coverage_end` 间开市日数计算，后者按当前日期与 `last_successful_update_at` 计算 | 数据新鲜度披露、失败降级、质量报告、报告 metadata | 已确认 |

## 设计评审自检

| 规则 | 自检结果 |
|---|---|
| 修订记录 | `process/HLD.md` 已包含修订记录 |
| 量化成功标准 | 已包含 2019-2025、60 行扫描、候选 <= 4、0 网络调用、限速默认值、质量字段等量化条件 |
| 集成契约 | 已定义调用方向、调用时机、输入、输出、降级策略和调用方同步修改范围 |
| 相邻边界 | 已澄清 data_prep、backtest、聚宽验证、真实性增强、策略扩展边界 |
| 前置校验与失败路径 | 已定义数据准备、标准化、质量报告、单次回测、扫描、候选生成的前置条件和失败路径 |
| 可操作回退/降级 | 已定义数据源失败时的离线降级、warn/fail 质量策略和单组扫描失败行保留 |
| 理论依据 | 使用分层架构、管道过滤、数据契约、质量分级和偏差审计；枚举清单来自需求 v1.3 与领域经验 |
| 遗留问题状态 | 已收敛；`process/HLD.md` §7、§20 与本检查点均完整覆盖 Q-004 至 Q-019，当前状态为已确认 |
| Gotchas | 已包含常见误用和规避 |
| ADR 与章节对齐 | ADR 候选均标注已回写章节；正式 ADR 待 HLD 确认后生成 |
| 官方/事实来源 | 数据源依据来自 `process/INPUT-INDEX.md`；本 HLD 不涉及平台安装路径或 `delivery/**` |

## meta-po 确认记录

**确认状态**：已确认

**审核意见**：`process/HLD.md` §7 与 §20 已逐项覆盖 Q-004 至 Q-019；用户明确回复“确认通过，让自agent继续推行”，HLD 可作为后续 Story 拆解输入。

**确认人**：user

**确认时间**：2026-05-14

## 用户确认结果

用户已选择“确认通过”：HLD 可作为后续 Story 拆解输入。`meta-po` 已把 `process/HLD.md` 标记为 confirmed，并进入 `story-planning`。
