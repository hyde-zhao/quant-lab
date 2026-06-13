---
cr_id: "CR-043"
status: "closed-spike-complete"
impact_level: "medium"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "掘金 / Goldminer adapter 涉及外部平台接口、SDK、凭据边界、账户权限和后续仿真准入，必须保持 standard Spike。"
rollback_to: "CR042 closed-current-delivery"
approval_result: "approved-to-start-engineering-feasibility-spike"
boundary_decision_result: "cp2-cp3-approved-by-user"
spike_conclusion_recommendation: "NEEDS_ACCOUNT_PERMISSION"
cp8_review_status: "approved"
closed_at: "2026-06-11T08:56:11+08:00"
closed_by: "user"
closure_result: "NEEDS_ACCOUNT_PERMISSION"
created_at: "2026-06-11T07:35:00+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-11T07:35:00+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-042"
source_checkpoint: "process/checkpoints/CP8-CR041-DELIVERY-READINESS.md"
source_decision_id: "USER-20260611-START-CR043"
follow_up_type: "Spike"
risk_class: "medium"
owner: "meta-po"
feasibility_target: "engineering_fact_feasibility"
evidence_level_policy: "L0=local_contract_baseline; L1=official_public_docs_check; L2=isolated_sdk_static_check; L3=account_credential_check_not_authorized; L4=simulation_live_runtime_not_authorized"
authorized_evidence_levels: "L1 official public docs check; L2 isolated SDK static metadata/import/signature/docstring introspection"
non_authorized_levels: "credential_read; login; connect; account_query; submit_order; cancel_order; simulation; live; provider_fetch; lake_write; catalog_publish"
revisit_condition: "完成官方文档、SDK / gmtrade、账号权限、simulation account、query / order 边界、kill switch 和凭据处理边界核对后，决定是否启动 CR044。"
acceptance_criteria: "Spike 产出官方事实表、SDK 静态核对表、接口契约映射、风险清单、不可用项、授权边界和准入建议；不得做真实下单 / 撤单；不得记录凭据；不得把搜索摘要当作已验证合同。"
engineering_fact_acceptance_criteria: "官方公开资料来源可追溯；SDK 静态核对不需要账号或连接；接口符号、参数、权限前置条件、错误状态和 no-operation guard 能映射到 CR042 BrokerAdapter 合同；不可核对项必须标为 UNKNOWN / BLOCKED / NEEDS_ACCOUNT_PERMISSION。"
close_condition: "CR043 明确 PASS / PASS_WITH_UNKNOWN_RISKS / BLOCKED_BY_DOCS / NOT_RECOMMENDED / NEEDS_ACCOUNT_PERMISSION，并给出 CR044 是否可启动的推荐决策。"
cr044_admission_gate: "CR043 closed-spike-complete / NEEDS_ACCOUNT_PERMISSION 只表示可作为后续账号权限准入输入；不自动启动 CR044，不授权 simulation/live，不授权任何真实 broker 运行。"
engineering_feasibility_report_path: "process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md"
interface_mapping_matrix_path: "process/research/cr043_goldminer_adapter_spike/INTERFACE-MAPPING-MATRIX.md"
spike_conclusion_path: "process/research/cr043_goldminer_adapter_spike/SPIKE-CONCLUSION.md"
cp8_auto_check_path: "process/checks/CP8-CR043-DELIVERY-READINESS.md"
cp8_checkpoint_path: "process/checkpoints/CP8-CR043-DELIVERY-READINESS.md"
cr_index_path: "process/changes/CR-INDEX.yaml"
---

## 变更描述

启动 CR043 Goldminer / 掘金量化 Adapter Spike。目标是在 CR042 broker-neutral adapter 合同已关闭后，受控核对掘金官方接口、SDK / gmtrade、账号权限、simulation account、查询 / 下单边界、kill switch、错误归一化、凭据处理和后续 CR044 仿真准入条件。

本 CR 是 **Spike**，不是仿真交易准入，也不是真实 broker 运行授权。用户已要求达到“工程事实可行性”，因此当前授权范围升级为 L1 + L2：

- L1：允许核对掘金 / Goldminer / gmtrade / gm.api 官方公开文档、官方示例、官方 SDK 说明、官方下载页和公开包元数据。
- L2：允许在隔离临时环境下载 / 安装 / import SDK，仅做包结构、版本、依赖、函数签名、docstring 和静态 introspection 核对。

