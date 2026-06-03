---
cr_id: "CR-012"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "limited-window readiness audit 影响 PIT universe、available_at 语义、coverage denominator、报告声明和生产级 claim 边界，命中数据合同、审计口径和多 Story 依赖。"
rollback_to: "solution-design"
approval_result: "approved-implemented-final-review-closed"
created_at: "2026-05-24T00:00:00+08:00"
updated_at: "2026-05-30T14:25:41+08:00"
created_by: "codex"
approved_by: "user"
approved_at: "2026-05-24T00:00:00+08:00"
closed: true
closed_by: "meta-po"
closed_at: "2026-05-30T14:25:41+08:00"
closure_checkpoint: "checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md"
close_approval_text: "@meta-po 好的按照你推荐的顺序，逐步完成。"
source: "run-exec"
linked_issue: ""
---

# CR-012 Limited Window Readiness 审计口径修正

> 2026-05-30T14:25:41+08:00 状态更新：G0 第一批 CR 状态收口已通过 `checkpoints/CP8-G0-CR-STATUS-CLOSURE-2026-05-30.md` 人工审查，CR-012 关闭。关闭依据为定向测试 `24 passed`、最终 readiness summary `overall_status=production_strict_target_window_pass` 且 `blocking_count=0`；关闭只代表 limited-window strict 修正完成，不外推到 full-history，不授权真实 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作或 QMT 操作。

## 变更描述

`reports/data_lake_readiness_limited_2025_2026/*` 暴露出当前 readiness audit 对 `2025-02-11..2026-02-18` limited window 的判断混合了真实数据缺口、审计模式错配和 metadata 语义问题：

- `index_members` 当前是 snapshot / rebalance 形态，但旧审计只按每日 materialized `trade_date` 行计算覆盖，导致 PIT membership 被误判为每日 coverage gap。
- `index_weights` 旧口径容易被误读为 PIT universe 证明；新口径只允许其证明权重行与 as-of membership 对齐。
- `trade_calendar.available_at` 旧口径把 `next_open` 类字段当成通用 future availability；新口径要求 `available_at` 表示交易日历已知时间，`next_open` 必须迁移到独立字段。
- `adj_factor.available_at` 仍保持 strict PIT 检查；若只能证明 ex-post 复权，报告必须保留 blocked claim。
- `prices` / `adj_factor` 等日频数据缺口需要结合 PIT membership、tradability 和 stock lifecycle 分类，不应把停牌、不可交易、未上市或退市全部写成真实行情缺失。
- limited-window 结论不能外推到 `2020-01-01..2024-12-31`，也不能直接声明持续生产级 `production_current_truth`。

本 CR 只修改代码、审计口径和报告 / 文档声明；不执行真实补数、不写真实 lake、不联网抓取 provider、不读取凭据、不读取旧 `data/**`。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 不变 | CR-012 场景变更完整记录在本 CR；不替换既有场景基线 | 不适用 | approved |
| `process/REQUIREMENTS.md` | 不变 | CR-012 需求修正完整记录在本 CR；不替换既有需求基线 | 不适用 | approved |
| `process/HLD.md` | 原文档更新 | 既有 CR-011 研究消费设计保留；追加 §28 limited-window audit 声明边界 | `## 修订记录` | approved |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | 既有 CR-010 / CR-011 数据湖设计保留；追加 §15 readiness audit 口径 | `## 修订记录` | approved |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | CR-010 historical pass 作为历史发布结论保留；新增 CR-012 当前 strict 复验边界说明 | 相关状态章节 | approved |
| `reports/data_lake_readiness_limited_2025_2026/*` | 不变 | 作为触发 CR-012 的执行反馈证据保留；不覆盖旧报告 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-010 limited-window `PASS` 历史结论 | CR-012 strict readiness audit 新口径 | 原文保留 + 文档声明修正 | CR-010 说明历史发布曾完成；CR-012 要求按 as-of PIT、dataset-specific `available_at` 和 claim boundary 复验。 |
| 旧 `index_members.trade_date` 每日覆盖审计 | `snapshot_asof` / `daily_materialized` 双模式 | CR 摘录保留 | snapshot 形态默认走 as-of 展开；daily materialized 模式只用于每日物化 membership。 |
| `index_weights` coverage pass | weights 与 as-of membership 对齐 | 原文保留 | `index_weights` 不再替代 `index_members` 证明 PIT universe。 |
| `trade_calendar` future available_at 误报 | calendar 专用 available_at policy | 原文保留 | `next_open` 写入 `available_at` 是 metadata semantics gap，不再记为通用 future false positive。 |
| `adj_factor` future available_at | strict PIT blocked claim | 原文保留 | ex-post 复权不能支撑 PIT 无泄漏复权声明。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | readiness audit、production strict claim、limited-window 声明 | true | 明确 limited-window 不能外推 2020-2024；strict pass 必须以实际 coverage 和 PIT 可见性为准。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | snapshot PIT as-of audit、daily materialized audit、report claim review | true | 新增 snapshot PIT as-of 审计与 daily materialized PIT 审计两个场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | CR012-S01..S04、HLD / LLD / verification | true | 回退到 `solution-design`；本轮按用户批准计划完成代码、测试和文档增量。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 外置 lake、provider、凭据、旧 `data/**` | false | 保持只读审计；默认 `lake_writes=0`、`provider_fetches=0`、`env_fallback_reads=0`、`legacy_data_reads=0`。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、readiness reports | true | 刷新 limited-window 声明；报告新增 `issue_category`、gap attribution 和 blocked claims。 |

