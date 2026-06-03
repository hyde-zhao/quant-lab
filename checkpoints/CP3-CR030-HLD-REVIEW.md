---
checkpoint_id: "CP3-CR030-HLD-REVIEW"
checkpoint_name: "CR-030 HLD 人工审查"
type: "manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-03T07:34:00+08:00"
change_id: "CR-030"
auto_check_result: "process/checks/CP3-CR030-HLD-CONSISTENCY.md"
discussion_checkpoint: "process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json"
target_hld: "process/HLD.md"
target_hld_section: "§35"
auto_final_authorization: false
---

# CP3 CR-030 HLD 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP3-CR030-HLD-CONSISTENCY.md` | PASS | 0 | HLD / discussion / schema / 外部项目矩阵 / 不授权边界一致；未进入 Story、实现、依赖或真实运行。 |
| `process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json` | PASS | 0 | `cp3_hld_ready_for_meta_po=true`，5 个 Architecture Gray Areas 已处理，7 个 CP3 DQ 已形成。 |
| `process/HLD.md` §35 | draft-pending-cp3-cr030 | 0 | HLD v2.9 已追加 CR-030 多因子研究闭环设计。 |

## Decision Brief

### 推荐决策

建议 `approve` CR-030 HLD 草案，接受推荐方案 CR30-A：项目自有多因子研究闭环主线。外部项目只作为 `reference_only` / `optional_spike` / `exclude` / `forbidden_migration` 管理；schema 采用项目自有契约、现有基线复用、外部项目 cross-check 和 fail-closed；CR-026 Qlib isolated runner 保持后续 Spike candidate。

如果用户回复 `approve`，表示接受以下 7 项推荐方案，并允许 CR-030 在后续由 meta-se 进入 story-planning / CP4 准备；不表示授权实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live、账户操作或凭据读取。自动终验授权：auto_final_authorization: false。

### 候选架构适用条件、优化项、牺牲项、影响面与切换条件

