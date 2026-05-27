---
cr_id: "CR-011"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "补齐真实 benchmark、PIT 股票池、可交易性、执行价、行业市值、容量成本等研究数据会修改数据契约、实验消费边界和验证矩阵，命中外部接口、数据层和多 Story 依赖。"
rollback_to: "solution-design"
approval_result: "approved"
created_at: "2026-05-23T19:51:02+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-23T19:56:45+08:00"
closed_by: "user"
closed_at: "2026-05-24T17:41:32+08:00"
closure_checkpoint: "checkpoints/CP8-CR011-DELIVERY-READINESS.md"
source: "user"
linked_issue: ""
---

# CR-011 因子研究生产级数据补齐

## 变更描述

基于实验 14-21 的阶段性结论，补齐当前因子研究链路中仍缺失的关键数据与交易约束，使后续实验可以从“固定快照 + 代理 benchmark + close 执行价”的探索结论，升级为可审计、可复现、可分层验证的生产级因子研究输入。

本 CR 不改变实验 17-21 已经形成的阶段性结论。既有结论继续限定为：

```text
在固定快照股票池和代理 benchmark 下，低波动 + 低 RSI + 小回撤 + 短期反转组合相对趋势/追涨因子更稳定。
```

本 CR 的目标是补齐使该结论能够进一步升级所需的数据能力：

- 真实 benchmark：真实 `hs300_index` 覆盖、口径确认、实验 17-21 消费。
- PIT 股票池：历史成分、权重、股票基础状态、上市退市状态。
- 可交易性：停牌、涨跌停、ST、无成交、上市天数、事件状态。
- 执行价：open/high/low/close/VWAP 或可审计的日频执行价代理。
- 复权与公司行动：`adj_factor`、复权链路、分红送转等异常价格解释。
- 行业 / 市值 / 风格：行业分类、市值 / 流通市值、Beta / 风格暴露、行业市值中性 IC。
- 流动性 / 容量 / 成本：成交额、换手、冲击成本、成本敏感性。
- 因子审计产物：完整 raw / directional / winsorized / zscore factor panel 落盘。
- 稳健性验证：rolling walk-forward、年度分层、市场状态分段、参数与成本敏感性。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有场景原文保留；追加“生产级因子研究数据补齐”场景，不替换实验 14-21 既有场景基线 | `## 修订记录` | approved |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有需求原文保留；新增数据补齐、真实交易约束、因子审计和稳健性验证需求 | `## 修订记录` | approved |
| `process/HLD.md` | 原文档更新 | CR-010 之前主 HLD 保留；追加 CR-011 与数据湖 / 研究消费层关系，不重写既有架构 | `## 修订记录` | approved |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | CR-010 companion HLD 保留；追加因子研究辅助数据补齐范围和 provider/readiness 策略 | `## 修订记录` | approved |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 既有 ADR 保留；追加 benchmark/PIT/tradability/factor-audit/capacity 决策 | `## 修订记录` | approved |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 状态不回滚；追加 CR011-S01..S08 | `## 修订记录` | approved |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave / CP 记录保留；追加 CR011 数据补齐 Wave 和依赖 | frontmatter / waves | approved |
| `process/TEST-STRATEGY.md` | 原文档更新 | 既有测试策略保留；追加数据补齐质量门、真实 smoke、实验回归和稳健性验证矩阵 | `## 修订记录` | approved |
| `reports/experiment_17_21/*` | 不变 | 作为 CR-011 触发背景和旧实验基线保留；后续新实验另行输出新目录或版本化报告 | 不适用 | approved |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 既有用户说明保留；补充生产级因子研究数据口径与限制说明 | `## 修订记录` | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| 实验 14 数据 / benchmark 口径审计 | CR011-S01 / S02 / S03 | 原文保留 | 实验 14 暴露的 proxy benchmark、fixed snapshot、可交易性缺口作为本 CR 的补齐输入。 |
| 实验 15 因子框架 | CR011-S07 / S08 | 原文保留 | 实验 15 的 factor panel schema 保留；CR-011 扩展为完整因子审计面板和生产级 metadata。 |
| 实验 16 动量有效性检验 | CR011-S08 | 原文保留 | 既有 IC / 分组收益逻辑保留；新增 rolling / 年度 / 市场状态分层验证。 |
| 实验 17-21 因子策略报告 | CR011-S01..S08 | 原文保留 | 当前结论作为 fixed-snapshot/proxy baseline 基线；补齐数据后输出新版研究报告，不覆盖旧报告。 |
| CR-008 research input contract | CR011-S07 / S08 | 原文保留 | 继续使用 `research_input_v1`、allowed/blocked claims；新增因子审计与中性化能力字段。 |
| CR-010 数据湖生产化能力 | CR011-S01..S06 | 原文保留 | CR-011 复用 CR-010 的数据湖、catalog、readiness、quality/report 能力，聚焦因子研究缺口补齐。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、research input contract、实验 17-21 结论口径 | true | 新增生产级因子研究数据补齐需求；旧实验结论限定条件不删除。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 实验 14-21、真实 benchmark、PIT universe、tradability、cost sensitivity | true | 新增真实 benchmark 对照、PIT / fixed 对比、可交易性门控、行业市值中性、rolling 验证场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `STORY-BACKLOG.md`、`DEVELOPMENT-PLAN.yaml`、CR011-S01..S08 | true | 进入 standard 流程；先完成 HLD/ADR/Story Plan，再按批次 LLD 和 CP5 统一确认后实施。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 真实数据源、外置 lake、凭据、数据写入、旧 `data/**` 对比 | true | 默认不授权真实联网、真实抓取、真实 lake 写入、旧数据迁移/删除；真实执行需用户显式授权并禁止打印凭据。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、实验报告、测试策略、guardrail / readiness report | true | 新增回归集和报告产物；旧报告保留为 baseline，新报告单独输出并披露数据补齐状态。 |

