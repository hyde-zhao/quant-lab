---
checkpoint_id: "CP5"
checkpoint_name: "CR-015 / CR-016 / CR-017 All Stories LLD Batch Review"
type: "batch_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-28T06:40:12+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-28T07:03:27+08:00"
auto_check_result:
  - "process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md"
  - "process/checks/CP5-CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR017-S03-qfq-hfq-derived-view-normalization-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR017-S04-reader-api-and-policy-gates-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR017-S05-validation-quality-parity-and-leakage-tests-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S01-qmt-environment-and-interface-spike-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S02-qmt-broker-adapter-contract-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S03-oms-order-state-machine-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S04-pretrade-risk-gate-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S05-broker-lake-schema-and-writer-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR015-S07-docs-and-foundation-runbook-boundary-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S01-simulation-account-order-enable-gate-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S02-reconciliation-service-and-reports-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S03-monitoring-heartbeat-and-kill-switch-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S04-simulation-live-runbook-and-approval-gates-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S05-live-readonly-and-small-live-admission-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S06-scale-up-and-research-maturity-gates-LLD-IMPLEMENTABILITY.md"
  - "process/checks/CP5-CR016-S07-docs-user-manual-and-incident-playbooks-LLD-IMPLEMENTABILITY.md"
target:
  phase: "story-planning"
  story_id: ""
  artifacts:
    - "process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD.md"
    - "process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD.md"
    - "process/stories/CR017-S03-qfq-hfq-derived-view-normalization-LLD.md"
    - "process/stories/CR017-S04-reader-api-and-policy-gates-LLD.md"
    - "process/stories/CR017-S05-validation-quality-parity-and-leakage-tests-LLD.md"
    - "process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md"
    - "process/stories/CR015-S01-qmt-environment-and-interface-spike-LLD.md"
    - "process/stories/CR015-S02-qmt-broker-adapter-contract-LLD.md"
    - "process/stories/CR015-S03-oms-order-state-machine-LLD.md"
    - "process/stories/CR015-S04-pretrade-risk-gate-LLD.md"
    - "process/stories/CR015-S05-broker-lake-schema-and-writer-LLD.md"
    - "process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD.md"
    - "process/stories/CR015-S07-docs-and-foundation-runbook-boundary-LLD.md"
    - "process/stories/CR016-S01-simulation-account-order-enable-gate-LLD.md"
    - "process/stories/CR016-S02-reconciliation-service-and-reports-LLD.md"
    - "process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch-LLD.md"
    - "process/stories/CR016-S04-simulation-live-runbook-and-approval-gates-LLD.md"
    - "process/stories/CR016-S05-live-readonly-and-small-live-admission-LLD.md"
    - "process/stories/CR016-S06-scale-up-and-research-maturity-gates-LLD.md"
    - "process/stories/CR016-S07-docs-user-manual-and-incident-playbooks-LLD.md"
---

# CP5 CR-015 / CR-016 / CR-017 全量 LLD 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | PASS | 0 | Story Plan 覆盖 20 个 Story、8 个 Wave、3 个 LLD 批次；DAG 无环，CP5 前实现保持阻断。 |
| `process/checks/CP5-CR017-S01..S06-*-LLD-IMPLEMENTABILITY.md` | PASS | 0 | CR017 6 个复权双视图 Story 的 LLD 均为 14 章节，`confirmed=false`，`implementation_allowed=false`。 |
| `process/checks/CP5-CR015-S01..S07-*-LLD-IMPLEMENTABILITY.md` | PASS | 0 | CR015 7 个 QMT foundation Story 的 LLD 均为 14 章节，只覆盖 shadow / dry-run / mock foundation。 |
| `process/checks/CP5-CR016-S01..S07-*-LLD-IMPLEMENTABILITY.md` | PASS | 0 | CR016 7 个 activation / runbook / gate Story 的 LLD 均为 14 章节；S05 / S06 标记 later-gated。 |

## Decision Brief