当前仍不授权读取凭据、登录、连接 broker、查询账户、下单、撤单、provider fetch、lake write、catalog publish、simulation/live 或任何交易运行。

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-042` |
| 来源检查点 | `process/checkpoints/CP8-CR041-DELIVERY-READINESS.md` |
| 来源决策 ID | `USER-20260611-START-CR043` |
| follow-up 类型 | `Spike` |
| 风险等级 | `medium` |
| owner | `meta-po` |
| 重访条件 | 官方接口、SDK / gmtrade、账号权限、仿真账户和凭据边界核对完成后，决定 CR044 是否可启动。 |
| 验收标准 | Spike 产出官方事实表、SDK 静态核对表、接口契约映射、风险清单、不可用项和准入建议；不连接真实 broker，不记录凭据，不下单 / 撤单。 |
| 关闭条件 | CR043 形成明确阶段结论：PASS / BLOCKED / NOT_RECOMMENDED / NEEDS_ACCOUNT_PERMISSION。 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 原文档更新 | 保留 Track C CR043 原候选行，状态从 planned-spike 经 active 转 closed | 本 CR 摘录 | approved |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR042 关闭态，记录 CR043 closed-spike-complete 索引 | N/A | approved |
| `process/STATE.md` | 原文档更新 | 保留 CR042 delivered 基线，记录 CR043 closed-spike-complete 状态 | N/A | approved |
| `docs/product/USE-CASES.md` | 不变 | 既有场景基线不变 | 不适用 | approved |
| `docs/product/REQUIREMENTS.md` | 不变 | 既有需求基线不变 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR042 `GoldminerStubBrokerAdapter` | CR043 official-docs / SDK / account-permission Spike | CR042 stub 原样保留 | CR043 只验证可行性和边界，不替换 CR042 stub 为真实 adapter。 |
| CR019 Track C CR043 候选 | CR043 正式 Spike | 台账保留候选来源 | CR043 由 planned-spike 转 active-cp2-intake。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` | false | 作为后续 Spike 启动，不改长期需求基线。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | CR043 Spike evidence / 后续 CR044 候选 | true | 后续需补充接口边界、失败路径、权限和 no-real-operation 场景。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | `STATE.md` / `CR-INDEX.yaml` / CR019 follow-up 台账 | true | CR043 转 active formal Spike；CR044 继续 blocked by CR043 PASS。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 官方文档、SDK、token、账号权限、simulation account | true | 当前授权 L1 官方公开资料核对和 L2 隔离 SDK 静态核对；任何登录、连接、凭据读取、查询账户、下单或撤单必须另行授权。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | Spike report / adapter contract proposal | true | 下一步产出官方事实表、SDK 静态核对表、Spike 结论、风险清单、接口候选和 CR044 准入建议。 |

## 工程事实证据等级

| 等级 | 当前状态 | 授权边界 | 证据路径 / 处理 |
|---|---|---|---|
| L0 local contract baseline | confirmed | 允许读取本地 CR042 合同和测试证据 | `engine/broker_adapter.py`、`tests/test_cr042_broker_adapter_contract.py` |
| L1 official public docs check | partial-confirmed | 允许核对官方公开文档、官方示例、官方下载页和公开包元数据 | `process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md` |
| L2 isolated SDK static check | partial-confirmed | 允许在隔离临时环境下载 / 安装 / import SDK，仅做包结构、版本、依赖、函数签名、docstring 和静态 introspection | `process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md` |
| L3 account / credential check | not-authorized | 不读取 token、账号、密码、session、cookie、密钥或终端配置 | 若后续需要，必须另起运行授权决策 |
| L4 simulation/live runtime | not-authorized | 不登录、不连接、不查询账户、不下单、不撤单、不启动 simulation/live | 只能由 CR044 或后续独立 CR 逐 run 授权 |

## 当前工程事实报告

| 产物 | 路径 | 当前结论 | 下一步 |
|---|---|---|---|
| Goldminer Adapter Spike 工程事实可行性报告 | `process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md` | 可继续推进到 CP2/CP3 边界确认，但不能进入 CR044 仿真准入或真实 adapter 实现。`gm` 在 Python 3.11 下可静态 import；`gmtrade` 在 Python 3.10 下可静态 import，但 Python 3.11 无匹配 wheel。 | 基于报告补 CP2/CP3 Decision Brief，明确主选 SDK、权限边界、接口映射矩阵和 CR044 go/no-go 条件。 |
| Goldminer Adapter 接口映射矩阵 | `process/research/cr043_goldminer_adapter_spike/INTERFACE-MAPPING-MATRIX.md` | 已将 CR042 `BrokerAdapter`、`BrokerCashSnapshot`、`BrokerPositionSnapshot`、`BrokerOrderRequest`、`BrokerFillEvent`、错误归一化和 no-operation guard 映射到 `gm` / `gmtrade` 静态候选。 | CP3 确认主选 SDK、fallback、权限边界和后续真实 adapter 是否另起 CR。 |
| Spike 结论建议 | `process/research/cr043_goldminer_adapter_spike/SPIKE-CONCLUSION.md` | 推荐 CR043 关闭结论为 `NEEDS_ACCOUNT_PERMISSION`。 | 等待 CP8 人工确认；approve 后关闭 CR043，不启动 CR044。 |