| 方案 | 适用条件 | 优化项 | 牺牲项 | 影响面 | 切换条件 |
|---|---|---|---|---|---|
| CR30-A 项目自有多因子研究闭环主线（推荐） | 当前 CP3；已有数据湖、`research_input_v1`、实验 17-21、CR-011、Stage6 gate 和 CR-025 handoff 基线 | truth 一致、权限最小、可审计、可 fail-closed、易解释 | 短期不获得 Qlib qrun / optimizer runtime | HLD、Story、schema、QA、报告、admission package | 若自有 runner 表达力或性能不足，合同冻结后另启 CR-026 / Spike |
| CR30-B Qlib runner-first / qrun 集成 | FactorPanel / LabelWindow / ReportCatalog / runner I/O 合同已冻结，且用户另行授权依赖和运行 | workflow 和 recorder 生态成熟，后续 ML 空间大 | provider_uri、qrun、MLflow/pickle、LightGBM/cvxpy、数据格式和双 truth 风险高 | 依赖、数据入口、runner、provider、报告 truth、安全、维护 | 仅通过 CR-026 单独启动，不作为 CR-030 默认 |
| CR30-C 文档 / Spike-only | 用户暂不接受合同冻结，或需先做许可证 / 依赖 Spike | 成本最低、风险最低 | 无法为 CP4/CP5 提供可执行输入 | 文档、Decision Brief、后续 backlog | CP3 不通过时回退 |
| CR30-D 外部框架适配层 / adapter-first | 内部合同已稳定，且出现明确外部 runner / analyzer 导入需求 | 可导入外部分析生态 | 内部合同未冻结前会形成空转抽象和双 truth | 映射层、错误码、测试、维护 | 后续增强，不进入 P0 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 推荐 / 备选优劣摘要 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP3-CR030-01 | architecture | 是否接受 CR30-A 项目自有多因子研究闭环作为 HLD 推荐方案？ | 接受 CR30-A；外部项目只 reference / Spike / exclude / forbidden migration。 | A. Qlib runner-first；B. 文档 / Spike-only。 | 推荐方案最贴合现有 truth 和权限边界；Qlib-first 生态强但依赖 / provider 风险高；doc-only 无法支撑落地。 | 影响 Story 边界、依赖策略、数据 truth 和 QA。 | 若用户要求 runner，回退到 CR-026 CP2/CP3。 |
| DQ-CP3-CR030-02 | implementation | 是否接受 schema provenance 和字段字典方案？ | 采用项目自有契约 + 现有基线复用 + external cross-check + fail-closed。 | A. 直接采用外部对象；B. 从零设计。 | 推荐方案兼顾项目事实源和成熟经验；直接采用外部对象会产生依赖和双 truth；从零设计遗漏风险高。 | 影响 `FactorSpec` 等 10 个合同和后续测试 fixture。 | CP3 修改字段字典后重跑自动预检。 |
| DQ-CP3-CR030-03 | follow_up_tracking | CR-026 Qlib isolated runner 是否继续后置？ | 保持后续 Spike candidate，不并行启动。 | A. 合并入 CR-030 P0；B. 取消。 | 推荐方案避免 runner 绑架 schema；合并会扩大权限和依赖；取消会丢失 Qlib runtime 价值。 | 影响 CR tracking 和后续路线。 | 合同冻结、依赖隔离和运行授权明确后启动 CR-026。 |
| DQ-CP3-CR030-04 | implementation | MultiFactorCombiner 是否默认采用可解释组合、optimizer 后置？ | P0 使用规则权重 / 轻量线性组合；EnhancedIndexing / cvxpy / ML optimizer 转 Spike。 | A. 默认 optimizer；B. 不设计组合。 | 推荐方案易解释可验证；默认 optimizer 依赖和风险模型要求高；不设计组合无法形成准入闭环。 | 影响组合、成本、容量和 benchmark 约束。 | 若 P0 组合不足且用户接受依赖风险，另起 optimizer Spike。 |
| DQ-CP3-CR030-05 | security | 是否确认 CP3 通过不授权实现、依赖变更、外部项目运行或真实操作？ | 确认不授权；只批准 HLD 进入后续规划。 | A. 授权 bounded external runtime Spike；B. 授权依赖安装但不运行。 | 推荐方案权限最小；运行 Spike 证据更强但扩大安全 / 许可证面。 | 防止 provider/lake/QMT/credential 越权。 | 需要运行时另起 CR / Spike 和 per-run 授权。 |
| DQ-CP3-CR030-06 | runtime_authorization | 是否接受 `StrategyAdmissionPackage` 只输出 `order_intent_draft_v1` 草稿，不生成真实 order？ | 接受；真实 QMT / simulation / live 仍由 CR-020..CR-024 单独授权。 | A. 生成可执行 order；B. 完全不设计执行 handoff。 | 推荐方案保留生产路线衔接且不越权；可执行 order 风险极高；不设计 handoff 削弱 Stage6 闭环。 | 影响 QMT route、admission 文档和用户误读风险。 | QMT CR approved 后再消费 draft。 |
| DQ-CP3-CR030-07 | risk_acceptance | 是否接受静态调研支撑 HLD、runtime 细节转后续 Spike 的残余风险？ | 接受静态调研作为 CP3 证据，runtime 细节不阻断 HLD。 | A. 要求先运行外部项目；B. 删除外部项目参考。 | 推荐方案符合当前权限；运行证据更强但越权；删除参考会降低 cross-check 质量。 | 静态资料可能遗漏 runtime 约束。 | 后续实现发现阻塞时转 bounded Spike。 |

### 不授权项

| 不授权项 | 状态 |
|---|---|
| 实现 CR-030 Story、修改业务代码或测试代码 | 不授权 |
| 修改 `pyproject.toml` / `uv.lock` 或新增依赖 | 不授权 |
| clone / install / run Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py、Backtrader 或其他外部项目 | 不授权 |
| 运行 qrun、Notebook、外部 runner、外部 provider 或外部样例 | 不授权 |
| 复制、裁剪、改写、vendor、fork 或源码级迁移外部项目代码 / 样例 / 测试 / 数据 | 不授权 |
| provider fetch、真实联网补数、真实 lake write、catalog publish、broker lake write、reports overwrite | 不授权 |
| QMT / MiniQMT / XtQuant、gateway 启动、simulation、live_readonly、small_live、scale_up | 不授权 |
| 发单、撤单、账户查询、账户写操作、broker 操作 | 不授权 |
| 读取、打印、记录或保存凭据、token、session、cookie、交易密码、私钥或 `.env` 内容 | 不授权 |
| 把 HLD、因子评价、多因子组合或 `StrategyAdmissionPackage` 声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据 | 不授权 |

### CP3 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| HLD | `process/HLD.md` §35，推荐 CR30-A 项目自有多因子研究闭环。 |
| discussion log / checkpoint | `process/discussions/CP3-CR030-HLD-DISCUSSION-LOG.md`；`process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json`。 |
| 自动预检 | `process/checks/CP3-CR030-HLD-CONSISTENCY.md`，结论 PASS，阻断项 0。 |
| meta-se handoff | `process/handoffs/META-SE-CR030-HLD-2026-06-03.md`。 |
| Architecture Gray Areas | AGA-CR030-01 至 AGA-CR030-05 已处理；AGA-CR030-04 为 non-blocking-open，转 optimizer Spike 条件。 |
| 外部项目矩阵 | 覆盖 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py / vnpy.alpha、Backtrader。 |
| schema 方案 | 项目自有契约 + `research_input_v1` / 实验 17-21 / CR-011 / label gate / Stage6 gate 基线复用 + 外部 cross-check + fail-closed。 |
| 回退点 | 若 CP3 不通过，回退到 solution-design，按 DQ 修改 HLD §35、discussion checkpoint 和自动预检。 |

