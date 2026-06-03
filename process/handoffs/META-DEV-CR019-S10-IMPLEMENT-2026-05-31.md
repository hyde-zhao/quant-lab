---
handoff_id: "META-DEV-CR019-S10-IMPLEMENT-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S10-docs-runbook-user-manual-boundary"
wave_id: "CR019-W5-DOCS-RUNBOOK"
status: "completed-closed"
created_at: "2026-05-31T09:54:01+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7bbd-ebb5-74a3-8745-f3dc74cfc1f0"
  agent_name: "dev-qin"
  thread_id: "019e7bbd-ebb5-74a3-8745-f3dc74cfc1f0"
  spawned_at: "2026-05-31T09:55:07+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T10:04:36+08:00"
  closed_at: "2026-05-31T10:10:20+08:00"
  evidence: "spawn_agent returned agent_id=019e7bbd-ebb5-74a3-8745-f3dc74cfc1f0 nickname=dev-qin; wait_agent returned completed CR019-S10 CP6 PASS; close_agent previous_status returned completed CR019-S10 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S10-docs-runbook-user-manual-boundary"
  wave_id: "CR019-W5-DOCS-RUNBOOK"
---

# META-DEV CR-019 S10 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S10-docs-runbook-user-manual-boundary`。当前 S01..S09 均已 verified，S10 的 LLD 与 CP5 已批准。本轮只允许受控离线 / 静态文档 / 文档边界测试实现，目标是把 CR019 的 admission、QMT C/S bridge、pairing/HMAC、endpoint/gate/fallback、deferred capabilities 和 no-real-operation 边界收敛到用户可读文档。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。若目标文件已有变更，先读懂并在其上增量修改。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S10-docs-runbook-user-manual-boundary.md` |
| LLD | `process/stories/CR019-S10-docs-runbook-user-manual-boundary-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S10-docs-runbook-user-manual-boundary-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| Upstream S01-S09 Stories | `process/stories/CR019-S01-*.md` through `process/stories/CR019-S09-*.md` |
| Upstream S01-S09 LLDs | `process/stories/CR019-S01-*-LLD.md` through `process/stories/CR019-S09-*-LLD.md` |
| Upstream S01-S09 CP7 | `process/checks/CP7-CR019-S01-*.md` through `process/checks/CP7-CR019-S09-*.md` |
| Existing docs | `README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md` |
| S09 register | `docs/CR019-DEFERRED-CAPABILITIES.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| docs | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | 创建 CR019 C/S bridge runbook，覆盖 DQ、Story、no-real-operation、pairing/HMAC、endpoint/gate/fallback 和 deferred register 引用。 |
| docs | `README.md` | 仅增量加入阶段六 admission 与 QMT C/S bridge 用户入口边界；不得覆盖既有 CR015/CR016/CR017/CR018/CR019 内容。 |
| docs | `docs/USER-MANUAL.md` | 仅增量加入用户操作边界、真实授权禁区和后续 CR / CP 入口。 |
| docs | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 增量对齐 CR019 gateway / run gate / no-real-operation 说明；不得授权 simulation/live。 |
| docs | `docs/QMT-INCIDENT-PLAYBOOK.md` | 增量对齐 S08 fail-closed fallback、manual dry-run / signed file drop 边界。 |
| test | `tests/test_cr019_docs_runbook_boundary.py` | 创建静态文档边界测试。 |
| process | `process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `process/stories/CR019-S10-docs-runbook-user-manual-boundary.md` | 仅更新本 Story 的实现状态、CP6 结果和 agent 证据字段。 |

禁止修改：`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、其他 Story 卡片、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值、`delivery/**`。

## 必须实现

1. `docs/QMT-C-S-BRIDGE-RUNBOOK.md` 包含 authorization boundary，明确文档、runbook、Story verified、CP5/CP6/CP7 都不授权真实交易。
2. runbook 覆盖 `CP3-CR019-DQ-01` 至 `CP3-CR019-DQ-07` 共 7 个决策，每项说明 accepted recommendation、user impact、not authorization。
3. runbook 覆盖 `CR019-S01` 至 `CR019-S10` 共 10 个 Story 边界，每项说明 scope、output surface、forbidden operation、verification entry。
4. no-real-operation 表覆盖 8 类禁止项：dependency change、service start、credential read、QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake、publish、simulation/live。
5. README、USER-MANUAL、QMT-SIMULATION-LIVE-RUNBOOK、QMT-INCIDENT-PLAYBOOK 增量均不得写成真实运行、真实账户查询、真实发单 / 撤单、真实 broker lake 写入、publish 或 simulation/live 已授权。
6. 静态测试验证 DQ 覆盖、Story 覆盖、8 类禁止项、敏感值示例为 0、真实授权误读语义为 0。
7. `pyproject.toml` / `uv.lock` 修改次数必须为 0；不得读取 `.env` 内容。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s10-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile tests/test_cr019_docs_runbook_boundary.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_docs_runbook_boundary.py tests/test_cr019_deferred_capabilities.py tests/test_cr019_qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_run_gates.py
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
rg -n -i "runbook.*(authori[sz]es|授权).*(real trade|真实交易|实盘)|story verified.*(authori[sz]es|授权)|cp[567].*(authori[sz]es|授权).*(real|真实)|默认授权|实盘授权|已授权真实|真实凭据|token=|password=|secret=|private key|account_id=[0-9]" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n "provider_uri|level2 entitlement|Level2 entitlement|minute fetch|fetch_minute|qlib.init|D.features|pip install|uv add|poetry add|conda install|backtrader==|qlib==|xtquant\\.|XtQuant" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\\.remove|shutil\\.rmtree|subprocess|Popen|eval\\(|exec\\(" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
git diff --check -- docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py process/stories/CR019-S10-docs-runbook-user-manual-boundary.md process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md
```

若目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md`

完成后请回复：

- 修改文件列表
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- 依赖 / 锁文件 / `.env` 是否保持未修改
- 是否确认真实操作计数均为 0
