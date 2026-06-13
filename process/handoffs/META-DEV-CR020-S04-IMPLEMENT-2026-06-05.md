---
handoff_id: "META-DEV-CR020-S04-IMPLEMENT-2026-06-05"
from: "meta-po"
to: "meta-dev"
change_id: "CR-020"
story_ids:
  - "CR020-S04-hmac-pairing-allowlist-scope"
phase: "story-execution"
status: "dispatched"
created_at: "2026-06-05T08:25:46+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e952d-161f-7063-94e6-22557c687643"
  agent_name: "dev-you"
  thread_id: "019e952d-161f-7063-94e6-22557c687643"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-05T08:25:46+08:00"
  completed_at: ""
  closed_at: ""
---

# Handoff: CR-020 S04 实现

## Scope

- 修改 `trading/qmt_auth.py`
- 修改 `trading/qmt_redaction.py`
- 创建 `tests/test_cr020_hmac_pairing_allowlist_scope.py`

## Guardrails

- 不修改 `pyproject.toml` / `uv.lock`。
- 不读取真实 `.env` / `.env.*`。
- 不启动 gateway、不绑定端口、不打开 socket。
- 不连接 QMT / MiniQMT / XtQuant。
- HMAC pass 只表示调用方识别与 scope 通过，不授权交易、账户写入、simulation/live 或 QMT 扩大调用。

