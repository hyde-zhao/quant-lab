---
cr_id: CR-034
title: 第三章真实数据 readiness 与财务 PIT 审计
status: open
created_at: 2026-06-09
created_by: codex
owner: meta-po
source: user
change_type: add
impact_level: high
workflow_mode_before: fast-lane
workflow_mode_after_change: standard
fast_lane_upgrade_reason: "涉及真实 lake readiness、可能读取 .env 中 lake root、财务 PIT/as-of 审计和后续 2000-2019 全样本实证门禁，必须标准模式管理运行授权与人工决策。"
rollback_to: "68f79b6 Add long-term factor extension registry"
approval_result: pending
approved_by: ""
approved_at: ""
parent_cr: ""
source_checkpoint: ""
source_decision_id: "USER-20260609-CHAPTER3-CR"
follow_up_type: "chapter3-real-data-readiness"
risk_class: high
cr_index_path: "process/changes/CR-INDEX.yaml"
related_changes:
  - CR-014
  - CR-030
  - CR-032
  - CR-033
---

# CR-034 第三章真实数据 readiness 与财务 PIT 审计

## 变更描述

用户在完成第三章因子复刻、缺口整改、因子库边界整改和长期因子扩展入口后，追问“第三章描述的数据问题都解决好了吗”。当前结论是：代码层已经具备本地离线处理能力，但真实数据层尚未验证，不能声明第三章严格实证口径已经全部解决。

本 CR 的目标是把第三章数据问题从“离线工程能力覆盖”推进到“真实数据 readiness 可审计”。本 CR 创建本身不授权读取 `.env`、真实 lake、provider、publish、QMT、simulation 或 live；后续执行真实数据审计前必须经过明确运行授权。

## 当前基线

| 基线对象 | 当前状态 |
|---|---|
| CR-032 | 已实现第三章数据问题离线处理能力：复权优先、收益压缩、停牌置缺、股票池/可交易 mask、PIT 财务去重、分组检验。 |
| CR-033 | 已把通用因子定义、计算和统计从第三章模块拆出，并建立长期因子扩展入口。 |
| `process/research/chapter3_factor_replication/README.md` | 已明确剩余事项：真实 lake 字段、财务 revision/as-of、严格后复权、2000-2019 全样本实证、无风险利率。 |
| 验证状态 | 仅 fixture / 离线单元测试通过；未读真实 lake，未跑真实全样本。 |

## 目标

1. 审计真实数据 lake 是否满足第三章复刻所需字段和覆盖率。
2. 审计价格复权口径是否能严格支持第三章后复权收益。
3. 审计停牌、涨跌停、股票生命周期、ST/退市、科创板、负净资产、次新股字段是否足够构造第三章股票池和调仓可交易 mask。
4. 审计财务数据是否具备报告期、公告/可用时间、基准报告期、调整/更正、revision/as-of 语义。
5. 评估盈利、价值、投资因子所需 TTM / book equity / total assets 等字段的 PIT 可用性。
6. 审计 CAPM / 市场因子严格超额收益所需无风险利率数据是否存在。
7. 生成第三章真实数据 readiness 报告，明确 `PASS`、`PASS_WITH_LIMITATIONS` 或 `BLOCKED`。
8. 只有 readiness 通过或用户接受限制后，才允许另行启动 2000-01-01 至 2019-12-31 A 股全市场第三章实证复跑。

## Non-Goals

- 不在本 CR 创建阶段读取 `.env` 或任何凭据。
- 不在未授权情况下读取真实 lake。
- 不触发 provider fetch。
- 不写 lake。
- 不 catalog publish。
- 不 QMT、simulation、live。
- 不访问账户、订单或外部交易能力。
- 不在 readiness 未完成前声明“第三章真实复刻完成”。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/research/chapter3_factor_replication/README.md` | 原文档更新 | 保留 CR-032/CR-033 离线工程基线，追加 CR-034 真实数据 readiness 结果链接 | 新增 `## CR-034 真实数据 readiness 审计` | pending |
| `docs/CR030-FACTOR-RESEARCH-QUICKSTART.md` | 原文档更新 | 保留长期因子库入口，追加第三章真实数据 readiness 前置条件 | 相关章节追加说明 | pending |
| `process/changes/CR-034-CHAPTER3-REAL-DATA-READINESS-PIT-AUDIT-2026-06-09.md` | 新增 | N/A | 本文件 | pending |
| `process/research/chapter3_real_data_readiness/README.md` | 新增 | N/A | 新文档 | pending |
| `process/research/chapter3_real_data_readiness/READINESS-REPORT.md` | 新增 | N/A | 新文档 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-032 离线数据问题整改 | CR-034 真实数据 readiness 审计 | 原文保留 | CR-034 不重写离线实现，只验证真实数据是否满足实现输入合同。 |
| CR-033 因子库长期扩展入口 | CR-034 readiness runner / report | 原文保留 | CR-034 消费通用因子库和第三章适配层，不改变因子身份和长期扩展方式。 |
| 第三章 README 剩余事项 | CR-034 验证清单 | 原文保留并追加结果 | README 中“剩余需授权或真实数据接入事项”是本 CR 输入基线。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | 第三章真实数据 readiness 要求 | true | 新增 readiness 审计需求，不改变 CR032/CR033 已完成范围。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 第三章真实数据字段覆盖、PIT、复权、股票池、调仓可交易性 | true | 新增真实数据 readiness 场景和报告验收；fixture 测试不再足以关闭数据问题。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | 后续真实实证复跑依赖 readiness 结果 | true | 标准模式；先审计 readiness，再决定是否启动真实全样本复跑 CR/Story。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | `.env`、真实 lake、可能数据目录读取 | true | CR 创建不授权执行；运行前必须单独收集 runtime authorization。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | readiness report、第三章 README、CR030 快速手册 | true | 生成报告与 CP6/CP7 证据，回归通用因子和第三章适配层测试。 |

