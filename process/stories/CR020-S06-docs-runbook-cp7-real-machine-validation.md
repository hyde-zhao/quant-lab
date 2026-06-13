---
story_id: "CR020-S06-docs-runbook-cp7-real-machine-validation"
title: "文档、runbook 与 CP7 实机只读验收边界"
story_slug: "docs-runbook-cp7-real-machine-validation"
status: "verified-fixture-static-pending-manual-validation"
priority: "P1"
wave: "CR020-W4-DOCS-REAL-MACHINE-VALIDATION"
depends_on:
  - "CR020-S01-windows-gateway-runtime-admission"
  - "CR020-S02-server-qmt-login-session"
  - "CR020-S03-linux-client-rest-transport"
  - "CR020-S04-hmac-pairing-allowlist-scope"
  - "CR020-S05-query-positions-readonly"
dependency_type:
  - "documentation-merge"
  - "cp7-evidence-input"
  - "readonly-query-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
credential_output_allowed: false
qmt_operation_allowed: false
simulation_or_live_allowed: false
docs_as_runtime_authorization_allowed: false
file_ownership:
  primary:
    - "docs/QMT-GATEWAY-INSTALL.md"
    - "docs/QMT-C-S-BRIDGE-RUNBOOK.md"
    - "tests/test_cr020_docs_runbook_no_authorization.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "docs/QMT-INCIDENT-PLAYBOOK.md"
    - "process/TEST-STRATEGY.md"
  merge_owner: "CR020-S06-docs-runbook-cp7-real-machine-validation"
  forbidden:
    - "real credential examples"
    - "runbook authorizes real trade"
    - "CP3/CP4 approval as runtime authorization"
    - "simulation/live instructions as authorized"
    - "provider/lake/publish instructions"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.14"
    - "process/HLD.md#36.15"
    - "process/HLD.md#36.17"
    - "process/ARCHITECTURE-DECISION.md#ADR-087..ADR-093"
    - "process/stories/CR020-S06-docs-runbook-cp7-real-machine-validation.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  credential_output_allowed: false
  qmt_operation_allowed: false
  simulation_or_live_allowed: false
  docs_as_runtime_authorization_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S06-docs-runbook-cp7-real-machine-validation-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S06：文档、runbook 与 CP7 实机只读验收边界

## 目标

汇总 Windows S 端安装 / 启动前置、Linux C 端调用、pairing/HMAC、credential redaction、rollback、incident、CP7 实机只读验收证据和不授权声明。文档不得把 CP3/CP4/CP5 设计确认写成运行授权。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D6、D7 |
| HLD | `process/HLD.md` §36.14、§36.15、§36.17 |
| ADR | ADR-087..093 |
| CP3 决策 | DQ-CP3-CR020-01..07 |

## 开发上下文（dev_context）

**背景说明**：CR-020 最终需要 CP7 在真实 Windows S 端 + Linux C 端上验证只读持仓查询链路，但本阶段不执行验证、不启动 gateway、不连接 QMT。文档必须清晰区分设计通过、实现通过、运行授权和交易授权。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-087..093、CR020-S01..S05 Story 卡片、本 Story 卡片。

**输出文件**：`docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr020_docs_runbook_no_authorization.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| install docs | 说明 Windows S 端前置和配置占位符，不提供真实凭据样本 |
| C/S runbook | 说明 Python REST client 和 Typer CLI 验收面，不把 CLI 写成业务运行时 |
| CP7 evidence | 只允许只读持仓查询证据；真实运行必须独立授权 |
| no-authorization table | 明确交易、发单、撤单、改单、账户写入、simulation/live、provider/lake/publish 均未授权 |

**设计约束**：不得写真实凭据示例；不得写“CP3/CP4/CP5 通过即授权运行”；不得包含 simulation/live 执行说明或 provider/lake/publish 指令。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR020-S01..S05 | documentation-merge / cp7-evidence-input / readonly-query-contract | 必须等待上游合同冻结 | CP5 前不得实现 | S06 聚合所有边界并交给 meta-qa 制定 CP7 验收 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/QMT-GATEWAY-INSTALL.md`、`docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr020_docs_runbook_no_authorization.py` | 当前 Story LLD owner |
| shared | `README.md`、`docs/USER-MANUAL.md`、`docs/QMT-INCIDENT-PLAYBOOK.md`、`process/TEST-STRATEGY.md` | 后续 CP5/CP6/CP7 按文件 owner 串行合并 |
| forbidden | 真实凭据示例、交易授权声明、simulation/live 指令、provider/lake/publish 指令 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S06-T1 | 设计 | `docs/QMT-GATEWAY-INSTALL.md` | 定义 Windows gateway 安装、配置占位符、启动前置和禁止边界 |
| CR020-S06-T2 | 设计 | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | 定义 C/S runbook、HMAC pairing、只读查询和 rollback/incident |
| CR020-S06-T3 | 设计 | `tests/test_cr020_docs_runbook_no_authorization.py` | 设计 no-authorization / credential leak / CP7 boundary scan |
| CR020-S06-T4 | 协调 | `process/TEST-STRATEGY.md` | 给 meta-qa 留出 CP7 实机只读验收输入，不在本阶段修改 |
| CR020-S06-T5 | 门控 | CP7 | CP7 必须只验证 `query_positions` 只读链路，不授权交易 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_docs_runbook_no_authorization.py`，但本阶段不执行。

**验证方式**：文档静态扫描、credential placeholder 检查、no-authorization 声明检查、CP7 evidence schema 检查。

**依赖环境**：CP5/CP6 前不依赖真实 Windows 机器；CP7 实机验证必须由 meta-po / meta-qa 在独立授权下发起。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 文档含真实凭据 | 命中次数为 0 |
| 文档把 CP3/CP4/CP5 写成运行授权 | 命中次数为 0 |
| CP7 evidence | 仅覆盖 `query_positions` read-only |
| simulation/live 指令 | 命中次数为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] 文档覆盖 7 个 CP3 DQ、6 个 Story 边界和 no-real-operation 表。
- [ ] CP7 evidence schema 仅允许只读持仓查询链路。
- [ ] 真实凭据、账号、token、session、私钥样本数量为 0。
- [ ] “设计确认即运行授权 / 交易授权 / simulation-ready / live-ready”声明次数为 0。
- [ ] provider/lake/publish、交易、账户写入、simulation/live 指令次数为 0。

## 阻塞说明

CP5 前不得实现文档或测试；CP7 实机验证必须等 CP5/CP6 完成、meta-qa 验证策略就绪，并由 meta-po 单独确认运行授权。