| 字段 | 内容 |
|---|---|
| 推荐决策 | `approve`：批准 CR-015 / CR-016 / CR-017 共 20 个 Story 的全量 LLD 与 Story 级 CP5 自动预检结果，允许进入 story-execution 的受控实现队列。 |
| 备选方案 | `修改: <具体修改点>`：退回指定 Story / LLD / 批次修改；`reject`：不接受本批 LLD，回退到 Story Plan 或 HLD 边界重新设计。 |
| 影响维度 | 用户价值、交易安全、复权研究可信度、实现复杂度、可验证性、维护成本、跨平台兼容、安全 / 权限、后续交付节奏。 |
| 优劣分析 | 推荐方案保留三批 LLD 全量覆盖，优点是 CR017 数据口径、CR015 foundation、CR016 activation 边界完整，后续可按 DAG 推进；代价是实现范围较大，需要严格按 Wave、文件所有权和真实操作授权边界推进。 |
| 风险与回退 | 若批准后发现 LLD 缺陷，可在对应 Story CP6 前回退到 LLD 修改并重跑 Story 级 CP5；若不批准，则不得进入实现。 |
| 用户需决策事项 | 是否批准 20 个 Story 的 LLD；是否接受 CP5 approve 只授权代码 / 文档 / 测试实现，不授权真实 QMT / 真实发单 / 真实抓取 / 真实写湖；是否接受 CR016-S05 / S06 纳入 LLD 但保持 later-gated。 |

## CP5 待决策项

| ID | 决策问题 | 推荐方案 | 备选方案 A | 备选方案 B | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|
| CP5-D1 | 是否批准 20 个 Story 的全量 LLD 进入 story-execution | 批准全部 20 个 Story LLD，进入受控实现队列 | 只批准 CR017 + CR015，暂缓 CR016 | 退回指定 Story 修改后重审 | 可按已确认 DAG 启动实现，减少上下文反复；实现仍受 CP6/CP7 和真实操作边界控制 | 不批准则无法实现；部分批准会使 CR016 activation 继续缺工程落点 |
| CP5-D2 | CP5 approve 后是否只授权离线 / mock / fixture / 文档实现，不授权真实 QMT 或真实数据操作 | 接受：代码、测试、文档可按 Story 实现；真实 QMT API、发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实写湖、publish 均继续为 0 | 只允许文档实现，不允许代码实现 | 提前授权真实 QMT / 写湖试运行 | 推荐方案能验证工程链路，同时保持真实资金和真实数据安全 | 只做文档会无法验证架构；提前真实操作会越过 CP6/CP7、run 授权和安全门控 |
| CP5-D3 | 是否接受 CR016-S05 / CR016-S06 纳入 LLD 全量确认，但实现与真实操作保持 later-gated | 接受纳入 LLD，保持 `live_readonly` / `small_live` / `scale_up` later-gated | 从本批移除 S05 / S06，另起 CR 或后续批次 | 直接允许 S05 / S06 与前序 Story 同步实现 | 先冻结边界，避免后续资金放大无设计依据；不会授权真实 live / scale_up | 移除会留下激活路径断点；直接同步实现会把资金风险前置 |
| CP5-D4 | 是否接受三批 LLD 批次与实现顺序：CR017 数据口径先行、CR015 foundation 次之、CR016 activation 后置 | 接受该顺序，按文件所有权和 runtime 依赖串行 / 分 Wave 推进 | 先实现 QMT foundation，再补 CR017 | 三批完全并行实现 | 推荐方案降低复权价误入交易和 activation 过早风险 | QMT 先行可能混用价格口径；完全并行会扩大共享文件冲突和安全审计成本 |

## CP5 方案优劣对比（详细）

### CP5-D1 是否批准 20 个 Story 的全量 LLD 进入 story-execution

| 方案 | 推荐度 | 优点 | 缺点 / 代价 | 适用条件 | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|
| 批准全部 20 个 Story LLD，进入受控实现队列 | 推荐 | CR017 复权双视图、CR015 QMT foundation、CR016 activation/runbook/gate 的边界一次性冻结；实现可按 DAG、Wave 和文件所有权推进；减少反复拆批导致的上下文漂移 | 实现面较大，需要严格执行 CP6/CP7、真实操作禁令和 later-gated 边界 | 接受当前 LLD 批次的职责边界和自动预检结果，希望尽快进入工程实现 | 可启动 story-execution，但只允许按已确认 LLD、DAG 和 CP6/CP7 推进；不等于授权真实 QMT 或真实写湖 | 不批准则无法进入实现；需要返回 Story Plan / LLD 修改，项目节奏后移 |
| 只批准 CR017 + CR015，暂缓 CR016 | 备选 A | 先完成数据口径和 QMT 基础层，短期风险更低；CR016 中模拟盘 / live 门控暂不进入工程实现 | activation、reconciliation、monitoring、runbook 的工程落点延后；CR016 后续可能受 CR017/CR015 实现细节反向影响，需要补改 LLD | 用户希望更保守，只先建设不会触达模拟盘 / live 的基础能力 | CR017/CR015 可先进入实现；CR016 保持 pending 或拆成后续批次 | CR016 相关模拟盘启用、对账、监控、kill switch 和 live 准入无法按本批推进 |
| 退回指定 Story / LLD 修改后重审 | 备选 B | 可以精确修正用户不接受的 Story、接口、测试或风险边界；保留审查质量 | 需要 meta-dev 修订对应 LLD，并重跑对应 Story CP5；若问题跨 Story，可能影响批次一致性 | 发现具体 LLD 条款不清楚、风险边界不足或实现文件冲突 | 被点名 Story 暂不进入实现；未受影响 Story 是否可先行需要用户额外明确 | 不指定修改项则无法执行返工；整体实现保持阻断 |