## 第三章数据问题审计清单

| ID | 问题 | readiness 判定要求 | 当前预期状态 |
|---|---|---|---|
| C3-RD-01 | 后复权价格 | 全样本存在 `back_adjusted_close` 或等价后复权字段，覆盖 2000-2019 研究范围 | 待审计 |
| C3-RD-02 | 收益压缩输入 | 可构造每日收益，能识别 1996-12-16 后 `+/-10%` 压缩规则适用范围 | 待审计 |
| C3-RD-03 | 停牌处理 | 存在停牌状态或可从交易状态可靠推断；beta/收益不被停牌 0 收益污染 | 待审计 |
| C3-RD-04 | 涨跌停 / 一字板 | 调仓日可识别一字涨停、一字跌停 | 待审计 |
| C3-RD-05 | 股票生命周期 | 存在上市日、退市日、上市状态、板块/交易所字段 | 待审计 |
| C3-RD-06 | ST / 风险警示 | 可按日期识别 ST / 风险警示状态，而不是只用当前状态 | 待审计 |
| C3-RD-07 | 科创板边界 | 可排除科创板；2000-2019 样本中应记录 N/A 或边界逻辑 | 待审计 |
| C3-RD-08 | 负净资产 | 财务 PIT 下可判断净资产为负 | 待审计 |
| C3-RD-09 | 财报 PIT | 有 `available_at/ann_date/publish_date`、`report_period/end_date`、调整/更正字段 | 待审计 |
| C3-RD-10 | TTM 构造 | 能构造或直接读取 ROE(TTM)、经营利润 TTM 等盈利字段 | 待审计 |
| C3-RD-11 | BM / book equity | 可 PIT 获取 book equity 并与市值匹配 | 待审计 |
| C3-RD-12 | 投资因子 | 可 PIT 获取 total assets / asset growth | 待审计 |
| C3-RD-13 | 换手率 | 可覆盖 21/252 日异常换手率窗口 | 待审计 |
| C3-RD-14 | 无风险利率 | 有 CAPM 超额收益所需无风险利率曲线，或明确限制 | 待审计 |
| C3-RD-15 | 月末交易日 | 交易日历覆盖研究区间并可识别月末调仓日 | 待审计 |

## 待人工决策项

| 决策 ID | 类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| D-CR034-01 | runtime_authorization | 是否允许读取 `.env` 中的 `MARKET_DATA_LAKE_ROOT` 并只读审计真实 lake？ | 暂不授权；先创建 CR 和审计计划，等待用户明确授权。 | 授权只读 `.env` + lake metadata，不 provider fetch、不写入。 | 未授权则只能停留在计划；授权后可生成真实 readiness 报告。 | 用户明确回复授权范围后进入执行。 |
| D-CR034-02 | risk_acceptance | 若真实 lake 只有 qfq/adjusted_close，没有严格后复权，是否允许 `PASS_WITH_LIMITATIONS`？ | 默认不接受严格复刻声明，仅允许 limited。 | 用户接受替代复权口径并在报告中标红限制。 | 影响第三章复刻可信度。 | 若后续补齐后复权字段，可升级为 PASS。 |
| D-CR034-03 | implementation | 财务 PIT 若缺 revision/as-of，是否先做字段 readiness 报告还是补数据？ | 先出 readiness 报告，不补数据。 | 另起数据补齐 CR。 | 补数据会涉及 provider/lake/publish 授权。 | readiness BLOCKED 后再决策。 |
| D-CR034-04 | follow_up_tracking | readiness 通过后是否启动 2000-2019 全样本实证复跑？ | 不在本 CR 自动启动，作为后续 CR 候选。 | 本 CR 后半段继续跑实证。 | 全样本复跑可能耗时并涉及真实 lake 访问。 | readiness PASS 后再人工确认。 |