## 回退决策

- 影响范围：全局数据层 + 因子研究消费层 + 实验 17-21 验证口径。
- 回退到阶段：`solution-design`。
- 需要重新确认的对象：
  - CR-011 HLD / ADR 增量。
  - CR011-S01..S08 Story Plan。
  - CR011 LLD 批次。
  - TEST-STRATEGY 数据补齐回归矩阵。
  - 真实数据执行授权边界。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 本 CR 涉及数据合同、实验输入、真实源、外置 lake 和多 Story 依赖。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 涉及真实联网 / 数据湖写入授权边界和数据 contract。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 benchmark、PIT、trade status、industry、market cap、factor panel 等接口。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先冻结数据契约和实验消费边界。 |
| 是否保持 fast-lane | false | 升级 / 保持 standard。 |

## LLD 设计批次门禁

> 本 CR 影响 Story、LLD、接口契约、文件所有权和实现设计。批次内全部 LLD 设计和 CP5 自动预检完成并统一人工确认前，不得实施任何 Story。

- 是否需要 LLD 设计批次：true
- batch_id：
  - `CR011-DATA-BATCH-A`
  - `CR011-RESEARCH-BATCH-B`
  - `CR011-VALIDATION-BATCH-C`
- 批次范围来源：CR-011 影响分析。
- 批次内 Story：
  - `CR011-S01-real-benchmark-and-policy-consumption`
  - `CR011-S02-pit-universe-and-stock-lifecycle-completion`
  - `CR011-S03-tradability-status-and-price-limit-gates`
  - `CR011-S04-ohlcv-vwap-clean-execution-feed`
  - `CR011-S05-adjustment-and-corporate-action-audit`
  - `CR011-S06-industry-market-cap-style-exposure-data`
  - `CR011-S07-liquidity-capacity-and-cost-sensitivity`
  - `CR011-S08-factor-panel-audit-and-robust-validation`