### CP5-D2 CP5 approve 后是否只授权离线 / mock / fixture / 文档实现

| 方案 | 推荐度 | 优点 | 缺点 / 代价 | 适用条件 | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|
| 只授权代码、测试、文档、fixture、mock、dry-run / shadow 实现；真实 QMT、真实发单、真实账户、真实 broker lake 写入、真实抓取、真实写湖、publish 均继续为 0 | 推荐 | 能验证接口、状态机、风险门、读写契约和文档闭环；不触达真实资金、真实账户、真实凭据和生产数据写入；符合 CP5 后先工程实现、CP6/CP7 后再逐级授权的门控 | 无法证明真实 QMT 环境、柜台返回、网络异常、真实账户字段和真实成交回报；后续仍需要单独真实连接 / 模拟盘授权 | 当前目标是实现 CR015/CR016/CR017 工程骨架和安全边界，而不是立即跑真实交易或真实数据写入 | 可安全进入实现；所有真实操作仍需后续明确授权和对应 runbook / gate | 若不接受，需要选择“文档-only”或“提前真实试运行”，否则 CP5 授权边界不清晰 |
| 只允许文档实现，不允许代码实现 | 备选 A | 运行时风险最低；适合用户只想先继续评审方案，不希望改动工程代码 | 无法验证 LLD 的接口可实现性、测试契约和模块集成；后续实现仍要重新恢复上下文 | 用户对当前 LLD 仍不够放心，但愿意先沉淀文档和 runbook | 只能更新设计 / 说明 / runbook；代码和测试仍阻断 | 项目不会产生可执行能力，CR015/CR016/CR017 的工程收益延后 |
| 提前授权真实 QMT / 真实写湖试运行 | 备选 B，不推荐 | 可以更早暴露真实 QMT API、账户字段、柜台返回、真实数据源写入等环境问题 | 越过 CP6/CP7、per-run authorization、kill switch、对账和回滚门控；存在真实资金、凭据、账户信息、生产数据污染风险；与当前 LLD 的安全边界冲突 | 只有在用户明确接受安全风险，并额外给出真实环境、账户、凭据、时间窗口和回滚方案时才可考虑 | 需要新建单独真实操作授权记录 / Story 或 CR，并先补安全边界 | 不推荐直接接受；如果用户要求真实操作，应拆成 later-gated 真实运行任务 |

### CP5-D3 是否接受 CR016-S05 / CR016-S06 纳入 LLD 全量确认，但实现与真实操作保持 later-gated