## 回退决策

- 影响范围：局部，主要影响第三章真实数据 readiness 计划和审计产物。
- 回退到阶段：`68f79b6 Add long-term factor extension registry`。
- 需要重新确认的对象：无；本 CR 创建不会修改代码执行路径。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 后续可能涉及真实 lake metadata 和 `.env` lake root。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 引入 runtime authorization 决策和真实数据审计边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | false | 当前只创建 CR；后续实现再拆 Story。 |
| 需要 HLD / LLD 才能解释影响 | true | 真实数据 readiness runner / report 需要设计输入输出和失败路径。 |
| 是否保持 fast-lane | false | 升级为 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR034-LLD-BATCH`
- 批次范围来源：CR 影响分析
- 批次内 Story：
  - `CR034-S01-chapter3-real-data-readiness-scope-and-authorization`
  - `CR034-S02-readonly-lake-schema-coverage-audit`
  - `CR034-S03-financial-pit-readiness-audit`
  - `CR034-S04-readiness-report-and-follow-up-decision`
- 批次人工确认稿：`process/checkpoints/CP5-CR034-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 批次内全部 Story 设计证据已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 真实 lake 读取前已获得 runtime authorization。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | meta-po | 创建 CR034 并收集运行授权决策 | 用户请求、CR032/CR033、第三章 README | 本 CR、待决策项 | 用户确认是否授权只读真实数据审计 | 进入 LLD 批次或保持 open |
| 2 | meta-se/meta-dev | 设计 readiness runner 和报告格式 | 本 CR、第三章适配层、CR030 合同 | Story / LLD / 测试计划 | CP5 批次确认 | 实现只读审计 |
| 3 | meta-dev | 实现只读 readiness audit | LLD、授权范围 | 审计脚本/模块、fixture 测试 | CP6 | 交验证 |
| 4 | meta-qa | 执行 fixture + 授权范围内真实 readiness 验证 | 审计产物、lake metadata | CP7、READINESS-REPORT | 不触发未授权操作 | 交 meta-po |
| 5 | meta-po | 发起 CP8 人工决策 | CP7、readiness report、后续 CR 候选 | CP8 人工稿 | 用户 approve / 修改 / reject | 关闭或回修 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：N/A
- 授权原文：N/A
- 授权时间：N/A

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：待 CP8 或 readiness 结果生成
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`
- 当前说明：`process/changes/CR-INDEX.yaml` 在本 CR 创建前已有未提交改动；为避免混入无关状态，本次先创建正式 CR 文件，索引同步作为 CR034-S01 的第一项任务。

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR034-FU-01 | 2000-2019 第三章全样本真实实证复跑 | candidate | CR | 1 |  | CR-034 | readiness PASS / PASS_WITH_LIMITATIONS 后 | 未完成真实数据 readiness | 等待 CR034 readiness 结果 |
| CR034-FU-02 | 财务 PIT / revision 数据补齐 | candidate | CR | 1 |  | CR-034 | readiness BLOCKED 后 | 可能缺少 revision/as-of 或 TTM 字段 | 等待真实数据审计 |
| CR034-FU-03 | 无风险利率曲线接入 | candidate | CR | 2 |  | CR-034 | CAPM 严格复刻需要 | 当前未接入 | 等待 readiness 报告 |

## 处理结论

- 审批结论：pending
- [ ] 自动批准（低风险）
- [x] 待人工确认（中风险/高风险运行授权）
- [x] 待人工审批（真实 lake / `.env` 读取）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| CR | CR-030 | 多因子研究闭环和 FactorSpec/FactorRunSpec 合同。 |
| CR | CR-032 | 第三章数据问题离线工程整改。 |
| CR | CR-033 | 因子库边界和长期扩展入口整改。 |
| 文档 | `process/research/chapter3_factor_replication/README.md` | 第三章当前覆盖状态和剩余真实数据事项。 |
| 代码 | `engine/chapter3_factor_replication.py` | 第三章复刻适配层。 |
| 代码 | `engine/factor_library.py` / `engine/factor_calculators.py` / `engine/factor_statistics.py` | 通用因子定义、计算和统计。 |

## 当前状态

CR 已创建，尚未获得读取 `.env` 或真实 lake 的运行授权。下一步应先由 meta-po 发起 D-CR034-01 至 D-CR034-04 的人工决策，再进入 LLD 批次或只读审计实现。
