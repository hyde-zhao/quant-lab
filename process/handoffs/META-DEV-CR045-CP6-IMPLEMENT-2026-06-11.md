---
handoff_id: "META-DEV-CR045-CP6-IMPLEMENT-2026-06-11"
from_agent: "meta-po"
to_agent: "meta-dev"
change_id: "CR-045"
phase: "story-execution"
batch_id: "CR045-BRIDGE-BATCH-A"
status: "completed"
created_at: "2026-06-11T23:16:11+08:00"
context_capsule: "process/context/CP6-CR045-IMPLEMENTATION-CONTEXT.yaml"
dispatch:
  mode: "spawn_agent"
  agent_id: "019eb748-a3bf-75d3-b37c-ce4ba4924235"
  agent_name: "dev-zhu"
  thread_id: "019eb748-a3bf-75d3-b37c-ce4ba4924235"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-11T23:16:11+08:00"
  completed_at: "2026-06-11T23:30:08+08:00"
  fallback_reason: ""
---

# META-DEV CR045 CP6 Implementation Handoff

## 任务

把已通过 CP5 的 CR045 Bridge Batch A 设计证据实现为 L2 skeleton / fixture / static / runbook 工程资产，并输出 CP6 实现证据。

## 必读输入

| 类型 | 路径 |
|---|---|
| CP6 context | `process/context/CP6-CR045-IMPLEMENTATION-CONTEXT.yaml` |
| CP5 checkpoint | `process/checkpoints/CP5-CR045-BRIDGE-BATCH-A-LLD-BATCH.md` |
| Feature design | `docs/features/cr045-goldminer-bridge/DESIGN.md` |
| Feature test plan | `docs/features/cr045-goldminer-bridge/TEST-PLAN.md` |
| Feature tasks | `docs/features/cr045-goldminer-bridge/TASKS.md` |
| Story cards / LLD | `process/stories/CR045-S01..S06*` |

## 允许实现范围

- 新增 / 修改 L2 skeleton、fixture response、static validation 和 runbook。
- 使用 Python 3.11 + `uv run`。
- 默认 `max_parallel_dev=1`，按 S01 -> S02 -> S03 -> S04 -> S05 -> S06 合并。

## 禁止范围

- 不读取 `.env`、`.env.*`、token、account_id、账号、密码、session、cookie、private key。
- 不启动 Windows bridge runtime。
- 不导入或调用真实 `gm` / `gmtrade` runtime。
- 不登录 / 连接 Goldminer 或 broker。
- 不查询账户 / cash / position / order / fill。
- 不下单、撤单、启动 simulation/live、provider fetch、lake write、catalog publish。

## 预期输出

| 输出 | 路径 |
|---|---|
| bridge contract | `engine/goldminer_bridge_contract.py` |
| bridge client | `engine/goldminer_bridge_client.py` |
| readonly probe | `engine/goldminer_bridge_probe.py` |
| contract tests | `tests/test_cr045_goldminer_bridge_contract.py` |
| client tests | `tests/test_cr045_goldminer_bridge_client.py` |
| readonly probe tests | `tests/test_cr045_goldminer_readonly_probe.py` |
| no-operation static tests | `tests/test_cr045_goldminer_no_operation_static.py` |
| runbook | `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` |
| implementation evidence | `process/stories/CR045-BRIDGE-BATCH-A-IMPLEMENTATION.md` |
| CP6 check | `process/checks/CP6-CR045-BRIDGE-BATCH-A-CODING-DONE.md` |

## 验证要求

优先运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py tests/test_cr045_goldminer_bridge_client.py tests/test_cr045_goldminer_readonly_probe.py tests/test_cr045_goldminer_no_operation_static.py
git diff --check
```

无法运行的验证必须在实现证据和 CP6 检查中说明原因。
