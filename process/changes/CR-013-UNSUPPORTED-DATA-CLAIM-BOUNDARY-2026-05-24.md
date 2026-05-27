---
cr_id: "CR-013"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "不支持内容涉及 2020-2024 全历史生产级声明、真实 VWAP / 分钟执行价声明、unsupported data register 和用户文档边界，命中数据合同、研究声明和交付说明。"
rollback_to: "solution-design"
approval_result: "approved"
created_at: "2026-05-24T23:41:15+08:00"
created_by: "codex"
approved_by: "user"
approved_at: "2026-05-25T21:50:37+08:00"
closed_by: "user"
closed_at: "2026-05-25T23:58:21+08:00"
cp8_manual_status: "approved"
source: "run-exec-boundary-review"
approval_text: "@meta-po 组织分析和实现 process/changes/CR-013-UNSUPPORTED-DATA-CLAIM-BOUNDARY-2026-05-24.md"
linked_issue: ""
---

# CR-013 Unsupported Data 与 Claim Boundary 重建

## 变更描述

CR-012 已将 `2025-02-11..2026-02-18` limited-window 的 10 个正式 dataset 修复到 `production_strict_target_window_pass`，但边界复验明确显示该结论不能外推：

- `reports/data_lake_readiness_2020_2024/readiness_summary.md` 显示 `overall_status=research_limited_only`、`limited_window_only=10`、`blocking_count=10`。
- `reports/data_lake_readiness_2020_2024/readiness_matrix.csv` 显示 10 个正式 dataset 均为 `limited_window_only`，核心阻断为 `target_window_not_covered`，部分 dataset 还存在 `coverage_denominator_empty`。
- `reports/data_lake_readiness_2020_2024/data_validity_assessment.md` 明确：CR-012 limited-window 修复有效，但 `2020-01-01..2024-12-31` 仍需单独补齐 current truth 并复验。
- `reports/data_lake_readiness_2020_2024/execution_price_audit.csv` 显示 execution feed 仍为 `required_missing`，`missing_ohlcv_columns=volume;amount`，`true_vwap_available_count=0`，blocked claims 为 `real_vwap_execution;vwap_fill_claim`。
- `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` 仍将行业 / 市值 / 风格、capacity inputs、完整公司行动、非 HS300 benchmark、分钟 / 逐笔 / 盘口 / 撮合、microstructure impact cost、真实 VWAP 执行价列为 research-only、unsupported 或 contract-supported-but-unavailable。

本 CR 将上述“不支持内容”从 CR-012 limited-window pass 中独立拆出，形成正式的声明边界与后续整改入口。当前只登记变更、影响、证据和待批准 Story；不执行真实补数、不写真实 lake、不联网抓取 provider、不读取凭据、不把 limited-window 结论升级为 2020-2024 生产级可用。

## 支持 / 不支持边界

