请审查：checkpoints/CP8-CR030-DELIVERY-READINESS.md

自动预检结论：PASS
本轮待人工决策项：4

如果你回复 approve，表示你接受以下 4 项推荐方案，不表示授权以下 10 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP8-CR030-01 | follow_up_tracking | 是否接受 CR-030 当前交付范围已完成，并允许 CP8 approve 后关闭本 CR。 | approve 后关闭 CR-030 当前多因子研究与实验闭环交付范围，并确认策略侧已达到模拟盘入口审查输入。 | 修改指定文档 / 状态 / 证据后重跑 CP8；或 reject 回退到指定阶段。 | 推荐方案可收敛 8 个 verified Story，让多因子策略研究、实验和本地回测准备开始；代价是不追加真实运行或外部 runtime 能力。 | 主要风险是被误读为真实模拟盘 / 实盘能力，已通过不授权项隔离。 |
| DQ-CP8-CR030-02 | runtime_authorization | 是否确认 CP8 approve 不授权依赖变更、外部项目 clone/install/run/source copy、provider/lake/publish、QMT/simulation/live、账号/订单或凭据读取。 | 接受不授权边界，CP8 只关闭受控离线研究闭环交付。 | 单独启动 CR-020..CR-024、CR-026 或 Spike；或回退补强不授权措辞。 | 推荐方案审计风险最低；代价是后续真实路线仍需独立授权和门控。 | 若误授权会触发交易、凭据、写湖、publish 或 license 风险。 |
| DQ-CP8-CR030-03 | follow_up_tracking | 是否接受后续分流：CR-026、optimizer / ML / external runtimes、CR-020..CR-024、CR-027 / CR-028 保持候选或 Spike。 | 接受分流；CR-030 关闭后，多因子策略研究、实验和本地回测可继续，QMT 接口 ready 后投入模拟盘仍从 CR-020 / CR-021 开始单独授权。 | 合并 CR-026 与 optimizer / ML；或先启动 CR-020 / CR-021；或全部等待。 | 推荐方案符合先完成策略侧研究实验闭环、再完成 QMT 接口 / simulation 账号准入、最后进入真实 QMT 路线的顺序；代价是不会自动集成外部 runtime 或真实账号。 | 影响 roadmap、文件 owner、依赖和安全边界；候选启动前仍需冲突预检。 |
| DQ-CP8-CR030-04 | risk_acceptance | 是否接受“模拟盘入口”的语义边界：当前出口是策略侧模拟盘入口审查输入，已完成多因子策略研究与实验闭环、StrategyAdmissionPackage 和 handoff 草稿；不是 QMT-ready / simulation-ready / live-ready。 | 接受风险；将 CR-030 关闭为 strategy-side simulation-entry preparation complete; QMT interface and runtime authorization pending。QMT 接口 ready 且后续运行侧门控通过后，才可投入模拟盘。 | 回退 documentation，改成更保守措辞后重跑 S08 safety scan 和 CP8；或新增策略准入修复 CR。 | 推荐方案保留用户目标导向；代价是需要持续提醒这只是策略侧入口，不等于真实模拟盘授权。 | 风险等级 MEDIUM；主要风险是将策略侧入口误认为 QMT 接口、simulation 账号或订单通道已 ready。 |

不授权项：

- 修改 `pyproject.toml` / `uv.lock` 或新增 / 安装 Qlib、Alphalens、vectorbt、PyBroker、bt、Zipline Reloaded、QuantConnect LEAN、RQAlpha、vn.py、Backtrader、optimizer、ML 等依赖。
- clone / install / run 外部项目、外部 runner、Notebook、qrun、样例或测试。
- 复制、裁剪、改写、vendoring、fork 或源码级迁移任何外部项目源码、样例、测试或数据。
- provider fetch、真实联网补数、真实 lake write、catalog publish / current pointer publish、broker lake write 或 reports overwrite。
- 调用 QMT、MiniQMT、XtQuant；启动 gateway、端口绑定、simulation、live_readonly、small_live、scale_up。
- 发单、撤单、账户查询、持仓查询、账户写操作或 broker 操作。
- 读取、打印、记录或保存 token、API key、cookie、session、账号、密码、交易密码、私钥、`.env` 或其他凭据。
- 将 CR-030、因子评价报告、多因子组合、catalog 或 `StrategyAdmissionPackage` 声明为 production truth、QMT-ready、simulation-ready、live-ready、真实模拟盘可用、真实交易可用或真实可交易证据。
- 自动启动 CR-020..CR-024、CR-026、CR-027、CR-028、optimizer / ML / external runtime Spike。
- 将 CP8 approve 解释为真实 simulation 账号、QMT gateway、订单、账户、provider、lake 或 publish 的运行授权。

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受上表全部推荐方案；如需调整，请用 `修改: <具体修改点>` 指明决策 ID 和修改内容。
审查后请在“人工审查结果”中填写结论，也可以直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```