## 回退决策

- 影响范围：readiness audit 脚本、定向测试、HLD 增量、README / USER-MANUAL limited-window 声明。
- 回退到阶段：`solution-design`。
- 需要重新确认的对象：
  - CR-012 变更单。
  - CR-012 HLD / DATA-LAKE HLD 增量。
  - CR012-S01..S04 LLD 批次边界。
  - `tests/test_data_lake_readiness_audit.py` 回归结果。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 修改数据审计口径和生产级 claim 边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 修改 available_at / PIT / claim 边界，安全边界保持只读。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 readiness audit 输出合同和报告字段。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须解释 snapshot as-of、daily materialized、metadata semantics 和 unsupported claim 的关系。 |
| 是否保持 fast-lane | false | 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR012-AUDIT-BATCH-A`
- 批次范围来源：CR-012 影响分析 / 用户提供实施计划
- 批次内 Story：
  - `CR012-S01-pit-asof-coverage-audit`
  - `CR012-S02-available-at-policy-audit`
  - `CR012-S03-daily-gap-attribution`
  - `CR012-S04-report-claims-doc-refresh`
- 批次人工确认稿：`checkpoints/CP5-CR012-AUDIT-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [x] 批次范围已在本 CR 中冻结
  - [x] 用户已在本轮明确要求按既定计划实现
  - [x] 只读安全边界已冻结
  - [x] 定向测试覆盖已补齐

## 拟拆 Story

| Story | 目标 | 已实现范围 |
|---|---|---|
| `CR012-S01` | `index_members` 支持 `snapshot_asof` 与 `daily_materialized` 审计模式 | `AuditConfig.index_members_audit_mode`、CLI 参数、as-of 展开、daily materialized mismatch 分类。 |
| `CR012-S02` | dataset-specific `available_at` policy | trade_calendar next_open 语义 gap、真实 future 仍 fail、adj_factor strict PIT blocked claim。 |
| `CR012-S03` | prices / adj_factor / tradability / lifecycle 缺口归因 | `missing_price_count`、`untradable_or_suspended_count`、`not_listed_or_delisted_count`、`denominator_excluded_count`。 |
| `CR012-S04` | 报告声明、unsupported register 与文档刷新 | `issue_category`、`blocked_claims`、summary / blocking gaps 文案、README / USER-MANUAL limited-window 声明。 |

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `codex` | 创建 CR 并登记影响 | 用户计划、limited-window 报告 | 本 CR | CR 已登记 | 修改审计脚本 |
| 2 | `codex` | 实现 readiness audit 修正 | CR、现有脚本和测试 | `experiments/run_data_lake_readiness_audit.py`、测试 | py_compile / pytest | 刷新文档 |
| 3 | `codex` | 刷新 HLD 与用户文档 | CR、验证结果 | HLD / README / USER-MANUAL 增量 | 文档自检 | 等待用户终验 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：若生效，人工审查稿必须标注 `approval_source=user-preauthorized`

## 处理结论

- 审批结论：`approved`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 人工审批通过（高风险，按用户提供计划直接实施）

后续门控：

