---
checkpoint_id: "CP3"
checkpoint_name: "CR-025 HLD 人工审查"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-01T21:53:17+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-01T22:37:12+08:00"
auto_check_result: "process/checks/CP3-CR025-HLD-CONSISTENCY.md"
target:
  phase: "solution-design"
  change_id: "CR-025"
  artifacts:
    - "process/HLD.md"
    - "process/HLD-QMT-TRADING.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md"
    - "process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json"
---

# CP3 CR-025 HLD 人工审查

> 本文件是 meta-se 为 meta-po 准备的 CP3 人工审查稿草案。正式发起、打印待人工决策清单、收集用户 `approve / 修改: <具体修改点> / reject` 并回填人工结果，仍由 meta-po 完成。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP3-CR025-HLD-CONSISTENCY.md` | PASS | 0 | HLD / ADR / discussion / QMT 边界同步完整；无实现、依赖、运行或真实操作。 |
| `process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json` | PASS | 0 | `cp3_ready=true`，5 个 AGA 均已形成 decision item。 |

## Decision Brief

### 推荐决策

建议 `approve` CR-025 HLD 草案，接受推荐方案 CR25-A：Backtrader 默认作为 optional semantic reference / design reference；本项目采用 clean-room interface adaptation，默认不源码级移植；CP5 前不得实现、改依赖、运行 Backtrader 或触发真实 broker/QMT/provider/lake/publish/simulation/live。

### 候选架构适用条件、优化项、牺牲项、影响面与切换条件

| 方案 | 适用条件 | 优化项 | 牺牲项 | 影响面 | 切换条件 |
|---|---|---|---|---|---|
| CR25-A Design reference + clean-room interface adaptation（推荐） | 当前 CP3；需模块级分析、语义对照和 order intent 草案，但不能实现或改依赖 | license 风险低、主路径稳定、HLD 可审计 | 不直接获得 Backtrader runtime 行为 | HLD、ADR、clean feed、semantic diff、order intent、QA 合同 | CP5 后若需真实 Backtrader 对照，切 CR25-B。 |
| CR25-B Optional dependency runtime | CP5 已批准实现；dependency、lazy import、分发策略和未安装回归已冻结 | 可运行外部 Backtrader 对照，不复制源码 | 依赖、版本、测试和文档成本上升 | pyproject/uv.lock、adapter、tests、docs | 依赖泄漏或分发策略不清时回退 CR25-A。 |
| CR25-C Source migration / fork | 用户明确接受 GPLv3/copyleft 风险并另起 CR / CP5 | 可深度改造事件循环或订单模型 | license、维护、回归和发布成本最高 | 许可证、代码 owner、QA、发布 | 仅在 CR25-A/B 不能满足已量化场景时评估。 |

### Use Case -> Architecture Traceability

| 对象 | 设计落点 | 结论 |
|---|---|---|
| UC-19 | `process/HLD.md` §34 | 覆盖 research-to-execution、Backtrader 模块矩阵、semantic diff、order intent draft。 |
| SM-33 / REQ-161 | HLD §34.3/§34.4；ADR-074 | lightweight 默认，Backtrader 不替代主路径。 |
| SM-34 / REQ-162 | HLD §34.11；ADR-074 | CP5 前不改依赖；未安装环境合法。 |
| SM-35 / REQ-163 | HLD §34.6 | clean feed gate 冻结。 |
| SM-36 / REQ-164 | HLD §34.6 | semantic diff schema 冻结。 |
| SM-37 / REQ-165 | HLD §34.13 | 真实操作计数目标为 0。 |
| SM-39 / REQ-169 | HLD §34.7；HLD-QMT §18 | order intent draft 与 QMT 消费边界清晰。 |
| SM-41 / REQ-173 | HLD §34.5 | Backtrader 本地项目模块级分析完成。 |

### 关键场景模拟结果

| 场景 | 结果 |
|---|---|
| 未安装 Backtrader，默认研究运行 | 走 lightweight baseline；Backtrader unavailable 不影响主路径。 |
| 同一 clean feed 做 semantic diff | CP3 只冻结 schema；CP5 后可实现，输出 research comparison。 |
| feed 缺 PIT / 复权混用 | clean feed gate fail，不进入 optional reference。 |
| 研究结果进入 QMT 路线 | 只生成 order intent draft；不启动 gateway。 |
| 有人要求复制 Backtrader 源码 | 被 ADR-076 阻断，需新 CP3/CP5 决策和合规确认。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP3-CR025-01 | `architecture` | 是否接受 Backtrader 默认只作为 optional semantic reference / design reference，不替代 lightweight 主路径？ | 接受 CR25-A：lightweight baseline 保持默认，Backtrader 只用于设计参考和研究对照声明。 | 备选 A：CP5 后 optional runtime；备选 B：主路径迁移 / 完整框架评估 CR。 | 推荐方案风险最低且满足 CP2；A 可运行但需依赖和回归；B 范围最大且不能解决 QMT 治理。 | 影响默认入口、依赖、回归、用户 truth 认知。 | 若用户要求真实 Backtrader 对照，CP5 后切 A；若要求主路径迁移，回退 CP2/另起 CR。 |
| DQ-CP3-CR025-02 | `architecture` | 是否接受 Backtrader 模块矩阵分类和默认无源码级移植推荐？ | 接受 HLD §34.5：reference-only / adapt-interface / exclude；`migration_candidate` 当前为空。 | 备选 A：标记 `order.py` / `trade.py` 为源码候选；备选 B：仅做高层描述不列矩阵。 | 推荐方案满足用户模块级要求且降低 license 风险；A 有源码风险；B 不满足 REQ-173。 | 影响 LLD forbidden path、文件 owner、验证策略。 | 若用户指定移植模块，必须新增 CP3 决策并进入 CP5 授权。 |
| DQ-CP3-CR025-03 | `risk_acceptance` | 是否接受 GPLv3 源码级移植治理：默认 no-copy，任何例外需 CP3/CP5 双门控和合规确认？ | 接受 ADR-076；本轮只允许 clean-room adaptation 或 CP5 后 optional dependency。 | 备选 A：CP5 后 optional dependency 使用外部包；备选 B：fork/vendor GPLv3 子集。 | 推荐方案合规风险最低；A 仍需依赖治理；B 维护和分发风险最高。 | GPLv3/copyleft、源码开放、修改标记、分发义务、长期维护。 | 若 legal/package 策略不明确，保持 no-copy；若用户接受 GPL 风险，另起 CR。 |
| DQ-CP3-CR025-04 | `implementation` | 是否接受 clean feed gate 与 semantic diff schema？ | 接受 HLD §34.6，覆盖 PIT、available_at、复权、benchmark、tradability、quality、成交、现金、成本、净值和差异原因。 | 备选 A：只做 smoke；备选 B：字段推迟到 LLD。 | 推荐方案可验证且可交接；A 无法解释差异；B 会让 CP4/CP5 输入不完整。 | 影响 adapter、报告、QA 和 Story 切分。 | 若字段过宽，CP4 可分 Story；若缺字段，回退 AGA-CR025-04。 |
| DQ-CP3-CR025-05 | `architecture` | 是否接受 target portfolio / order intent draft 字段和 QMT 边界？ | 接受 HLD §34.7 与 HLD-QMT §18：CR-025 只输出 `order_intent_draft_v1`，不触发 QMT。 | 备选 A：只输出 diff，不输出 intent draft；备选 B：CR-025 直接接 QMT validate/dry-run。 | 推荐方案连接 production route 且不越权；A 断开 QMT 衔接；B 越过 CR-020 门控。 | 影响后续 CR-020..CR-024、OMS/risk 输入和安全授权。 | 若用户要真实 gateway，另起 CR-020；若暂不接生产路线，保留 diff-only。 |
| DQ-CP3-CR025-06 | `runtime_authorization` | 是否确认 CR-025 CP3 不授权实现、依赖变更、Backtrader 运行、源码迁移或真实 broker/QMT/provider/lake/publish/simulation/live/credential 操作？ | 确认全部不授权，相关计数必须保持 0。 | 备选 A：为 dependency Spike 单独建 CR；备选 B：为 QMT/gateway/真实运行另起 CR / per-run authorization。 | 推荐方案符合 CP3 门控；备选需要更高风险门控。 | 防止设计通过被误读为运行授权或账户操作授权。 | 任一真实操作需求出现时，停止 CR-025，转独立 CR。 |

### 不授权项

如果用户回复 `approve`，表示接受以上 6 项推荐方案；不表示授权以下 10 类操作：

| 不授权项 | 状态 |
|---|---|
| 实现 Backtrader backend 或修改业务代码 / 测试代码 | 不授权 |
| 修改 `pyproject.toml` / `uv.lock` 或新增 Backtrader 依赖 | 不授权 |
| 运行 Backtrader optional backend、样例或测试 | 不授权 |
| 复制、裁剪、改写或源码级移植 Backtrader GPLv3 源码 | 不授权 |
| 接入 Backtrader live broker / store 或真实 broker | 不授权 |
| QMT / MiniQMT / XtQuant、gateway 启动、端口绑定、simulation、live、account query、order/cancel | 不授权 |
| provider fetch 或真实联网补数 | 不授权 |
| lake write、broker lake write、catalog publish | 不授权 |
| 读取、打印、记录或保存任何凭据 / token / session / cookie / 交易密码 | 不授权 |
| 把 Backtrader 输出声明为 production truth、simulation-ready 或 QMT admission pass | 不授权 |

### CP3 追加 Decision Brief 字段

| 字段 | 内容 |
|---|---|
| discussion log / checkpoint | `process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md`；`process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json`。 |
| 推荐 HLD | `process/HLD.md` §34：CR25-A design reference / clean-room interface adaptation。 |
| 备选方案 | CR25-B optional runtime after CP5；CR25-C source migration / fork only after explicit CP3/CP5 + compliance acceptance。 |
| Architecture Gray Areas 处理结果 | AGA-CR025-01 至 AGA-CR025-05 均处理为 decision-item，并进入 DQ-CP3-CR025-01 至 DQ-CP3-CR025-06。 |
| advisor table 摘要 | CR25-A 推荐，CR25-B 条件备选，CR25-C 不推荐默认，CR25-D 不采用。 |
| 关键取舍 | 牺牲短期运行 Backtrader 的便利性，换取 license 风险、默认回归、安全边界和 QMT 路线治理的可控性。 |
| 未决风险 | CP5 后若实现 optional runtime，仍需依赖版本、package/legal 策略、file owner、回归矩阵和不复制源码 guardrail。 |
| 回退点 | 若 CP3 不通过，回退 AGA-CR025-01/02/03/04/05，分别重新界定定位、模块范围、GPL 治理、schema 和 QMT 边界。 |

## Entry Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| CP2 已批准进入 CP3 | approved | `checkpoints/CP2-CR025-REQUIREMENTS-BASELINE.md` | 状态 approved。 |
| CP3 自动预检 PASS | approved | `process/checks/CP3-CR025-HLD-CONSISTENCY.md` | 阻断项 0。 |
| HLD / ADR / discussion 文件存在 | approved | 本文件 target artifacts | 用户回复“同意。继续”。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR25-A 推荐架构 | approved | DQ-CP3-CR025-01 | 接受推荐方案。 |
| 2 | 是否接受 Backtrader 模块矩阵和 no source migration 默认 | approved | DQ-CP3-CR025-02 | 接受推荐方案；当前 `migration_candidate` 为空。 |
| 3 | 是否接受 GPLv3 no-copy 治理 | approved | DQ-CP3-CR025-03 | 接受推荐方案；源码级例外需后续独立门控。 |
| 4 | 是否接受 clean feed gate 与 semantic diff schema | approved | DQ-CP3-CR025-04 | 接受推荐方案。 |
| 5 | 是否接受 order intent draft 与 QMT 边界 | approved | DQ-CP3-CR025-05 | 接受推荐方案；CR-025 不触发 QMT。 |
| 6 | 是否确认不授权实现 / 依赖 / 运行 / 真实操作 | approved | DQ-CP3-CR025-06 | 确认本 CP3 只批准 HLD / ADR，不授权实现、依赖、运行或真实操作。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 若 approve：CR-025 可进入 CP4 Story Plan | approved | CP3 Decision Brief；用户回复“同意。继续” | approve 只表示 HLD 通过，不授权实现或真实运行。 |
| 若修改：meta-se 按修改点刷新 HLD / ADR / CP3 预检 | N/A | 用户无修改意见 | 无需重新发布 Decision Brief。 |
| 若 reject：回退到 solution-design 或 requirement-clarification | N/A | 用户未拒绝 | 无需回退。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| HLD 增量 | `process/HLD.md` | approved | §34。 |
| QMT companion 同步 | `process/HLD-QMT-TRADING.md` | approved | §18。 |
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` | approved | ADR-074..077。 |
| CP3 自动预检 | `process/checks/CP3-CR025-HLD-CONSISTENCY.md` | approved | PASS。 |
| CP3 discussion log | `process/discussions/CP3-CR025-HLD-DISCUSSION-LOG.md` | approved | AGA + advisor table。 |
| CP3 discussion checkpoint | `process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json` | approved | cp3_ready。 |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-06-01T22:37:12+08:00
- 修改意见：用户回复“同意。继续”；接受 DQ-CP3-CR025-01 至 DQ-CP3-CR025-06 的推荐方案，允许进入 CP4 Story Plan。
- 风险接受项：接受 Backtrader 默认只作为 optional semantic reference / design reference；接受模块矩阵和当前无源码级移植推荐；接受 GPLv3 no-copy 治理；接受 clean feed gate、semantic diff schema、`order_intent_draft_v1` 与 QMT 消费边界；确认 CP3 不授权实现、依赖变更、Backtrader 运行、源码迁移或真实 broker / QMT / provider / lake / publish / simulation / live / credential 操作。