## CP2 / CP3 人工决策回填

| 决策 ID | 决策类型 | 用户决策 | 推荐方案 | 结果 |
|---|---|---|---|---|
| CP2-CR043-DQ-01 | scope | 同意 | CR043 继续推进到 CP3 边界确认。 | approved |
| CP2-CR043-DQ-02 | runtime_authorization | 同意 | L3 凭据 / 账户和 L4 simulation/live 继续不授权。 | approved |
| CP2-CR043-DQ-03 | follow_up_tracking | 同意 | CR044 不启动，等待 CR043 结论。 | approved |
| CP3-CR043-DQ-01 | architecture | 同意 | `gm` 作为 Python 3.11 主选候选，`gmtrade` 作为 Python 3.10 fallback。 | approved |
| CP3-CR043-DQ-02 | implementation | 同意 | CR043 不写真实 Goldminer adapter；真实 adapter 另起后续 CR / LLD / 实现 / 验证。 | approved |
| CP3-CR043-DQ-03 | security | 同意 | capability 可声明 SDK 静态支持候选，但必须保持 `not_authorization=true`、`real_broker_enabled=false`、`simulation_ready=false`、`live_ready=false`。 | approved |
| CP3-CR043-DQ-04 | risk_acceptance | 同意 | `gmtrade` Python 3.11 不可用标为技术选型风险，不阻断 CR043；若采用需 Python 3.10 隔离 runtime。 | approved |

| Checkpoint | 路径 | 结论 |
|---|---|---|
| CP2 自动预检 | `process/checks/CP2-CR043-REQUIREMENTS-BASELINE.md` | PASS |
| CP2 人工审查 | `process/checkpoints/CP2-CR043-REQUIREMENTS-BASELINE.md` | approved |
| CP3 自动预检 | `process/checks/CP3-CR043-HLD-CONSISTENCY.md` | PASS |
| CP3 人工审查 | `process/checkpoints/CP3-CR043-HLD-REVIEW.md` | approved |
| CP8 自动预检 | `process/checks/CP8-CR043-DELIVERY-READINESS.md` | PASS |
| CP8 人工审查 | `process/checkpoints/CP8-CR043-DELIVERY-READINESS.md` | approved |

## CP8 关闭建议

| 项 | 内容 |
|---|---|
| 推荐关闭结论 | `NEEDS_ACCOUNT_PERMISSION` |
| 推荐理由 | SDK 静态接口与 CR042 合同可映射，但资金 / 持仓 / 委托 / 成交字段、账号权限和仿真账户可用性仍需后续受控授权核对。 |
| 不推荐 `PASS` 的原因 | 当前未授权也未执行凭据、登录、连接、账户查询、下单、撤单或仿真运行。 |
| CR044 状态 | 不启动；保留为 follow-up planned。 |
| CP8 审查路径 | `process/checkpoints/CP8-CR043-DELIVERY-READINESS.md` |

## CP8 人工审查回填与关闭结论

| 项 | 内容 |
|---|---|
| 用户回复 | 同意 |
| 回填语义 | 按 `approve` 处理 |
| 回填时间 | 2026-06-11T08:56:11+08:00 |
| CR043 最终状态 | `closed-spike-complete` |
| 关闭结论 | `NEEDS_ACCOUNT_PERMISSION` |
| CR044 状态 | `planned` / `not-started`，不自动启动 |
| 不授权边界 | 不读取凭据、不登录、不连接、不查询账户、不下单、不撤单、不启动 simulation/live、不执行 provider fetch / lake write / catalog publish。 |

## 回退决策

- 影响范围：局部
- 回退到阶段：`CR042 closed-current-delivery`
- 需要重新确认的对象：
  - 若无法核对官方文档或 SDK 边界，CR043 结论应为 `BLOCKED` 或 `NEEDS_ACCOUNT_PERMISSION`。
  - SDK 安装 / import 只允许在隔离临时环境做静态核对；若需要登录终端、连接 broker、读取 token 或查询账户，必须先发起运行授权决策，不得在本 CR 静默执行。
  - 若需要仿真下单 / 撤单 / 对账，必须等待 CR044 独立启动和逐 run 授权。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及外部 broker 平台接口和后续运行授权边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 命中外部接口 / 权限 / 凭据边界。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 目标是 adapter 可行性和接口边界。 |
