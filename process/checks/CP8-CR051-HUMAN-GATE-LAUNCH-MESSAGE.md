请审查：`process/checkpoints/CP8-CR051-DELIVERY-READINESS.md`

自动预检结论：PASS

Context Capsule 摘要：`process/release/RELEASE-CONTEXT-CR051.yaml`（read_profile=compact，release_decision=READY，完整来源见 checklist）

本轮待人工决策项：0

决策收集覆盖：已扫描 6 个来源，发现候选问题 16 个，纳入待决策 0 个；原因是 CR051 CP2 / CP3 / CP5 已 approved，CP7 PASS_WITH_RISK=0，CP8 release_decision=READY，且后续 CR052..CR056 仍只是候选路线。

如果你回复 approve，表示你接受 CR051 当前交付 READY，不表示授权以下 9 类禁止操作。

待人工决策清单：本轮无新增待人工决策项。

不授权项：
- 目录重命名 / 远端仓库改名。
- git push / tag publish / 重写历史。
- NAS scan / mount / copy / delete / migration。
- external archive migration execution。
- provider fetch / lake write / catalog publish。
- QMT / MiniQMT import / connection / runtime。
- `.env`、token、account_id、账号、密码、session、cookie、private key 读取。
- submit / cancel / simulation / live trading。
- 启动 CR052..CR056。

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受 CR051 当前交付 READY；如需调整，请用 `修改: <具体修改点>` 指明文件和修改内容。

审查后请在“人工审查结果”中填写结论，也可以直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```