- 已完成代码实现和定向测试。
- 2026-05-24 补充反馈显示仍有 7 个 `blocked_required_missing`，根因已拆分为审计口径修正后暴露的 current truth 缺口与 metadata 语义缺口。
- 本轮用户已要求“制定修复计划，并完成问题修复”；因此 CR-012 追加真实 current truth 修复阶段，需显式授权写 `/mnt/ugreen-data-lake` catalog/canonical，并读取 Tushare provider 补齐缺口。
- 终验建议以 limited-window readiness audit 复跑结果、定向测试结果和本 CR 修复记录后关闭。

## 2026-05-24 补充修复计划

### 阻断根因拆分

| Dataset | 当前阻断 | 根因判定 | 修复动作 |
|---|---|---|---|
| `trade_calendar` | `calendar_available_at_rule_semantics_gap` | normalization 将交易日历可知时间和 next-open 语义混用，已发布 current truth 的 `available_at_rule=date_only_next_open` 不满足 CR-012 语义。 | 修改 normalizer；重写 current truth 中 `available_at=<trade_date>T00:00:00+08:00`、`available_at_rule=calendar_known` 并更新 catalog。 |
| `adj_factor` | `future_available_at;adj_factor_pit_available_at_blocked_claim;coverage_gap` | 已发布 rows 默认使用 run 完成时间作为 `available_at`，导致全量 future；另有 20 个后续调入成分缺复权因子。 | 修改 normalizer；重写既有 Tushare `adj_factor` 派生 `available_at=<trade_date>T16:00:00+08:00`；联网补 20 个缺失成分。 |
| `index_members` | `coverage_gap` | Tushare snapshot current truth 最早为 `2025-04-30`，目标窗口 `2025-02-11..2025-04-29` 缺 as-of 成分。 | 使用已发布 JQData `index_weights` v2 `2025-02-11` 快照派生 `index_members` 补齐前段 as-of 窗口，并保留 `derived_from=index_weight`。 |
| `stock_basic` | `coverage_gap` | `601989.SH` 是 PIT membership 成分但不在现有 Tushare active `stock_basic` 快照中，生命周期 gate 无法判定退市边界。 | 联网抓取 Tushare `stock_basic(list_status=D)` 并合并退市生命周期行。 |
| `prices` | `coverage_gap` | 后续调入 HS300 的 20 个成分未被原 CR-010 prices 拉取覆盖；另有停牌/退市类缺口应由 tradability/lifecycle gate 排除。 | 联网抓取这 20 个成分的 `prices.daily`；退市/不可交易缺口由更新后的 `stock_basic` 与 `trade_status` 归因排除。 |
| `trade_status` | `coverage_gap` | 剩余缺口集中在 `601989.SH` 退市后日期；当前 stock lifecycle 缺失导致不能 denominator exclude。 | 优先通过 `stock_basic` 退市生命周期修复；复验若仍缺，再合并已有 JQData W3 rows。 |
| `prices_limit` | `coverage_gap` | 与 `trade_status` 相同，集中在 `601989.SH` 退市后日期。 | 优先通过 `stock_basic` 退市生命周期修复；复验若仍缺，再合并已有 JQData W3 rows。 |

### 执行计划

| 顺序 | 动作 | 工具 / 输出 | 权限 |
|---|---|---|---|
| 1 | 生成修复计划 | `scripts/cr012_limited_window_lake_repair.py` dry-run；输出 `reports/data_lake_readiness_limited_2025_2026/cr012_repair_plan.md` / `.json` | 只读 lake、写 repo report |
| 2 | 修复 normalizer | `market_data/normalization.py`，补充 `calendar_known` 与 Tushare `adj_factor` derived `available_at` | repo 写入 |
| 3 | 联网补数 | Tushare `prices.daily` / `prices.adj_factor` 20 个成分，Tushare `stock_basic(list_status=D)` | 需用户授权读取凭据环境变量、访问 provider、写真实 lake raw/manifest/canonical |
| 4 | 合并发布 | 生成 `cr012-limited-window-merged-*` canonical，更新 `catalog/catalog.json` 的 current truth 指针 | 需用户授权写真实 lake |
| 5 | 复验 | 复跑 `tests/test_market_data_tushare_datasets.py`、`tests/test_data_lake_readiness_audit.py` 与 limited-window readiness audit | repo 写报告；lake 只读 |

### 已生成计划摘要

