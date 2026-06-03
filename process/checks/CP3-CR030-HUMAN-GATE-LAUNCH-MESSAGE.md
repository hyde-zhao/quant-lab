# CP3 CR-030 Human Gate Launch Message

## 门禁元信息

| 字段 | 内容 |
|---|---|
| Gate | CP3 HLD 人工审查 |
| Change | CR-030 |
| Checklist | `checkpoints/CP3-CR030-HLD-REVIEW.md` |
| 自动预检 | `process/checks/CP3-CR030-HLD-CONSISTENCY.md`，结论 `PASS`，阻断项 0 |
| Discussion checkpoint | `process/checks/CP3-CR030-DISCUSSION-CHECKPOINT.json`，结论 `PASS` |
| HLD | `process/HLD.md` §35 |
| 待决策项数量 | 7 |
| 不授权项数量 | 10 |

## 发起消息

请审查：`checkpoints/CP3-CR030-HLD-REVIEW.md`

自动预检结论：`PASS`，阻断项 0。`meta-se/se-wei` 已完成 CR-030 HLD，推荐方案是 CR30-A：项目自有多因子研究闭环主线；Qlib 等外部项目只作为 reference / optional Spike / exclude / forbidden migration；schema 方案是项目自有契约 + 既有基线复用 + 外部项目 cross-check + fail-closed。

本轮待人工决策项：7

如果你回复 approve，表示你接受以下 7 项推荐方案；不表示授权以下 10 项禁止操作。

待人工决策清单：

| 决策 ID | 类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP3-CR030-01 | architecture | 是否接受 CR30-A 项目自有多因子研究闭环作为 HLD 推荐方案？ | 接受 CR30-A；外部项目只 reference / Spike / exclude / forbidden migration。 | Qlib runner-first；文档 / Spike-only。 | 影响 Story 边界、依赖策略、数据 truth 和 QA。 |
| DQ-CP3-CR030-02 | implementation | 是否接受 schema provenance 和字段字典方案？ | 项目自有契约 + 现有基线复用 + external cross-check + fail-closed。 | 直接采用外部对象；从零设计。 | 影响 `FactorSpec` 等合同和后续测试 fixture。 |
| DQ-CP3-CR030-03 | follow_up_tracking | CR-026 Qlib isolated runner 是否继续后置？ | 保持后续 Spike candidate，不并行启动。 | 合并入 CR-030 P0；取消。 | 影响 CR tracking 和后续路线。 |
| DQ-CP3-CR030-04 | implementation | MultiFactorCombiner 是否默认采用可解释组合、optimizer 后置？ | P0 使用规则权重 / 轻量线性组合；optimizer 转 Spike。 | 默认 optimizer；不设计组合。 | 影响组合、成本、容量和 benchmark 约束。 |
| DQ-CP3-CR030-05 | security | 是否确认 CP3 通过不授权实现、依赖变更、外部项目运行或真实操作？ | 确认不授权；只批准 HLD 进入后续规划。 | 授权 bounded runtime Spike；授权安装但不运行。 | 防止 provider/lake/QMT/credential 越权。 |
| DQ-CP3-CR030-06 | runtime_authorization | 是否接受 `StrategyAdmissionPackage` 只输出 `order_intent_draft_v1` 草稿，不生成真实 order？ | 接受；真实 QMT / simulation / live 仍由 CR-020..CR-024 单独授权。 | 生成可执行 order；完全不设计执行 handoff。 | 影响 QMT route 和误读风险。 |
| DQ-CP3-CR030-07 | risk_acceptance | 是否接受静态调研支撑 HLD、runtime 细节转后续 Spike 的残余风险？ | 接受静态调研作为 CP3 证据，runtime 细节不阻断 HLD。 | 先运行外部项目；删除外部项目参考。 | 静态资料可能遗漏 runtime 约束。 |

不授权项：

| 不授权项 | 状态 |
|---|---|
| 实现 CR-030 Story、修改业务代码或测试代码 | 不授权 |
| 修改 `pyproject.toml` / `uv.lock` 或新增依赖 | 不授权 |
| clone / install / run 外部项目，包括 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py、Backtrader | 不授权 |
| 运行 qrun、Notebook、外部 runner、外部 provider 或外部样例 | 不授权 |
| 复制、裁剪、改写、vendor、fork 或源码级迁移外部项目代码 / 样例 / 测试 / 数据 | 不授权 |
| provider fetch、真实联网补数、真实 lake write、catalog publish、broker lake write、reports overwrite | 不授权 |
| QMT / MiniQMT / XtQuant、gateway 启动、simulation、live_readonly、small_live、scale_up | 不授权 |
| 发单、撤单、账户查询、账户写操作、broker 操作 | 不授权 |
| 读取、打印、记录或保存凭据、token、session、cookie、交易密码、私钥或 `.env` 内容 | 不授权 |
| 把 HLD、因子评价、多因子组合或 `StrategyAdmissionPackage` 声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据 | 不授权 |

推荐回复只有三种：

approve

修改: <具体修改点>

reject