## Entry Criteria

| 条目 | 审查状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP2 已批准进入 CP3 | approved | `checkpoints/CP2-CR030-REQUIREMENTS-BASELINE.md` status=`approved` | 用户已要求组织 meta-se 输出 HLD。 |
| HLD 草案已完成 | approved | `process/HLD.md` §35 | 用户已确认 HLD 完成并接受全部推荐决策。 |
| CP3 自动预检 PASS | approved | `process/checks/CP3-CR030-HLD-CONSISTENCY.md` | 阻断项 0；用户接受自动预检结论。 |
| CP3 discussion checkpoint PASS | approved | `process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json` | 7 个 CP3 决策项全部接受推荐方案。 |

## Checklist

| # | 检查项 | 审查状态 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR30-A 推荐架构 | approved | DQ-CP3-CR030-01 | 接受推荐方案。 |
| 2 | 是否接受 schema provenance、字段字典、错误码和 fail-closed | approved | DQ-CP3-CR030-02 | 接受推荐方案。 |
| 3 | 是否接受 CR-026 Qlib runner 后置 | approved | DQ-CP3-CR030-03 | 接受推荐方案。 |
| 4 | 是否接受 P0 可解释组合、optimizer 后置 | approved | DQ-CP3-CR030-04 | 接受推荐方案。 |
| 5 | 是否确认 CP3 不授权实现 / 依赖 / 外部运行 / 真实操作 | approved | DQ-CP3-CR030-05 | 接受推荐方案；CP3 只批准 HLD 进入后续规划。 |
| 6 | 是否接受 StrategyAdmissionPackage 仅输出 draft handoff | approved | DQ-CP3-CR030-06 | 接受推荐方案。 |
| 7 | 是否接受静态调研作为 CP3 证据，runtime 细节后置 | approved | DQ-CP3-CR030-07 | 接受推荐方案。 |

## Exit Criteria

| 条目 | 审查状态 | 证据 | 审查意见 |
|---|---|---|---|
| 若 approve：CR-030 HLD 通过，可进入 story-planning / CP4 准备 | approved | 本 Decision Brief；用户 2026-06-03 确认 | approve 只表示 HLD 通过，不授权实现或真实运行。 |
| 若修改：meta-se 按修改点刷新 HLD / discussion checkpoint / CP3 预检 | pending | 用户修改意见 | 需重新发布 Decision Brief。 |
| 若 reject：回退到 solution-design 或 requirement-clarification | pending | 用户拒绝意见 | 需重新梳理 Architecture Gray Areas 或 CP2 基线。 |

## Deliverables

| 交付物 | 路径 | 审查状态 | 说明 |
|---|---|---|---|
| HLD 增量 | `process/HLD.md` §35 | approved | CR-030 HLD v2.9；用户接受全部推荐决策。 |
| CP3 discussion log | `process/discussions/CP3-CR030-HLD-DISCUSSION-LOG.md` | approved | AGA + advisor table。 |
| CP3 discussion checkpoint | `process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json` | approved | PASS。 |
| CP3 自动预检 | `process/checks/CP3-CR030-HLD-CONSISTENCY.md` | approved | PASS。 |
| meta-se handoff | `process/handoffs/META-SE-CR030-HLD-2026-06-03.md` | approved | completed。 |

## 人工审查结果

| 字段 | 内容 |
|---|---|
| 审查结论 | approved |
| 审查人 | user |
| 审查时间 | 2026-06-03T07:45:10+08:00 |
| 用户原文 | `@meta-po 之前的会话不可用了。我现在需要推进CR-030，HLD已完成设计，所有决策项我都同意了。你可以继续推进了。` |
| 接受的推荐决策 | DQ-CP3-CR030-01、DQ-CP3-CR030-02、DQ-CP3-CR030-03、DQ-CP3-CR030-04、DQ-CP3-CR030-05、DQ-CP3-CR030-06、DQ-CP3-CR030-07 |
| 自动终验授权 | auto_final_authorization: false |
| 不授权项 | 实现、依赖变更、外部项目运行、源码迁移、provider/lake/publish、QMT/simulation/live、账户操作、凭据读取均不授权 |
