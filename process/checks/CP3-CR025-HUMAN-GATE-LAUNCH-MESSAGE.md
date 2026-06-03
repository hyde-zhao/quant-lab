# CP3 CR-025 Human Gate Launch Message

> 本文件记录 meta-po 发起 CR-025 CP3 人工门禁前的消息草案与校验结果。`scripts/check_human_gate_decision_brief.py` 当前不存在，故人工门禁脚本校验记为 `N/A`；本消息按 Human Gate Launch Protocol 手工覆盖 checklist 路径、自动预检结论、待决策项数量、待决策表格和三个 exact 回复。

## 门禁元信息

| 字段 | 内容 |
|---|---|
| Gate | CP3 HLD 人工审查 |
| Change | CR-025 |
| Checklist | `checkpoints/CP3-CR025-HLD-REVIEW.md` |
| 自动预检 | `process/checks/CP3-CR025-HLD-CONSISTENCY.md`，结论 `PASS`，阻断项 0 |
| Discussion checkpoint | `process/checks/CP3-CR025-DISCUSSION-CHECKPOINT.json`，`cp3_ready=true` |
| HLD | `process/HLD.md` §34 |
| ADR | `process/ARCHITECTURE-DECISION.md` ADR-074..077 |
| HLD-QMT 同步 | `process/HLD-QMT-TRADING.md` §18 |
| 待决策项数量 | 6 |
| 不授权项数量 | 10 |

## 发起消息

CR-025 的 CP3/HLD 已由 `meta-se/se-chu` 完成并通过自动预检。请审查 `checkpoints/CP3-CR025-HLD-REVIEW.md`。

自动预检结论：`PASS`，阻断项 0。Backtrader 本地项目 `/home/hyde/download/backtrader` 已做静态分析：本地 license 为 GNU GPL v3 / GPLv3+；HLD §34.5 已记录模块级矩阵，当前默认 `migration_candidate` 为空，源码级复制 / 裁剪 / 改写 / vendor / fork 均不作为默认方案。

如果你回复 `approve`，表示你接受以下 6 项推荐方案；不表示授权以下 10 项禁止操作。

### 待人工决策清单

| 决策 ID | 类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP3-CR025-01 | `architecture` | 是否接受 Backtrader 默认只作为 optional semantic reference / design reference，不替代 lightweight 主路径？ | 接受 CR25-A：lightweight baseline 保持默认，Backtrader 只用于设计参考和研究对照声明。 | CP5 后 optional runtime；主路径迁移 / 完整框架评估 CR。 | 影响默认入口、依赖、回归、用户 truth 认知。 |
| DQ-CP3-CR025-02 | `architecture` | 是否接受 Backtrader 模块矩阵分类和默认无源码级移植推荐？ | 接受 HLD §34.5：reference-only / adapt-interface / exclude；`migration_candidate` 当前为空。 | 标记 `order.py` / `trade.py` 为源码候选；只做高层描述不列矩阵。 | 影响 LLD forbidden path、文件 owner、验证策略和 GPLv3 风险。 |
| DQ-CP3-CR025-03 | `risk_acceptance` | 是否接受 GPLv3 源码级移植治理：默认 no-copy，任何例外需 CP3/CP5 双门控和合规确认？ | 接受 ADR-076；本轮只允许 clean-room adaptation 或 CP5 后 optional dependency。 | CP5 后 optional dependency 使用外部包；fork/vendor GPLv3 子集。 | 影响许可证、分发义务、长期维护和回归范围。 |
| DQ-CP3-CR025-04 | `implementation` | 是否接受 clean feed gate 与 semantic diff schema？ | 接受 HLD §34.6，覆盖 PIT、available_at、复权、benchmark、tradability、quality、成交、现金、成本、净值和差异原因。 | 只做 smoke；字段推迟到 LLD。 | 影响 adapter、报告、QA 和 Story 切分。 |
| DQ-CP3-CR025-05 | `architecture` | 是否接受 target portfolio / order intent draft 字段和 QMT 边界？ | 接受 HLD §34.7 与 HLD-QMT §18：CR-025 只输出 `order_intent_draft_v1`，不触发 QMT。 | 只输出 diff，不输出 intent draft；CR-025 直接接 QMT validate/dry-run。 | 影响后续 CR-020..CR-024、OMS/risk 输入和安全授权。 |
| DQ-CP3-CR025-06 | `runtime_authorization` | 是否确认 CR-025 CP3 不授权实现、依赖变更、Backtrader 运行、源码迁移或真实 broker/QMT/provider/lake/publish/simulation/live/credential 操作？ | 确认全部不授权，相关计数必须保持 0。 | 为 dependency Spike 单独建 CR；为 QMT/gateway/真实运行另起 CR / per-run authorization。 | 防止设计通过被误读为运行授权或账户操作授权。 |

### 不授权项

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

推荐回复只有三种：

- `approve`
- `修改: <具体修改点>`
- `reject`
