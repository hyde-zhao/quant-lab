---
handoff_id: "META-QA-CR019-S10-CP7-VERIFY-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S10-docs-runbook-user-manual-boundary"
wave_id: "CR019-W5-DOCS-RUNBOOK"
status: "completed-closed"
created_at: "2026-05-31T10:14:37+08:00"
dispatch:
  required: true
  semantic: "story-cp7-verification"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7bd0-f92b-7550-be16-3a8fe67f77de"
  agent_name: "qa-kong"
  thread_id: "019e7bd0-f92b-7550-be16-3a8fe67f77de"
  spawned_at: "2026-05-31T10:15:57+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T10:18:14+08:00"
  closed_at: "2026-05-31T10:21:33+08:00"
  evidence: "spawn_agent returned agent_id=019e7bd0-f92b-7550-be16-3a8fe67f77de nickname=qa-kong; wait_agent returned completed CR019-S10 CP7 PASS; close_agent previous_status returned completed CR019-S10 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S10-docs-runbook-user-manual-boundary"
  wave_id: "CR019-W5-DOCS-RUNBOOK"
---

# META-QA CR-019 S10 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S10-docs-runbook-user-manual-boundary`。S10 的 CP6 已 PASS，主线程已复跑离线验证并 PASS。你的目标是独立生成 CP7 验证结果，确认 QMT C/S bridge runbook、README、USER-MANUAL、simulation/live runbook 和 incident playbook 只描述受控文档边界、后续 CR / CP 入口和禁止真实操作约束，不把文档、Story verified、CP5/CP6/CP7 或 runbook 解释为真实 QMT / simulation / live / broker 操作授权。

本轮仍是受控离线 / fixture / dry-run 合同验证。不得启动服务，不得读取 `.env` / secret / 凭据，不得调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker lake / publish / simulation / live，不得安装依赖或修改锁文件。

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
| CP6 | `process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S10-IMPLEMENT-2026-05-31.md` |
| C/S bridge runbook | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` |
| README | `README.md` |
| USER-MANUAL | `docs/USER-MANUAL.md` |
| Simulation/live runbook | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` |
| Incident playbook | `docs/QMT-INCIDENT-PLAYBOOK.md` |
| Static tests | `tests/test_cr019_docs_runbook_boundary.py` |
| Upstream register tests | `tests/test_cr019_deferred_capabilities.py` |
| Upstream fallback tests | `tests/test_cr019_qmt_gateway_fallback.py` |
| Upstream run gate tests | `tests/test_cr019_qmt_gateway_run_gates.py` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S10-docs-runbook-user-manual-boundary-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果，必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、Validation Results、BLOCKING / REQUIRED / OPEN / WAIVED。 |

禁止修改：代码、README、docs、测试、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工稿、依赖/锁文件、`.env`、`delivery/**`、凭据或 secret 值。若发现必须修改才能通过，应在 CP7 标记 FAIL/BLOCKED，并说明 REQUIRED fix，不要自行修代码或文档。

## 必验内容

1. `docs/QMT-C-S-BRIDGE-RUNBOOK.md` 必须覆盖 CP3 DQ-01..DQ-07 共 7 个决策，且每项明确 accepted recommendation、user impact 和 not authorization。
2. runbook 必须覆盖 CR019-S01..S10 共 10 个 Story 边界，且每项至少包含 scope、output surface、forbidden operation、verification entry。
3. no-real-operation 表必须覆盖 dependency change、service start、credential read、QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake、publish、simulation/live 共 8 类禁止项。
4. README / USER-MANUAL / QMT-SIMULATION-LIVE-RUNBOOK / QMT-INCIDENT-PLAYBOOK 只能作为用户入口、操作边界、per-run authorization 提醒和 incident fail-closed 路由，不得释放真实运行许可。
5. 文档不得包含真实 token、password、cookie、session、private key、账户号、broker secret、真实 provider URI 或真实 QMT 地址示例。
6. “runbook / Story verified / CP5 / CP6 / CP7 已授权真实交易、simulation/live、账户查询、发单、撤单、broker lake 写入或 publish”这类肯定语义匹配次数必须为 0。
7. `pyproject.toml` / `uv.lock` / `.env` 必须保持未修改；不得读取 `.env` 内容。
8. 本 CP7 不得启动服务、绑定端口、调用 socket、访问 QMT / MiniQMT / XtQuant、执行 provider fetch、写 lake / broker lake、publish 或运行 simulation/live。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s10-qa-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile tests/test_cr019_docs_runbook_boundary.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_docs_runbook_boundary.py tests/test_cr019_deferred_capabilities.py tests/test_cr019_qmt_gateway_fallback.py tests/test_cr019_qmt_gateway_run_gates.py
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
rg -n -i "secret|password|passwd|token|api[_-]?key|private key|cookie|session|credential|account id|broker secret|授权真实|真实授权|可直接实盘|自动实盘|自动交易|runbook.*授权|verified.*授权|无需.*授权" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n "provider_uri|level2 entitlement|Level2 entitlement|minute fetch|fetch_minute|qlib.init|D.features|pip install|uv add|poetry add|conda install|backtrader==|qlib==" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\.remove|shutil\.rmtree|subprocess|Popen|eval\(|exec\(" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py
git diff --check -- docs/QMT-C-S-BRIDGE-RUNBOOK.md README.md docs/USER-MANUAL.md docs/QMT-SIMULATION-LIVE-RUNBOOK.md docs/QMT-INCIDENT-PLAYBOOK.md tests/test_cr019_docs_runbook_boundary.py process/checks/CP7-CR019-S10-docs-runbook-user-manual-boundary-VERIFICATION-DONE.md process/handoffs/META-QA-CR019-S10-CP7-VERIFY-2026-05-31.md
```

若 S10 文档、测试、handoff 或 CP7 文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 宽泛扫描解释要求

`sensitive / permission` scan 可能命中文档中“禁止真实授权”的否定语义、`TUSHARE_TOKEN=<...>` / `JQDATA_PASSWORD=<...>` 这类占位示例、denylist 字段名或空 token smoke；不要仅因这些预期命中判 FAIL，必须结合 S10 pytest 中真实敏感值示例计数和肯定式真实许可误读计数判断。若发现真实值、真实地址、真实账户、肯定式真实授权或自动实盘语义，则标记 BLOCKING。

`dangerous command` scan 可能因 `nc ` 子串命中 `sync `；若命中仅为 README / USER-MANUAL 既有 `uv sync` 环境准备示例，应记录为 REVIEWED，而不是 blocking。若出现破坏性命令、服务控制、shell 执行、远程访问或进程终止命令，则标记 BLOCKING。

## 期望输出

生成：

- `process/checks/CP7-CR019-S10-docs-runbook-user-manual-boundary-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN / WAIVED
- 是否确认依赖 / 锁文件 / `.env` 未修改且未读取凭据
- 是否确认真实操作计数均为 0