| 需要 HLD / LLD 才能解释影响 | true | Spike 需先形成边界和准入建议。 |
| 是否保持 fast-lane | false | standard Spike。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：false
- batch_id：`CR-043-SPIKE`
- 原因：当前只启动 Spike intake 和边界核对，不进入 adapter 实现；若 Spike 推荐实现真实 Goldminer adapter，必须在后续 CR 或 CR043 后续阶段补充设计证据和门禁。
- 开发启动条件：
  - [ ] 官方接口和 SDK 边界已核对
  - [ ] 隔离临时环境 SDK 静态核对已完成或写明不可用原因
  - [ ] 凭据、账号权限和 simulation account 边界已状态化
  - [ ] no-real-operation 静态边界已定义
  - [ ] 用户明确授权任何需要登录、连接或账号查询的动作

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | CR043 启动、冲突预检、状态同步 | CR019 Track C / CR042 closed | 本 CR / STATE / CR-INDEX / 台账更新 | 当前无 active formal CR | 进入 Spike intake |
| 2 | `meta-po` | CP2 / CP3 级别边界梳理 | 官方文档核对范围、用户授权范围 | Spike questions / Decision Brief | 不登录、不连接、不读取凭据 | 等待用户确认或授权文档核对范围 |
| 3 | `meta-se` | 形成 adapter Spike 方案和风险表 | CR042 BrokerAdapter 合同、官方资料、SDK 静态核对、权限边界 | 官方事实表、SDK 静态核对表、接口契约草案、风险清单、不可用项、CR044 准入建议 | 只做官方公开资料和隔离 SDK 静态核对 | 交回 meta-po |
| 4 | `meta-po` | 收敛 Spike 结论 | Spike 输出 | PASS / BLOCKED / NOT_RECOMMENDED / NEEDS_ACCOUNT_PERMISSION | 不自动启动 CR044 | 等待用户决定 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：N/A
- 自动通过条件：N/A
- 授权原文：N/A
- 授权时间：N/A
- 回填要求：N/A

## 后续事项台账

- 是否存在后续事项：true
- 台账路径：`process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`
- CR 索引路径：`process/changes/CR-INDEX.yaml`
- 一致性检查：`uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .`

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 相关 active CR / blocked_by / superseded_by | 当前门控 | 阻塞原因 | 下一步 |
|---|---|---|---|---:|---|---|---|---|---|
| CR-044 | Goldminer Simulation Admission | planned | CR | 5 | N/A | blocked_by=CR043 closed + explicit user start + per-run authorization | not-started | 必须等待用户明确启动和逐 run 授权 | CR043 已以 `NEEDS_ACCOUNT_PERMISSION` 关闭；后续需先做账号 / 仿真权限准入 |

## 处理结论

- 审批结论：`approved-to-start-engineering-feasibility-spike`
- [x] 用户已请求启动 CR043 Spike
- [x] 无 active formal CR 冲突
- [x] 当前授权 L1 官方公开资料核对和 L2 隔离 SDK 静态核对
- [x] 不授权真实 broker / 凭据 / 账户 / 下单 / 撤单 / simulation/live
- [x] 用户已同意 CP8，CR043 关闭为 `closed-spike-complete`，关闭结论 `NEEDS_ACCOUNT_PERMISSION`

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Follow-up | CR019 Track C CR-043 row | 候选项来源。 |
| Parent CR | CR-042 | Broker-Neutral Adapter Contract。 |
| Code baseline | `engine/broker_adapter.py` | CR042 `GoldminerStubBrokerAdapter` 仍为 stub。 |
| Spike evidence | `process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md` | L1 官方公开资料核对和 L2 隔离 SDK 静态核对报告。 |
| Interface mapping | `process/research/cr043_goldminer_adapter_spike/INTERFACE-MAPPING-MATRIX.md` | CR042 BrokerAdapter 到 `gm` / `gmtrade` 静态候选接口的映射矩阵。 |
| Spike conclusion | `process/research/cr043_goldminer_adapter_spike/SPIKE-CONCLUSION.md` | 推荐关闭结论 `NEEDS_ACCOUNT_PERMISSION`。 |
| Future CR | CR-044 | 只有 CR043 PASS 后才能决定是否启动。 |

## 不授权声明

CR043 当前授权 L1 官方公开资料核对和 L2 隔离 SDK 静态核对：允许核对官方公开文档、官方示例、官方 SDK 说明、官方下载页、公开包元数据，并允许在隔离临时环境下载 / 安装 / import SDK，仅做包结构、版本、依赖、函数签名、docstring 和静态 introspection。

CR043 当前仍不授权读取 `.env`、token、账号、密码、session、cookie、密钥或终端配置；不授权登录、连接、查询真实账户、提交订单、撤单、真实 broker 调用、provider fetch、lake write、catalog publish、simulation/live 或任何交易运行。