- `open_trade_dates=251`。
- 当前 `membership_pairs=58800`，缺 `2025-02-11..2025-04-29` 共 55 个 open trade dates 的 as-of membership。
- `stock_basic_missing_symbols=601989.SH`。
- 需要补 Tushare 日频数据的 20 个成分：`001391.SZ,002384.SZ,002600.SZ,002625.SZ,300251.SZ,300476.SZ,300803.SZ,300866.SZ,301236.SZ,302132.SZ,600522.SH,600930.SH,601018.SH,601058.SH,601077.SH,601298.SH,601456.SH,601825.SH,603893.SH,688047.SH`。
- 已确认 `source_interface_matrix.csv` 中 `source_status=disabled` 是 provider 调用开关状态，不表示 current truth 不可读；本修复将显式启用真实 Tushare 读取。

## 2026-05-24 修复执行结果

### 执行批次

| 批次 | fetch_run_id | merged_run_id | provider fetch | catalog updates | 结果 |
|---|---|---|---:|---|---|
| 第一轮 | `cr012-limited-window-fetch-20260524T152036Z` | `cr012-limited-window-merged-20260524T152036Z` | 41 | `prices,adj_factor,trade_calendar,index_members,stock_basic` | 修复 `trade_calendar`、`index_members`、`stock_basic` 和 20 个调入成分；复验后剩余 4 个 coverage 阻断。 |
| 第二轮 | `cr012-limited-window-fetch-20260524T152331Z` | `cr012-limited-window-merged-20260524T152331Z` | 7 | `prices,adj_factor,trade_calendar,index_members,stock_basic,trade_status,prices_limit` | 补齐 `600837.SH` 前段、`601989.SH` 退市边界与 W3 缺口；复验通过。 |

### current truth 指针

最终 catalog current truth 指向：

| Dataset | canonical output |
|---|---|
| `prices` | `canonical/prices/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-prices.parquet` |
| `adj_factor` | `canonical/adj_factor/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-adj_factor.parquet` |
| `trade_calendar` | `canonical/trade_calendar/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-trade_calendar.parquet` |
| `index_members` | `canonical/index_members/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-index_members.parquet` |
| `stock_basic` | `canonical/stock_basic/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-stock_basic.parquet` |
| `trade_status` | `canonical/trade_status/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-trade_status.parquet` |
| `prices_limit` | `canonical/prices_limit/1.0/run_id=cr012-limited-window-merged-20260524T152331Z/part-cr012-prices_limit.parquet` |

### 最终复验

- `uv run --python 3.11 python -m py_compile market_data/normalization.py scripts/cr012_limited_window_lake_repair.py experiments/run_data_lake_readiness_audit.py tests/test_market_data_tushare_datasets.py tests/test_data_lake_readiness_audit.py`：PASS。
- `uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py tests/test_data_lake_readiness_audit.py`：PASS，`24 passed in 0.93s`。
- `uv run --python 3.11 python experiments/run_data_lake_readiness_audit.py --lake-root /mnt/ugreen-data-lake --start-date 2025-02-11 --end-date 2026-02-18 --output-dir reports/data_lake_readiness_limited_2025_2026 --max-workers 1`：PASS。
- 最终 readiness summary：`overall_status=production_strict_target_window_pass`，`available_for_target_window=10`，`blocking_count=0`。
- 审计复跑安全计数：`lake_writes=0`、`provider_fetches=0`、`legacy_data_reads=0`、`env_fallback_reads=0`。
- 声明边界：正式 10 dataset 在 `2025-02-11..2026-02-18` 目标窗口通过；该结论仍不得外推到 `2020-01-01..2024-12-31`；真实 VWAP claim 仍按 `execution_price_audit.csv` 保持 `required_missing`，不得声明真实 VWAP 可用。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 报告 | `reports/data_lake_readiness_limited_2025_2026/readiness_summary.md` | CR-012 触发证据；显示旧审计下 5 available / 5 blocked。 |
| 报告 | `reports/data_lake_readiness_limited_2025_2026/readiness_matrix.csv` | 旧口径下 `index_members`、`trade_calendar`、`adj_factor` 等问题来源。 |
| 代码 | `experiments/run_data_lake_readiness_audit.py` | 本 CR 主要实现文件。 |
| 测试 | `tests/test_data_lake_readiness_audit.py` | 本 CR 回归测试。 |