- 批次人工确认稿：
  - `checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md`
  - `checkpoints/CP5-CR011-RESEARCH-BATCH-B-LLD-BATCH.md`
  - `checkpoints/CP5-CR011-VALIDATION-BATCH-C-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 批次内全部 Story LLD 已输出
  - [ ] 批次内全部 Story CP5 自动预检已通过
  - [ ] 批次 CP5 人工确认结论为 `approved`
  - [ ] 批次内每个 Story 的 `dev_gate` 已满足

### 拟拆 Story

| Story | 名称 | 目标 | 主要输入 / 输出 | 优先级 |
|---|---|---|---|---|
| `CR011-S01` | 真实 benchmark 与 policy 消费 | 补齐真实 `hs300_index` 覆盖、口径确认、实验 17-21 消费和 missing reason | `hs300_index`、benchmark policy、experiment 17-21 report metadata | P0 |
| `CR011-S02` | PIT 股票池与股票生命周期 | 补齐历史成分、权重、上市退市、股票状态，支持 as-of universe | `index_members`、`index_weights`、`stock_basic`、as-of gate | P0 |
| `CR011-S03` | 可交易性与涨跌停门控 | 将停牌、涨跌停、ST、无成交、上市天数纳入研究和回测门控 | `trade_status`、`prices_limit`、events、portfolio gate | P0 |
| `CR011-S04` | OHLCV / VWAP 干净执行 feed | 提供 open/high/low/close/VWAP 或明确 close proxy 降级合同 | OHLCV/VWAP clean feed、Backtrader/vector path | P1 |
| `CR011-S05` | 复权与公司行动审计 | 补齐 adj_factor 链路和公司行动异常解释 | `adj_factor`、dividend/split events、adjustment audit | P1 |
| `CR011-S06` | 行业 / 市值 / 风格暴露 | 支持行业中性、市值中性和风格暴露分析 | industry classification、market cap、float cap、beta/style | P1 |
| `CR011-S07` | 流动性 / 容量 / 成本敏感性 | 将换手、成交额、冲击成本、成本敏感性纳入策略验收 | amount/volume/liquidity、capacity model、cost grid | P1 |
| `CR011-S08` | 因子审计面板与稳健性验证 | 落盘完整 factor panel，增加 rolling / 年度 / 市场状态分段验证 | factor_panel_full、rolling IC、annual reports、segment reports | P1 |

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记 | 用户请求、实验 14-21 缺口总结 | 本 CR、STATE 更新 | CR 已登记 | 等待用户审批 / 设计分派 |
| 2 | `meta-se` | 输出 HLD / ADR / Story Plan 增量 | CR、CR-008、CR-010、实验 17-21 报告 | HLD/ADR/Backlog/Plan 更新 | CP3/CP4 | 进入 LLD 批次 |
| 3 | `meta-dev` | 输出 LLD 并实施数据/实验能力 | CP5 approved、Story 卡片、数据合同 | 代码、测试、报告、CP6 | CP6 | 交 QA |
| 4 | `meta-qa` | 验证数据补齐和实验回归 | CP6、TEST-STRATEGY、真实执行授权 | CP7、真实 smoke、回归报告 | CP7 / 授权 | 交 doc |
| 5 | `meta-doc` | 刷新用户文档和研究限制说明 | 已验证实现、报告产物 | README / USER-MANUAL / 报告说明 | 文档自检 | 交 meta-po |
| 6 | `meta-po` | 收敛终验 | 下游结果、CR、检查点 | CP8 审查稿、CR 关闭建议 | 等待用户确认 | 关闭 CR 或回退 |

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
- [x] 人工审批通过（高风险）

审批证据：

- 审批人：user
- 审批时间：2026-05-23T19:56:45+08:00
- 审批原文：`@meta-po 请组织分析和实现process/changes/CR-011-FACTOR-RESEARCH-DATA-COMPLETION-2026-05-23.md`

后续门控：

- CR-011 已回退到 `solution-design` 并完成 HLD / ADR / Story Plan 增量。
- CP3 / CP4 已通过，CR011 三个 LLD 批次 CP5 均已 approved。
- CR011-S01..S08 均已完成 CP6 / CP7 并收敛为 `verified`。
- README / USER-MANUAL / TEST-STRATEGY 文档刷新已完成；CP8 自动预检 PASS；用户已通过 `checkpoints/CP8-CR011-DELIVERY-READINESS.md` 人工终验 `approve`，CR-011 已关闭。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| CR | `CR-008` | research input contract、因子辅助数据合同和 allowed/blocked claims 基线 |
| CR | `CR-010` | 数据湖生产化、真实源、readiness、quality/catalog 基线 |
| 报告 | `reports/experiment_17_21/factor_strategy_report.md` | 本 CR 的实验缺口来源 |
| 报告 | `reports/experiment_17_21/factor_retention_summary.csv` | 当前因子筛选结果基线 |
| 报告 | `reports/experiment_17_21/strategy_summary.csv` | 当前策略化回测结果基线 |
| 代码 | `experiments/run_experiment_17_21_factor_suite.py` | 当前实验 17-21 实现入口 |
| 测试 | `tests/test_experiment_17_21_factor_suite.py` | 当前实验 17-21 测试基线 |