| 对象 | 当前状态 | 可声明内容 | 禁止声明内容 | 证据 |
|---|---|---|---|---|
| `2025-02-11..2026-02-18` limited-window 10 dataset | supported | 该目标窗口内 10 个正式 dataset 已通过 CR-012 新口径 readiness audit。 | 不得外推到其他年份或全历史。 | `reports/data_lake_readiness_limited_2025_2026/readiness_summary.md` |
| `2020-01-01..2024-12-31` 全历史生产级 dataset | unsupported | 当前仅可声明尚未通过生产级 readiness audit。 | 不得声明 2020-2024 全历史生产级可用、可复现实盘级回测或全历史 PIT current truth 完整。 | `reports/data_lake_readiness_2020_2024/readiness_summary.md` |
| 真实 VWAP / VWAP fill | unsupported | 当前仅可声明 contract 已定义但数据不可用，claim 被 blocked。 | 不得声明真实 VWAP 执行价、VWAP fill、真实撮合执行价可用。 | `reports/data_lake_readiness_2020_2024/execution_price_audit.csv` |
| 分钟线 / 逐笔 / 盘口 / 撮合 | unsupported | 当前仅可声明未纳入正式 lake readiness。 | 不得声明分钟级执行价、tick、Level2 order book、订单撮合或真实交易执行模拟可用。 | `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` |
| 行业 / 市值 / 风格暴露 | research-contract-only | 可作为研究合同候选，不得作为已发布生产 dataset。 | 不得声明完整行业、市值、style exposure 因子数据已发布并通过 readiness。 | `unsupported_data_register.csv` |
| capacity / liquidity / impact cost inputs | unsupported | 仅可作为后续数据建设需求。 | 不得声明 ADV 约束、容量评估、冲击成本 microstructure 输入已可用。 | `unsupported_data_register.csv` |
| 完整公司行动 | unsupported | 当前不得支撑完整公司行动事件级声明。 | 不得声明完整分红、配股、拆并股、停复牌事件链已支持。 | `unsupported_data_register.csv` |
| 非 HS300 benchmark | unsupported | 当前只支持已声明的 HS300 benchmark 范围。 | 不得声明中证 500 / 中证 1000 / 全 A 等 benchmark 已通过同等 readiness。 | `unsupported_data_register.csv` |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 不变 | CR-013 只登记 unsupported 边界；不替换既有场景基线 | 不适用 | completed |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有研究需求保留；追加“不支持 claim 必须显式 blocked”的需求 | `## 修订记录` | completed |
| `process/HLD.md` | 原文档更新 | CR-011 / CR-012 设计保留；追加 unsupported claim boundary 与全历史补数边界 | `## 修订记录` | completed |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | CR-010 / CR-012 数据湖设计保留；追加 2020-2024 full-history 与 execution feed 未支持边界 | `## 修订记录` | completed |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | limited-window pass 作为窗口级结论保留；新增 2020-2024 与真实执行价 blocked 说明 | 相关状态章节 | completed |
| `reports/data_lake_readiness_2020_2024/*` | 不变 | 作为 CR-013 触发证据保留；不覆盖旧报告 | 不适用 | completed |
| `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` | 派生正式 CR-013 register | 现有 register 作为输入证据保留 | 不适用 | completed |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-012 limited-window pass | CR-013 unsupported full-history boundary | 原文保留 + 新 CR 单独声明 | CR-012 只证明 `2025-02-11..2026-02-18`；CR-013 记录该结论不得外推到 `2020-01-01..2024-12-31`。 |
| CR-011 execution feed 研究合同 | CR-013 real VWAP / minute execution blocked claim | 原文保留 + blocked claim 加固 | `prices` 缺 `volume/amount` 且无 `vwap_status=available`，真实 VWAP 与 VWAP fill 必须保持 blocked。 |
| `unsupported_data_register.csv` 临时登记 | CR-013 正式 unsupported register 管理入口 | 原文件保留为证据 | 将 research-only、unsupported、contract-supported-but-unavailable 明确纳入交付声明边界。 |
| 2020-2024 审计报告 | 后续 full-history remediation Story | 原报告保留 | 当前报告证明全历史尚未通过，后续若补数必须生成新 run 和新报告，不能覆盖旧证据。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | production strict readiness、unsupported claim、execution price claim | true | 新增“不支持内容必须 blocked，不得默认继承 limited-window pass”的要求；2020-2024 和真实 VWAP 均需单独满足数据与审计条件。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 2020-2024 full-history audit、execution price audit、unsupported register audit | true | 新增三个边界复验场景：全历史 dataset readiness、执行价 / VWAP claim、unsupported register 文档一致性。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | HLD / LLD / docs / report claim | true | 回退到 `solution-design`；批准后先刷新 HLD / DATA-LAKE HLD，再拆 Story 和 LLD，最后才允许实现或文档变更。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | provider fetch、真实 lake 写入、凭据读取、旧 `data/**` | true | 本 CR 当前不授权任何真实补数或 lake 写入；若后续要补 2020-2024 或接入分钟 / VWAP 数据，必须另行显式授权。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、readiness summary、unsupported register | true | 交付文档必须同步显示 supported / unsupported / blocked claim，避免把 limited-window pass 误读为全历史生产级可用。 |

## 回退决策

- 影响范围：需求声明、HLD / DATA-LAKE HLD、用户文档、unsupported register、readiness report claim 文案。
- 回退到阶段：`solution-design`。
- 需要重新确认的对象：
  - 本 CR 的支持 / 不支持边界表。
  - 全历史 `2020-01-01..2024-12-31` 是否仅登记 blocked，还是进入补数 Story。
  - execution feed 是否只保持 blocked claim，还是后续另启真实 VWAP / 分钟数据建设。
  - README / USER-MANUAL 是否立即刷新声明，或等待下一轮数据建设完成后刷新。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 本 CR 触及生产级数据可用性声明和真实执行价 claim。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 需要明确 provider / lake / 凭据权限未授权，并隔离 future backfill 权限。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 data lake current truth、execution feed、unsupported register 和报告输出合同。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须区分 limited-window pass、全历史 blocked、contract-supported-but-unavailable 和 unsupported。 |
