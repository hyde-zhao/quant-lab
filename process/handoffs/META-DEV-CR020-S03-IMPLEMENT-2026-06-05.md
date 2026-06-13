---
handoff_id: "META-DEV-CR020-S03-IMPLEMENT-2026-06-05"
from: "meta-po"
to: "meta-dev"
change_id: "CR-020"
story_ids:
  - "CR020-S03-linux-client-rest-transport"
phase: "story-execution"
status: "dispatched"
created_at: "2026-06-05T08:25:46+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e952d-15d7-7eb0-8c1e-61f86e1e6925"
  agent_name: "dev-zhang"
  thread_id: "019e952d-15d7-7eb0-8c1e-61f86e1e6925"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-05T08:25:46+08:00"
  completed_at: ""
  closed_at: ""
---

# Handoff: CR-020 S03 实现

## Scope

- 修改 `trading/qmt_client.py`
- 创建 `trading/qmt_client_cli.py`
- 创建 `tests/test_cr020_linux_client_rest_transport.py`

## Guardrails

- 不修改 `pyproject.toml` / `uv.lock`。
- 不读取真实 `.env` / `.env.*`。
- 不启动 gateway、不绑定端口、不打开 socket。
- Linux C 端不得导入 XtQuant / MiniQMT / QMT SDK。
- CLI 只做 pairing / diagnostics / validation，不作为业务 runtime；业务 runtime 是 Python REST client。

