---
handoff_id: "META-DEV-CR019-S09-IMPLEMENT-2026-05-31"
from_agent: "meta-po"
to_agent: "meta-dev"
workflow_id: "local_backtest-cr019"
change_id: "CR-019"
phase: "story-execution"
story_id: "CR019-S09-deferred-capability-register"
wave_id: "CR019-W4-FALLBACK-DEFERRED"
status: "completed-closed"
created_at: "2026-05-31T09:23:13+08:00"
dispatch:
  required: true
  semantic: "stage-dispatch"
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "multi_agent_v1.spawn_agent"
  agent_id: "019e7ba4-f915-7df2-9443-99586f4e7676"
  agent_name: "dev-xu"
  thread_id: "019e7ba4-f915-7df2-9443-99586f4e7676"
  spawned_at: "2026-05-31T09:27:52+08:00"
  resumed_at: ""
  completed_at: "2026-05-31T09:34:30+08:00"
  closed_at: "2026-05-31T09:38:44+08:00"
  evidence: "spawn_agent returned agent_id=019e7ba4-f915-7df2-9443-99586f4e7676 nickname=dev-xu; wait_agent returned completed CR019-S09 CP6 PASS; close_agent previous_status returned completed CR019-S09 CP6 PASS"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reuse_key:
  role: "meta-dev"
  workflow_id: "local_backtest-cr019"
  change_id: "CR-019"
  story_id: "CR019-S09-deferred-capability-register"
  wave_id: "CR019-W4-FALLBACK-DEFERRED"
---

# META-DEV CR-019 S09 Implementation Handoff

## 任务

请以 `meta-dev` 身份实现 `CR019-S09-deferred-capability-register`。当前 S01/S02 均已 verified，S08 也已 CP7 PASS 并收敛为 verified。S09 的 LLD 与 CP5 已批准。本轮只允许受控离线 / 静态文档 / register 合同实现，目标是固化 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的后置触发条件、blocked reason 和后续 CR / CP 入口，确保它们不进入阶段六 P0 admission 与 QMT C/S bridge 默认实现范围。

你不是独自在代码库中工作：当前仓库有多批未提交的 CR-015 / CR-016 / CR-017 / CR-018 / CR-019 产物。不要 revert 其他人的修改。若目标文件已有变更，先读懂并在其上增量修改。

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
| Upstream S01 CP7 | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| Upstream S02 CP7 | `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` |
| Deferred capability target | `docs/CR019-DEFERRED-CAPABILITIES.md` |
| README | `README.md` |

## 写入范围

| 类型 | 路径 | 规则 |
|---|---|---|
| docs | `docs/CR019-DEFERRED-CAPABILITIES.md` | 创建四类后置能力 register。 |
| test | `tests/test_cr019_deferred_capabilities.py` | 创建静态 register / README 边界测试。 |
| docs | `README.md` | 仅增量加入 CR019 deferred capability 非 P0 / 非默认授权边界，不改写既有功能说明。 |
| process | `process/checks/CP6-CR019-S09-deferred-capability-register-CODING-DONE.md` | 写入 CP6 编码完成检查结果。 |
| process | `process/stories/CR019-S09-deferred-capability-register.md` | 仅更新本 Story 的实现状态、CP6 结果和 agent 证据字段。 |

禁止修改：`process/STATE.md`、`process/STORY-STATUS.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-BACKLOG.md`、HLD / ADR / CP5 人工审查稿、其他 Story 卡片、`pyproject.toml`、`uv.lock`、`.env`、凭据或 secret 值。

## 必须实现

1. `docs/CR019-DEFERRED-CAPABILITIES.md` 包含 `backtrader_w6`、`qlib_w7`、`minute_spike`、`level2_spike` 四条 entry。
2. 每条 entry 必须包含：当前状态、非 P0 原因、至少 2 个触发条件、blocked reason、required evidence、next CR / CP entry、forbidden claims、revisit condition。
3. README 增量只说明这些能力为 deferred / later-gated / non-P0，不得写成当前已启用能力或默认授权能力。
4. 测试验证四类能力齐全、字段完整、禁止项存在、阶段六 P0 依赖新增次数为 0。
5. `pyproject.toml` / `uv.lock` 修改次数必须为 0。
6. 不写 Qlib provider URI，不声明 Level2 entitlement，不写 minute data fetch 配置，不新增依赖，不连接 Qlib provider。

## 必跑命令

```bash
PYTHONPYCACHEPREFIX=/tmp/cr019-s09-pycompile PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile tests/test_cr019_deferred_capabilities.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_deferred_capabilities.py tests/test_cr019_stage6_admission_gate.py tests/test_cr019_primary_benchmark_policy.py
git diff --name-only -- pyproject.toml uv.lock .env
git status --short -- .pytest_cache tests/__pycache__ engine/__pycache__ trading/__pycache__
```

建议额外运行：

```bash
rg -n "provider_uri|level2 entitlement|Level2 entitlement|minute fetch|fetch_minute|qlib.init|D.features|pip install|uv add|poetry add|conda install|backtrader==|qlib==" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n -i "enabled by default|default enabled|already enabled|authorized for live|current P0 dependency|当前已启用|默认启用|默认授权|实盘授权|P0 默认依赖" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n "rm -rf|sudo|curl|wget|nc |netcat|ssh|scp|chmod|chown|mkfs|dd if=|iptables|systemctl|kill -9|os\.remove|shutil\.rmtree|subprocess|Popen|eval\(|exec\(" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
rg -n -i "ignore (all )?(previous|prior) instructions|system prompt|developer message|prompt injection|jailbreak|exfiltrate|leak" docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py
git diff --check -- docs/CR019-DEFERRED-CAPABILITIES.md README.md tests/test_cr019_deferred_capabilities.py process/stories/CR019-S09-deferred-capability-register.md process/checks/CP6-CR019-S09-deferred-capability-register-CODING-DONE.md
```

若目标文件未被 Git 跟踪，需用等价 `git diff --check --no-index /dev/null <file>` 检查 whitespace，并在 CP6 中说明退出码 1 只是文件差异预期。

## 期望输出

`process/checks/CP6-CR019-S09-deferred-capability-register-CODING-DONE.md`

完成后请回复：

- 修改文件列表
- CP6 文件路径与结论
- 实际执行的验证命令和结果
- 是否发现 BLOCKING / REQUIRED / OPEN 项
- 依赖 / 锁文件 / `.env` 是否保持未修改