| 是否保持 fast-lane | false | 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR013-CLAIM-BOUNDARY-BATCH-A`
- 批次范围来源：CR-013 影响分析 / 2020-2024 边界复验 / execution price audit / unsupported register
- 批次内候选 Story：
  - `CR013-S01-full-history-readiness-gap-register`
  - `CR013-S02-execution-vwap-claim-boundary`
  - `CR013-S03-unsupported-register-and-doc-refresh`
  - `CR013-S04-full-history-backfill-roadmap`
- 批次人工确认稿：`checkpoints/CP5-CR013-BATCH-A-LLD-BATCH.md`（approved）
- 开发启动条件：
  - [x] 用户批准本 CR。
  - [x] HLD / DATA-LAKE HLD 已按本 CR 刷新。
  - [x] 全部目标 Story 的 LLD 已完成并通过 CP5 批量确认。
  - [x] 本 CR 仅执行离线边界重建；未授权也未执行真实 provider 或 lake 写入。

## 拟拆 Story

| Story | 目标 | 范围 | 不包含 |
|---|---|---|---|
| `CR013-S01` | 建立 2020-2024 full-history readiness gap register | 固化 10 个 dataset 的 `limited_window_only` 阻断、target-window coverage 缺口、remediation 分类和复验入口 | 不补真实数据，不写 lake |
| `CR013-S02` | 加固 execution / VWAP claim boundary | 将 `real_vwap_execution`、`vwap_fill_claim`、分钟 / 逐笔 / 盘口 / 撮合执行价保持 blocked，并定义解除条件 | 不从 `amount/volume` 推导真实 VWAP，不构造伪分钟数据 |
| `CR013-S03` | 刷新 unsupported register 与用户文档 | README / USER-MANUAL / report summary 中明确 supported、research-only、unsupported、blocked claim | 不修改研究策略逻辑 |
| `CR013-S04` | 制定全历史补数路线图 | 若用户后续批准，拆分 2020-2024 10 dataset 补数、复验和发布计划 | 当前不执行 provider fetch，不读取凭据，不写 `/mnt/ugreen-data-lake` |

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `codex` | 创建 CR-013 并登记影响 | 用户边界复验反馈、2020-2024 报告、execution audit、unsupported register | 本 CR | CR 已创建 | 等待用户审批 |
| 2 | `meta-se` / `codex` | 刷新 HLD / DATA-LAKE HLD | 本 CR、现有 HLD | HLD 增量 | CP3 / CP5 前置 | 拆 Story |
| 3 | `meta-dev` / `codex` | 设计候选 Story LLD | HLD、Story backlog | LLD 批次 | CP5 人工确认 | 执行文档或代码修复 |
| 4 | `meta-qa` / `codex` | 复验 claim boundary | readiness reports、execution audit、docs | CP7 / report consistency | 无 false pass | 等待终验 |

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
- [ ] 待人工确认（高风险）
- [x] 人工审批通过
- CP8 终验结论：`approved`
- 关闭结论：`closed`
- 关闭时间：2026-05-25T23:58:21+08:00
- 关闭依据：
  - `process/checks/CP8-CR013-DELIVERY-READINESS.md` 结论 PASS。
  - `checkpoints/CP8-CR013-DELIVERY-READINESS.md` 用户人工终验 approved。
  - CR013-S01..S04 均完成 CP6 / CP7 并收敛为 `verified`。

后续门控：

- 本 CR 已按 standard 门控完成 HLD / Story Plan / 全量 LLD / CP5 / CP6 / CP7 / CP8。
- CR-013 关闭不授权读取 Tushare 凭据、不访问 provider、不写 `/mnt/ugreen-data-lake`、不读取旧 `data/**`。
- 任何 2020-2024 full-history pass 声明，仍必须在 10 个正式 dataset 全部 current truth 补齐并通过新审计后才能解除 blocked。
- 任何真实 VWAP / 分钟执行价 claim，仍必须有 `vwap` 且 `vwap_status=available`，并满足执行价审计；不得由 `amount/volume` 派生为真实 VWAP。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 报告 | `reports/data_lake_readiness_2020_2024/readiness_summary.md` | 2020-2024 full-history 仍为 `research_limited_only` 的主证据。 |
| 报告 | `reports/data_lake_readiness_2020_2024/readiness_matrix.csv` | 10 个正式 dataset 均为 `limited_window_only` 的明细证据。 |
| 报告 | `reports/data_lake_readiness_2020_2024/data_validity_assessment.md` | limited-window pass 与全历史 blocked 边界说明。 |
| 报告 | `reports/data_lake_readiness_2020_2024/execution_price_audit.csv` | execution feed / VWAP claim 仍 `required_missing` 的证据。 |
| 报告 | `reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv` | unsupported / research-only / contract-supported-but-unavailable 内容登记。 |
| 变更 | `process/changes/CR-012-LIMITED-WINDOW-READINESS-AUDIT-CORRECTION-2026-05-24.md` | 上游 limited-window readiness 修复 CR；CR-013 不修改其通过结论，只补充不可外推边界。 |
