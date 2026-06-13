---
cr_id: "CR-042"
status: "closed-current-delivery"
impact_level: "medium"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "新增 broker-neutral adapter 接口合同，属于外部接口边界抽象，保持 standard。"
rollback_to: "CR041 closed-current-delivery"
approval_result: "implemented-local-verification-pass"
created_at: "2026-06-11T00:00:00+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-06-11T00:00:00+08:00"
source: "cp8-follow-up"
linked_issue: ""
parent_cr: "CR-041"
source_checkpoint: "process/checkpoints/CP8-CR041-DELIVERY-READINESS.md"
source_decision_id: "USER-20260611-START-CR042"
follow_up_type: "CR"
risk_class: "medium"
owner: "meta-po/meta-dev-inline"
revisit_condition: "CR043 Goldminer adapter Spike 启动前复核官方接口和账号权限。"
acceptance_criteria: "BrokerAdapter / PaperBrokerAdapter / capabilities / cash-position-order-fill / error normalization 合同具备测试覆盖；Goldminer 仅 stub；不接真实 broker、不读取凭据。"
close_condition: "CR042 fixture tests PASS，静态导入边界 PASS，并保留不授权声明。"
cr_index_path: "process/changes/CR-INDEX.yaml"
---

## 变更描述

启动 CR042 Broker-Neutral Adapter Contract。目标是在 CR041 API-less paper simulation runner 已关闭后，新增一层 broker-neutral adapter 合同，使上层策略与具体 broker 接口解耦；当前只实现 `PaperBrokerAdapter` fixture 和 `GoldminerStubBrokerAdapter`，不连接真实 broker，不读取凭据，不安装或导入掘金 / QMT / 交易运行时，不提交或撤销真实订单。

## CP8 Follow-up 来源

| 字段 | 内容 |
|---|---|
| 父级 CR | `CR-041` |
| 来源检查点 | `process/checkpoints/CP8-CR041-DELIVERY-READINESS.md` |
| 来源决策 ID | `USER-20260611-START-CR042` |
| follow-up 类型 | `CR` |
| 风险等级 | `medium` |
| owner | `meta-po/meta-dev-inline` |
| 重访条件 | CR043 Goldminer adapter Spike 启动前复核官方接口、SDK、账号权限、凭据边界和运行授权。 |
| 验收标准 | PaperBrokerAdapter 合同和 fixture PASS；Goldminer 仅 stub；不接真实 broker、不读取凭据。 |
| 关闭条件 | CR042 代码、测试、静态导入边界和不授权声明通过。 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 原文档更新 | 保留 Track C 原候选行，状态从 planned 转 active / closed 时追加路径和门控 | 本 CR 摘录 | approved |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR041 关闭态，新增 / 更新 CR042 索引 | N/A | approved |
| `process/STATE.md` | 原文档更新 | 保留 CR041 delivered 基线，记录 CR042 active / close 状态 | N/A | approved |
| `docs/product/USE-CASES.md` | 不变 | 既有场景基线不变 | 不适用 | approved |
| `docs/product/REQUIREMENTS.md` | 不变 | 既有需求基线不变 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR041 `paper_order_intent_v1` / `paper_fill_v1` / ledger artifacts | CR042 `broker_order_request_v1` / `broker_fill_event_v1` / `broker_adapter_result_v1` | CR041 artifacts 原样保留 | CR042 adapter 只做归一化映射，不改变 CR041 runner 默认输出。 |
| CR040 Track C broker adapter 候选 | CR042 正式合同 | 台账保留候选来源 | CR042 是候选转正式实现，不代表 CR043 / CR044 自动启动。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md` | false | 不改需求基线；CR042 只承接 follow-up 候选。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | CR041 fixture / 新 CR042 fixture tests | true | 新增 broker adapter contract tests，不改 CR041 测试语义。 |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` / `CR-INDEX.yaml` / `STATE.md` | true | CR042 从 planned 候选转正式实现；CR043 / CR044 仍后置。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | broker / credential / account / order boundary | false | 只实现 API-less fixture/stub；显式阻断 sensitive fields、非零 forbidden counters、非 raw execution policy。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `engine/broker_adapter.py` / `tests/test_cr042_broker_adapter_contract.py` | true | 新增代码和测试；局部回归 CR041 + CR042。 |

## 回退决策

- 影响范围：局部
- 回退到阶段：`CR041 closed-current-delivery`
- 需要重新确认的对象：若 CR042 合同扩大到真实 broker、掘金 SDK、账户查询、下单、撤单、凭据读取或 simulation/live，则必须停止本 CR，转 CR043 / CR044 或新 CR 重新门控。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 新增 adapter 接口合同。 |
| 修改架构、权限、安全边界或平台安装路径 | false | 不扩大权限；安全边界保持不授权。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 新增 broker-neutral interface contract。 |
| 需要 HLD / LLD 才能解释影响 | true | 用本 CR 记录合同和回退边界。 |
| 是否保持 fast-lane | false | standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：waived
- batch_id：`CR-042-LLD-BATCH`
- 豁免理由：用户直接要求“分析和实现 CR042”，且实现范围收敛为单一新增离线合同模块、单一测试文件和本 CR 文档；不改变真实 broker 权限、不改变 CR041 runner 默认路径。
- 开发启动条件：
  - [x] CR041 closed-current-delivery 已确认
  - [x] CR042 不授权真实 broker / 凭据 / 下单 / 撤单 / 查询账户
  - [x] 实现范围限于 fixture/stub 合同

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 候选 CR 冲突预检与正式 CR 创建 | CR019 Track C / STATE / CR041 CP8 | 本 CR | CR041 closed、无 active formal CR | 实施最小合同 |
| 2 | `meta-dev-inline` | 实现 broker-neutral adapter fixture/stub | CR041 paper simulation artifacts | `engine/broker_adapter.py` / tests | 不接真实 broker | 局部验证 |
| 3 | `meta-po` | 收敛结果 | 测试结果 / diff | final summary | 用户本轮要求实现 | 等待后续 CR043 / CR044 独立启动 |

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
| CR-043 | Goldminer / 掘金量化 Adapter Spike | planned-spike | Spike | 4 | N/A | blocked_by=CR042 completion | not-started | 需要官方文档、SDK、账号权限和用户授权 | CR042 关闭后独立启动 |
| CR-044 | Goldminer Simulation Admission | planned | CR | 5 | N/A | blocked_by=CR043 PASS | not-started | 必须等待 CR043 PASS 和逐 run 授权 | CR043 后独立决定 |

## 处理结论

- 审批结论：`implemented-local-verification-pass`
- [ ] 自动批准（低风险）
- [x] 已由用户请求确认（中风险）：用户本轮已明确要求分析并实现 CR042，范围限于 fixture/stub 合同。
- [x] 无需高风险人工审批（高风险未命中）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| Follow-up | CR019 Track C CR-042 row | 候选项来源。 |
| Parent CR | CR-041 | API-less Paper Simulation Runner。 |
| Code | `engine/broker_adapter.py` | 新增 broker-neutral adapter 合同。 |
| Test | `tests/test_cr042_broker_adapter_contract.py` | 新增 fixture/stub 合同测试。 |

## 不授权声明

CR042 不授权安装、登录、连接、查询真实账户、读取凭据、读取 token、提交订单、撤单、真实 broker 调用、掘金 / QMT / XtQuant 调用、provider fetch、lake write、catalog publish、simulation/live 或任何交易运行。`approve` 或代码测试通过也不改变上述不授权范围。
