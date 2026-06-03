请审查：checkpoints/CP8-CR025-DELIVERY-READINESS.md

自动预检结论：PASS
本轮待人工决策项：4

如果你回复 approve，表示你接受以下 4 项推荐方案，不表示授权以下 10 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP8-CR025-01 | follow_up_tracking | 是否接受 CR-025 当前交付范围已完成，并允许 CP8 approve 后关闭本 CR。 | approve 后关闭 CR-025 当前 research execution semantic alignment 交付范围。 | 修改指定文档 / 状态 / 证据后重跑 CP8；或 reject 回退到指定阶段。 | 推荐方案可收敛 6 个 verified Story 和文档交付；代价是不追加真实运行或多因子主框架能力。 | 主要风险是被误读为完整模拟盘 / 实盘能力，已通过不授权项隔离。 |
| DQ-CP8-CR025-02 | runtime_authorization | 是否确认 CP8 approve 不授权依赖变更、Backtrader 运行、源码迁移、真实 broker / QMT / provider / lake / publish / simulation / live、凭据读取或多因子研究主框架实现。 | 接受不授权边界，CP8 只关闭受控离线交付。 | 单独启动 CR-020..CR-024、CR-026、CR-030 或 Spike；或回退补强不授权措辞。 | 推荐方案审计风险最低；代价是后续真实路线仍需独立授权和门控。 | 若误授权会触发交易、凭据、写湖、publish 或 license 风险。 |
| DQ-CP8-CR025-03 | follow_up_tracking | 是否接受后续三条主线分流：CR-030/CR-026/CR-020..CR-024/CR-027/CR-028 保持候选或 Spike。 | 接受分流；CR-025 关闭后默认可先启动 CR-030 冲突预检，真实 QMT 从 CR-020 起步。 | 合并 CR-030 与 CR-026；或先启动 CR-020；或全部等待。 | 推荐方案符合先研究路线、最后真实 QMT 的顺序；代价是不会自动实现候选能力。 | 影响 roadmap、文件 owner 和安全边界；候选启动前仍需冲突预检。 |
| DQ-CP8-CR025-04 | risk_acceptance | 是否接受低残余风险：CR-025 文档保留本地 Backtrader 源码树路径作为 no-read / no-copy 边界字符串，且 S06 首轮 CP7 FAIL 保留为历史证据。 | 接受风险；路径只是禁止边界，最新 REVERIFY 已 PASS。 | 用户文档路径泛化后重跑 S06 文档扫描和 CP8；或回退 documentation。 | 推荐方案保留完整追溯链；代价是用户文档仍出现本地路径字符串。 | 风险等级 LOW；credential / private-path scan 为 0。 |

不授权项：

- 修改 `pyproject.toml` / `uv.lock` 或新增 / 安装 Backtrader、Qlib、Alphalens、vectorbt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py、PyBroker、bt 等依赖。
- 运行 Backtrader runtime、samples、tests 或把 Backtrader 作为默认执行引擎。
- 读取、扫描、复制、裁剪、改写、vendoring 或源码级移植 Backtrader GPLv3 源码、samples、tests、datas、live store、line / metaclass runtime。
- 启动 gateway / broker / provider / 外部服务或端口绑定。
- 调用真实 broker、QMT、MiniQMT、XtQuant；发单、撤单、账户查询、持仓查询或写 broker lake。
- provider fetch、真实联网补数、真实 lake write、catalog publish / current pointer publish。
- simulation、live、live-readonly、small-live、scale-up 或任何真实账户操作。
- 读取、打印、记录或保存 token、API key、cookie、session、账号、密码、交易密码、私钥或其他凭据。
- 将 CR-025 结论声明为 production truth、simulation-ready、QMT admission pass、真实交易可用或完整多因子研究框架已实现。
- 实现 FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪、策略准入包，或集成任何外部多因子 / 交易框架。

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受上表全部推荐方案；如需调整，请用 `修改: <具体修改点>` 指明决策 ID 和修改内容。
审查后请在“人工审查结果”中填写结论，也可以直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```
