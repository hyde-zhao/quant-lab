---
handoff_id: "META-DEV-CR019-S03-IMPLEMENT-2026-05-30"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
created_at: "2026-05-30T19:56:10+08:00"
status: "completed-closed"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent / multi_agent_v1.close_agent"
  agent_id: "019e78be-613b-7783-bca1-b48ef8e38365"
  agent_name: "dev-qin"
  thread_id: "019e78be-613b-7783-bca1-b48ef8e38365"
  spawned_at: "2026-05-30T19:56:46+08:00"
  resumed_at: ""
  completed_at: "2026-05-30T20:04:42+08:00"
  closed_at: "2026-05-30T20:10:44+08:00"
  evidence: "spawn_agent returned agent_id=019e78be-613b-7783-bca1-b48ef8e38365 nickname=dev-qin; close_agent previous_status returned completed S03 implementation with CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S03-qmt-cside-client-cli-contract"
  wave_id: "CR019-W2-CS-TRANSPORT"
---

# META-DEV CR-019 S03 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S03-qmt-cside-client-cli-contract`。当前 CR019-S01 / S02 均已通过 CP6 / CP7 并收敛为 `verified`，S03 Story 卡片为 `dev-ready`。本次只允许受控离线 / fixture / dry-run 合同实现，不授权任何真实 QMT / provider / lake / broker / publish / simulation / live 操作。

## 必读输入

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | CP6 / CP7 门控、真实子 agent 证据、禁止真实操作边界 |
| `process/STATE.md` | 当前 CR-019、S03 dev-ready、真实操作禁止范围 |
| `process/STORY-STATUS.md` | S03 dev-ready 与后续 Story gate |
| `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` | CP5 approved 决策与 DQ-01..DQ-07 |
| `process/stories/CR019-S03-qmt-cside-client-cli-contract.md` | Story 卡片、文件 owner、dev_gate |
| `process/stories/CR019-S03-qmt-cside-client-cli-contract-LLD.md` | S03 approved LLD，必须按第 4 / 6 / 10 / 11 / 14 节实现 |
| `process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md` | CR015-S02 adapter contract verified 证据 |
| `process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md` | CR016-S04 runbook / approval gate verified 证据 |
| `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` | S01 已 verified 的依赖证据 |
| `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` | S02 已 verified 的依赖证据 |
| `trading/qmt_transport.py` | CR015 signed file-drop transport 合同；本 Story 只能兼容性扩展 REST gateway contract |

## 允许写入范围

| 类型 | 路径 |
|---|---|
| 创建 | `trading/qmt_client.py` |
| 创建 | `trading/qmt_cli.py` |
| 修改 | `trading/qmt_transport.py`，仅允许增加 REST gateway transport enum / payload metadata / error contract，必须保持既有 CR015 file-drop 语义兼容 |
| 创建 | `tests/test_cr019_qmt_cside_client_cli.py` |
| 创建 | `process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md` |
| 可修改 | `process/stories/CR019-S03-qmt-cside-client-cli-contract.md`，仅允许将状态推进到 `ready-for-verification` 并记录 CP6 证据 |

## 禁止事项

- 不得修改 `pyproject.toml`、`uv.lock`、`.env` 或任何凭据文件。
- 不得导入 `xtquant`，不得调用 QMT / MiniQMT / XtQuant，C 侧 `xtquant` import 次数必须为 0。
- 不得启动服务、绑定端口、打开 socket、引入 HTTP 客户端依赖或访问真实 Windows gateway。
- 不得读取账户、发单、撤单、查询真实账户、读取 token / secret / cookie / session / 私钥。
- 不得执行 provider fetch、lake write、broker lake write、publish、current pointer publish、simulation/live run。
- 不得修改 HLD、ADR、REQUIREMENTS、STORY-BACKLOG、DEVELOPMENT-PLAN、STATE、STORY-STATUS 或 CR019-S04..S10 Story。
- 不得让 S03 的 HMAC header slot 替代 S05 配对式 token/HMAC、S07 run gate 或 per-run authorization。

## 实现要求

1. 创建 `trading/qmt_client.py`，至少覆盖：
   - `QmtEndpointCategory`
   - `QmtRequest`
   - `QmtResponse`
   - `QmtBlockedResult`
   - `QmtClientSafetyCounters`
   - `QmtClient`
   - `collect_qmt_client_safety_counters`
   - health、capabilities、validate intent、market query、account-like query、order intent、reconcile、kill switch 等方法
2. 创建 `trading/qmt_cli.py`，至少覆盖：
   - `run_qmt_cli(argv, client_factory=...)`
   - CLI 只解析参数、调用同一 `QmtClient`、格式化 JSON/text 输出和返回退出码
   - 退出码建议：0 ok，2 validation，3 blocked，4 auth，5 transport
3. 修改 `trading/qmt_transport.py`，至少覆盖：
   - REST gateway transport kind / enum 或常量
   - REST gateway payload metadata 字段集合
   - REST transport error / timeout contract
   - 不启动服务、不发网络请求、不改变 CR015 `build_transport_payload` 严格白名单行为
4. 创建 `tests/test_cr019_qmt_cside_client_cli.py`，至少覆盖：
   - C 侧 `xtquant` import 次数为 0
   - CLI 100% 复用 fake client，不复制业务逻辑
   - health / capabilities / query / order intent / simulation-live 请求均有 typed blocked result
   - REST_GATEWAY transport enum / payload metadata 合同存在
   - later-gated endpoint 默认 blocked，real order / cancel / account / QMT counters 全 0

## 建议验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_cside_client_cli.py tests/test_cr015_qmt_adapter_contract.py tests/test_cr019_stage6_admission_gate.py
```

可追加：

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s03-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile trading/qmt_client.py trading/qmt_cli.py trading/qmt_transport.py tests/test_cr019_qmt_cside_client_cli.py
git diff --check -- trading/qmt_client.py trading/qmt_cli.py trading/qmt_transport.py tests/test_cr019_qmt_cside_client_cli.py process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md process/stories/CR019-S03-qmt-cside-client-cli-contract.md
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

## CP6 文件要求

请创建 `process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md`，必须包含：

- Entry Criteria
- Checklist
- Exit Criteria
- Deliverables
- Agent Dispatch Evidence
- Validation Results
- Forbidden Operation Counters
- 写入范围复核
- 结论：`PASS` / `FAIL`

## 完成后回复

请列出：

- 修改文件清单
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否触发任何 forbidden 操作，预期应为 0
- 是否存在 BLOCKING / OPEN 项
