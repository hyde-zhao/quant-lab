# CP5 CR-030 人工门禁发起消息草稿

请审查：`checkpoints/CP5-CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A-LLD-BATCH.md`

自动预检结论：CP4 PASS，CR030-S01..S08 的 8 份 Story 级 CP5 自动预检全部 PASS，阻断项 0，`blocks_lld=true` 未回答项 0，8 份 LLD `open_items=0`。

本轮待人工决策项：5

用户出口目标澄清：CR-030 完成后应支持你开始项目自有多因子研究和本地回测，并输出模拟盘前策略准备包；该出口不表示 simulation-ready、QMT-ready、live-ready、真实可交易或已授权真实模拟盘运行。

如果你回复 approve，表示你接受以下 5 项推荐方案，并允许 CR-030 在 CP5 通过后进入 story-execution 的受控实现阶段；不表示授权以下 8 类不授权项。CP5 approve 不等于 CP8 终验授权，`auto_final_authorization: false`。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP5-CR030-01 | implementation | 是否接受 CR030-S01..S08 八份 LLD 和 8/8 CP5 PASS 作为后续受控实现输入？ | 接受全量 LLD 批次；CP5 后仅允许按 LLD 文件所有权、dev_gate 和 no-real-operation 边界进行受控实现；实现出口包含多因子研究、本地回测和模拟盘前策略准备包。 | 指定 Story 修改后重发 CP5；或拆成三个 CP5 子批次。 | 推荐方案保持闭环一致；修改更稳但延迟；拆批增加版本漂移。 | 影响多因子闭环、回测和准入准备包实现启动条件。 | 任一 LLD 需改时回退对应 LLD；拆批则回退 CP4/CP5 批次规划。 |
| DQ-CP5-CR030-02 | architecture | 是否接受当前 DAG 与 merge order？ | 接受 S01 -> S02 -> S03 -> S04 -> S05/S06 -> S07 -> S08；S03 file conflict 后续串行判定。 | 全串行；或仅 S01/S02 先实现。 | 推荐方案兼顾效率和冲突控制；全串行慢；只做 S01/S02 无法交付闭环。 | 影响实现波次、文件 owner、dev_ready 判定。 | 共享 owner 冲突时移入 blocked_by_dependency 或串行队列。 |
| DQ-CP5-CR030-03 | follow_up_tracking | 是否接受 CR-026 / optimizer / 外部 runtime 后置？ | 接受后置；CR-030 P0 只交付项目自有多因子研究闭环、可解释组合和内部 catalog truth。 | 合并 CR-026；或删除外部 runtime 后续项。 | 推荐方案避免双 truth 和依赖扩散；合并会扩大权限；删除会丢失后续路线。 | 影响后续 backlog、依赖治理和运行授权。 | 合同冻结且用户单独授权后另起 CR-026 / Spike。 |
| DQ-CP5-CR030-04 | runtime_authorization | CP5 通过后是否仍不授权真实外部运行、交易类操作和凭据读取？ | 确认不授权；CP5 仅授权 LLD 指定的本项目受控实现、测试和文档变更。 | 单独发起 dependency/runtime Spike；或另起 QMT route CR / per-run authorization。 | 推荐方案符合阶段门控；Spike 可获得证据但需额外门控；QMT route 风险更高。 | 防止 approve 被误读为真实运行、交易、凭据或 publish 授权。 | 任一真实操作需求出现时停止当前实现路线，转独立授权。 |
| DQ-CP5-CR030-05 | risk_acceptance | 是否接受静态 LLD 和 CP5 自动预检作为进入受控实现的充分设计证据？ | 接受；无阻断澄清，OPEN / Spike 作为非阻断后续项记录。 | 实现前补外部 runtime Spike；或删除 OPEN / Spike 再批准。 | 推荐方案可推进 P0；runtime Spike 会扩大权限；删除 OPEN 会损失追踪。 | 残余风险是外部 runtime 细节未验证。 | 实现发现自有合同不足时回退对应 Story 或启动 Spike。 |

不授权项：

| 不授权 ID | 操作类别 |
|---|---|
| NA-CP5-CR030-01 | 修改 `pyproject.toml` / `uv.lock` 或安装 Qlib / Alphalens / vectorbt / PyBroker / bt / Zipline Reloaded / QuantConnect LEAN / RQAlpha / vn.py / Backtrader |
| NA-CP5-CR030-02 | clone / install / run 外部项目、qrun、Notebook、外部 runner、外部 provider、外部样例或外部测试 |
| NA-CP5-CR030-03 | 复制、裁剪、改写、vendor、fork 或源码级迁移外部项目源码 / 样例 / 测试 / 数据 |
| NA-CP5-CR030-04 | provider fetch、真实联网补数、真实 lake write、catalog publish、broker lake write、reports overwrite |
| NA-CP5-CR030-05 | QMT / MiniQMT / XtQuant、gateway 启动、端口绑定、simulation、live_readonly、small_live、scale_up |
| NA-CP5-CR030-06 | 发单、撤单、账户查询、账户写操作、broker 操作、生成真实 broker order |
| NA-CP5-CR030-07 | 读取、打印、记录或保存 `.env`、token、session、cookie、交易密码、私钥、账户配置或任何凭据 |
| NA-CP5-CR030-08 | 将 HLD、LLD、因子评价、多因子组合、StrategyAdmissionPackage 或 `order_intent_draft_v1` 声明为 QMT-ready、simulation-ready、live-ready、production truth 或真实可交易证据 |

推荐回复：

approve

修改: <具体修改点>

reject
