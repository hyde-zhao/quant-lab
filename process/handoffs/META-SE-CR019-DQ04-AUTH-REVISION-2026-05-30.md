---
handoff_id: "META-SE-CR019-DQ04-AUTH-REVISION-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-se"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "solution-design"
created_at: "2026-05-30T17:44:36+08:00"
status: "agent_completed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "multi_agent_v1.resume_agent / multi_agent_v1.send_input"
  agent_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  agent_name: "se-wei"
  thread_id: "019e782a-2097-7112-a0da-9f0a692a06fd"
  spawned_at: "2026-05-30T17:14:51+08:00"
  resumed_at: "2026-05-30T17:44:36+08:00"
  completed_at: "2026-05-30T17:54:01+08:00"
  evidence: "resume_agent returned status=pending_init; send_input requested DQ-04 pairing token/HMAC revision; close_agent previous_status returned completed DQ-04 revision with CP3 auto PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-se"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-HLD-ADR-DQ04-REVISION"
  wave_id: "CR019-G2-CP3-R1"
---

# META-SE CR-019 DQ-04 鉴权修订交接

## 任务

用户在 CP3 人工审查中选择 `None of the above` 并提出三个澄清问题；meta-po 已解释 `signed file drop`、完整 QMT endpoint matrix 与运行门控分离，以及 token/HMAC 鉴权。随后用户确认将 DQ-04 修订为“配对式 token/HMAC 默认启用”。

请以 `meta-se` 身份仅修订 CR-019 CP3 设计产物，不进入 Story Plan、LLD、代码实现、依赖变更、服务启动或真实 QMT 操作。

## 必读输入

| 文件 | 用途 |
|---|---|
| `checkpoints/CP3-CR019-HLD-REVIEW.md` | 当前 CP3 Decision Brief，需修订 DQ-04 |
| `process/HLD.md` | 当前 CR-019 HLD §33，需修订鉴权 / 安全部署 / 场景模拟相关文字 |
| `process/HLD-QMT-TRADING.md` | QMT companion HLD §17，需同步 token/HMAC pairing 默认值 |
| `process/ARCHITECTURE-DECISION.md` | ADR-071 / AD-Q68 需修订 |
| `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md` | 需追加用户 CP3 澄清与 DQ-04 修订记录 |
| `process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json` | 需更新恢复点中的 DQ-04 / AGA-CR019-04 |
| `process/checks/CP3-CR019-HLD-CONSISTENCY.md` | 需更新自动预检时间、结论仍 PASS 时保持 PASS，并反映 DQ-04 修订 |

## 用户确认的 DQ-04 新推荐方案

受控局域网默认启用轻量配对式 token/HMAC；no-auth 仅作为本机 debug / fixture 测试 / 明确配置的临时模式。鉴权只解决“谁能调用网关”，真实交易仍必须经过 run mode、stage gate、risk gate、kill-switch 和 per-run authorization。

推荐配对流程：

1. C 侧执行 `local-backtest qmt pair request --server http://<windows-host>:<port> --client-name <name>`。
2. S 侧 Windows gateway 记录 pending request，包含 `request_id`、client name、来源 IP、机器指纹摘要、创建时间和过期时间。
3. S 侧管理员执行 `qmt-gateway pair list` 查看请求。
4. S 侧管理员执行 `qmt-gateway pair approve <request_id>` 批准请求。
5. S 侧生成 client id + secret，并显示一次性 pairing code，或在短 TTL 内允许 C 侧完成领取。
6. C 侧执行 `local-backtest qmt pair complete --request-id <id> --code <code>`。
7. 后续请求携带 `X-QMT-Client-Id`、`X-QMT-Timestamp`、`X-QMT-Nonce`、`X-QMT-Signature`。
8. 签名建议为 `HMAC_SHA256(secret, method + path + body_hash + timestamp + nonce)`。
9. S 侧校验 approved client、timestamp 偏移、nonce replay 和 scope。
10. HMAC 通过后仍继续执行 run gate、risk gate、kill-switch 和 per-run authorization。

## 目标输出

请最小化修改以下文件：

1. `process/HLD.md`
2. `process/HLD-QMT-TRADING.md`
3. `process/ARCHITECTURE-DECISION.md`
4. `process/discussions/CP3-CR019-HLD-DISCUSSION-LOG.md`
5. `process/checks/CP3-CR019-DISCUSSION-CHECKPOINT.json`
6. `process/checks/CP3-CR019-HLD-CONSISTENCY.md`
7. `checkpoints/CP3-CR019-HLD-REVIEW.md`

## 验收要求

- DQ-04 的推荐方案、备选方案、优劣分析、影响 / 风险、切换条件均改为“配对式 token/HMAC 默认启用”。
- no-auth 不再作为默认推荐，只能作为 debug / fixture / 显式临时模式。
- 说明 token/HMAC 鉴权不替代运行门控。
- CP3 自动预检仍须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables。
- CP3 仍为 pending 人工审查；不得回填用户 approved。
- 不得创建 Story Plan、LLD、Story 卡片或代码实现。
- 不得读取凭据、`.env`、账户、session，且不得调用真实 QMT / MiniQMT / XtQuant。
