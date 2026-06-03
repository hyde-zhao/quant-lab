---
handoff_id: "META-QA-CR019-S09-CP7-VERIFY-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-qa"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S09-deferred-capability-register"
wave_id: "CR019-W4-FALLBACK-DEFERRED"
status: "completed-closed"
created_at: "2026-05-31T09:42:09+08:00"
dispatch:
  required: true
  semantic: "story-cp7-verification"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7bb2-d91e-7513-8a5e-a16a0e6528c9"
  agent_name: "qa-he"
  thread_id: "019e7bb2-d91e-7513-8a5e-a16a0e6528c9"
  spawned_at: "2026-05-31T09:43:03+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T09:45:23+08:00"
  closed_at: "2026-05-31T09:50:40+08:00"
  evidence: "spawn_agent returned agent_id=019e7bb2-d91e-7513-8a5e-a16a0e6528c9 nickname=qa-he; wait_agent returned completed CR019-S09 CP7 PASS; close_agent previous_status returned completed CR019-S09 CP7 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-qa"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S09-deferred-capability-register"
  wave_id: "CR019-W4-FALLBACK-DEFERRED"
---

# META-QA CR-019 S09 CP7 Verification Handoff

## 任务

请以 `meta-qa` 身份验证 `CR019-S09-deferred-capability-register`。S09 的 CP6 已 PASS，主线程已复跑离线验证并 PASS。你的目标是独立生成 CP7 验证结果，确认 deferred capability register 只登记 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的后置能力边界，不把这些能力加入阶段六 P0 admission 或 QMT C/S bridge 默认实现范围。

本轮仍是受控离线 / fixture / dry-run 合同验证。不得启动服务，不得读取 `.env` / secret / 凭据，不得调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker lake / publish / simulation / live。

## 必读输入

| 类型 | 路径 |
|---|---|
| 项目规则 | `AGENTS.md` |
| 工作流状态 | `process/STATE.md` |
| Story 汇总 | `process/STORY-STATUS.md` |
| Story | `process/stories/CR019-S09-deferred-capability-register.md` |
| LLD | `process/stories/CR019-S09-deferred-capability-register-LLD.md` |
| CP5 auto | `process/checks/CP5-CR019-S09-deferred-capability-register-LLD-IMPLEMENTABILITY.md` |
| CP5 manual | `checkpoints/CP5-CR019-STAGE6-QMT-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 | `process/checks/CP6-CR019-S09-deferred-capability-register-CODING-DONE.md` |
| Dev handoff | `process/handoffs/META-DEV-CR019-S09-IMPLEMENT-2026-05-31.md` |
| Deferred capability register | `docs/CR019-DEFERRED-CAPABILITIES.md` |
| Static tests | `tests/test_cr019_deferred_capabilities.py` |
| README | `README.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| process | `process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md` | 写入 CP7 验证完成检查结果，必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、Validation Results、BLOCKING / REQUIRED / OPEN / WAIVED。 |

禁止修改：代码、README、docs register、测试、Story 卡片、`process/STATE.md`、`process/STORY-STATUS.md`、依赖/锁文件、`.env`、凭据或 secret 值。若发现必须修改才能通过，应在 CP7 标记 FAIL/BLOCKED，并说明 REQUIRED fix，不要自行修代码。

## 必验内容

1. register 必须且只包含 `backtrader_w6`、`qlib_w7`、`minute_spike`、`level2_spike` 四类后置能力。
2. 每条 entry 必须有 current status、non-P0 reason、至少 2 个 trigger conditions、blocked reason、required evidence、next CR / CP entry、forbidden claims、revisit condition。
3. README 只能声明 deferred / later-gated / non-P0 边界，不得写成当前已启用、默认授权或阶段六 P0 依赖。
4. Stage 6 P0 dependency additions、QMT C/S bridge dependency additions、real operation permission claims 必须为 0。
5. 不得出现真实 Qlib provider URI、Level2 entitlement、minute fetch、依赖添加命令或真实 runtime init。
6. `pyproject.toml` / `uv.lock` / `.env` 必须保持未修改；不得读取 `.env` 内容。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s09-qa-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile tests/test_cr019_deferred_capabilities.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_deferred_capabilities.py tests/test_cr019_stage6_admission_gate.py tests/test_cr019_primary_benchmark_policy.py
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
rg -n "provider_uri|level2 entitlement|Level2 entitlement|minute fetch|fetch_minute|qlib.init|D.features|pip install|uv add|poetry add|conda install|backtrader==|qlib==" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n -i "enabled by default|default enabled|already enabled|authorized for live|current P0 dependency|当前已启用|默认启用|默认授权|实盘授权|P0 默认依赖" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\.remove|shutil\.rmtree|subprocess|Popen|eval\(|exec\(" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
git diff --check -- docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md process/handoffs/META-QA-CR019-S09-CP7-VERIFY-2026-05-31.md
```

若 `docs/CR019-DEFERRED-CAPABILITIES.md`、`tests/test_cr019_deferred_capabilities.py` 或 CP7 文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP7 中说明退出码 1 只是文件差异预期。

## 期望输出

生成：

- `process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md`

完成后请回复：

- CP7 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN / WAIVED
- 是否确认依赖 / 锁文件 / `.env` 未修改且未读取凭据
- 是否确认真实操作计数均为 0