| 方案 | 推荐度 | 优点 | 缺点 / 代价 | 适用条件 | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|
| 纳入本批 LLD 确认，但保持 `live_readonly` / `small_live` / `scale_up` later-gated | 推荐 | 提前冻结 live-readonly、小资金实盘、扩容门槛、暂停 / 回退条件，避免未来资金放大时无设计依据；同时不授权真实 live 或规模放大 | LLD 中包含未来阶段内容，审查时必须清楚区分“设计确认”和“执行授权” | 用户希望现在把模拟盘到实盘的路径设计完整，但当前不进入真实资金操作 | S05/S06 的设计边界被确认；后续仍必须另行满足前置 Story、人工授权和运行门控 | 若不接受，live / scale-up 的后续准入标准会缺少当前批次的设计约束 |
| 从本批移除 S05 / S06，另起 CR 或后续批次 | 备选 A | 当前批次更轻，避免审查未来 live / scale-up 内容；短期实现范围更纯粹 | 后续从模拟盘走向 live 时要重新设计；CR016 激活路径出现断点；runbook 和 kill switch 的终局目标不够完整 | 用户明确当前只关心 shadow / simulation，不希望讨论任何 live 相关设计 | 本批只推进到 simulation / runbook 基础能力；S05/S06 后置 | 后续实盘准入、资金放大、降级和暂停规则需要重新走 CR / LLD / CP5 |
| 直接允许 S05 / S06 与前序 Story 同步实现并进入真实 live 准备 | 备选 B，不推荐 | live-readonly / small-live 能力更早成型，模拟盘到实盘路径更快 | 把资金风险、账户权限、对账失败、kill switch 误触发 / 失效等风险前置；依赖 CR017/CR015/CR016 前置 Story 验证结果，过早实现容易返工 | 仅适合用户明确要求快速实盘化，并愿意单独授权真实账户风险 | 需要额外真实操作授权、账户隔离、资金上限、人工审批和回滚演练 | 当前不推荐；默认不授权任何 live / small-live / scale-up 真实操作 |

### CP5-D4 是否接受三批 LLD 批次与实现顺序：CR017 数据口径先行、CR015 foundation 次之、CR016 activation 后置

| 方案 | 推荐度 | 优点 | 缺点 / 代价 | 适用条件 | 接受影响 | 不接受影响 |
|---|---|---|---|---|---|---|
| CR017 数据口径先行，CR015 QMT foundation 次之，CR016 activation 后置 | 推荐 | 先确保 raw/qfq/hfq/returns 与 QMT 原始成交价隔离，降低复权价误入交易的风险；先完成 adapter/OMS/risk/broker lake，再启用 simulation/live gate；符合从事实源到交易执行再到激活的依赖顺序 | activation 交付较晚；短期看不到完整模拟盘流程 | 用户接受以交易安全和数据口径正确性优先 | 实现按 DAG 分 Wave 推进；可并行的文件独立任务仍可并行，但不跨越依赖门 | 若不接受，需要重新评估价格口径、交易安全和文件冲突风险 |
| 先实现 QMT foundation，再补 CR017 | 备选 A | 更快看到 QMT adapter、OMS、risk gate 等交易基础模块；有利于早期接口形态验证 | 在复权双视图未落地前，交易侧可能临时使用不稳定价格口径；后续需要回改 QMT 价格输入 / 研究消费边界 | 用户最关心 QMT 接入骨架，且愿意接受后续因 CR017 调整带来的返工 | CR015 可更早启动；CR017 成为后续修正项 | 需要在实现中增加临时防线，禁止 adjusted price 流入 QMT order price |
| 三批完全并行实现 | 备选 B，不推荐 | 理论上日历时间最短；适合人员充足且模块边界完全稳定的团队 | 共享文件和接口契约冲突概率高；CR017 口径未稳定时 CR015/CR016 可能误接；CP6/CP7 排查成本上升；真实操作边界更容易混淆 | 只适合强并行团队且接受更高协调成本 | 可最大化并行，但必须增加锁文件 / ownership / merge gate | 当前不推荐；如果采用，需要先重写 DEVELOPMENT-PLAN 的 Wave 和文件所有权约束 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 HLD / ADR 已 approved | 通过 | `checkpoints/CP3-CR015-CR016-CR017-HLD-REVIEW.md` | 用户已回复 `@meta-po 通过，继续。` |
| CP4 自动预检 PASS | 通过 | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | 用户已接受 CP4 摘要汇入 CP5。 |
| 20 个 Story 卡片已创建并进入 LLD review | 通过 | `process/stories/CR015-S*.md`、`process/stories/CR016-S*.md`、`process/stories/CR017-S*.md` | 本批 20 个 Story 全量纳入。 |
| 20 份 LLD 已生成 | 通过 | `process/stories/CR015-S*-LLD.md`、`process/stories/CR016-S*-LLD.md`、`process/stories/CR017-S*-LLD.md` | 本批 20 份 LLD 全量纳入。 |
| 20 份 Story 级 CP5 自动预检均 PASS | 通过 | `process/checks/CP5-CR015-*`、`process/checks/CP5-CR016-*`、`process/checks/CP5-CR017-*` | 20 份 Story 级 CP5 自动预检均 PASS。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR017 6 个复权双视图 LLD | 通过 | `process/stories/CR017-S01..S06-*-LLD.md` | 接受。 |
| 2 | 是否接受 CR015 7 个 QMT foundation LLD | 通过 | `process/stories/CR015-S01..S07-*-LLD.md` | 接受。 |
| 3 | 是否接受 CR016 7 个 activation / runbook / gate LLD | 通过 | `process/stories/CR016-S01..S07-*-LLD.md` | 接受；CR016-S05 / S06 later-gated。 |
| 4 | 是否接受 20 份 CP5 自动预检均 PASS | 通过 | `process/checks/CP5-CR015-*`、`process/checks/CP5-CR016-*`、`process/checks/CP5-CR017-*` | 接受。 |
| 5 | 是否接受 CP5 approve 后可进入受控实现队列 | 通过 | 本文件 Decision Brief CP5-D1 / CP5-D2 | 接受；进入 story-execution。 |
| 6 | 是否确认 CP5 approve 不授权真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实写湖或 publish | 通过 | 本文件 Decision Brief CP5-D2 | 确认；真实操作授权仍为 0。 |
| 7 | 是否接受 CR016-S05 / CR016-S06 later-gated | 通过 | `process/stories/CR016-S05-*-LLD.md`、`process/stories/CR016-S06-*-LLD.md` | 接受；只确认设计，不授权真实 live / scale_up。 |
| 8 | 是否接受按 CR017 -> CR015 -> CR016 的依赖顺序与文件所有权推进实现 | 通过 | `process/DEVELOPMENT-PLAN.yaml`、CP4 文件 | 接受；可并行项仍按文件所有权并行。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户已明确 approve / 修改 / reject | 通过 | 用户回复 `@meta-po 通过，继续。` | 结论为 approved。 |
| 若 approve，20 个 Story 可进入 story-execution 的受控实现队列 | 通过 | 本文件人工审查结果 | 可进入 story-execution；真实操作仍未授权。 |
| 若修改或 reject，不进入实现，按指定范围回退 | N/A | 本文件人工审查结果 | 本轮未选择修改或 reject。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CP4 自动预检 | `process/checks/CP4-CR015-CR016-CR017-STORY-DAG-PARALLEL-SAFETY.md` | 通过 | PASS。 |
| CR017 LLD 批次 | `process/stories/CR017-S01..S06-*-LLD.md` | 通过 | 全量接受。 |
| CR017 CP5 自动预检 | `process/checks/CP5-CR017-S01..S06-*-LLD-IMPLEMENTABILITY.md` | 通过 | PASS。 |
| CR015 LLD 批次 | `process/stories/CR015-S01..S07-*-LLD.md` | 通过 | 全量接受。 |
| CR015 CP5 自动预检 | `process/checks/CP5-CR015-S01..S07-*-LLD-IMPLEMENTABILITY.md` | 通过 | PASS。 |
| CR016 LLD 批次 | `process/stories/CR016-S01..S07-*-LLD.md` | 通过 | 全量接受；S05/S06 later-gated。 |
| CR016 CP5 自动预检 | `process/checks/CP5-CR016-S01..S07-*-LLD-IMPLEMENTABILITY.md` | 通过 | PASS。 |
| LLD 批次 handoff | `process/handoffs/META-DEV-CR017-LLD-BATCH-A-2026-05-28.md`、`process/handoffs/META-DEV-CR015-LLD-BATCH-A-2026-05-28.md`、`process/handoffs/META-DEV-CR016-LLD-BATCH-A-2026-05-28.md` | 通过 | 三个 LLD 批次均已 completed / closed。 |

## 人工审查结果

- 结论：approved
- 审查人：user
- 审查时间：2026-05-28T07:03:27+08:00
- 修改意见：无
- 风险接受项：
  - 接受 CP5-D1 推荐方案：20 个 Story 的全量 LLD 进入 story-execution 受控实现队列。
  - 接受 CP5-D2 推荐方案：仅授权离线 / mock / fixture / 文档 / dry-run / shadow 实现；真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实写湖、publish 仍为 0。
  - 接受 CP5-D3 推荐方案：CR016-S05 / CR016-S06 只确认 LLD，保持 later-gated，不授权真实 live_readonly / small_live / scale_up。
  - 接受 CP5-D4 推荐方案：按 CR017 -> CR015 -> CR016 的依赖顺序和文件所有权推进；可并行项仍受 `max_parallel_dev=2`、依赖和文件冲突门控约束。
