---
story_id: "CR025-S03-order-intent-draft-qmt-boundary"
title: "order_intent_draft_v1 与 QMT 后续边界"
story_slug: "order-intent-draft-qmt-boundary"
status: "verified"
priority: "P0"
wave: "CR025-W3-ORDER-INTENT-QMT"
depends_on:
  - "CR025-S02-semantic-diff-schema-artifact"
  - "CR015-S03-oms-order-state-machine"
  - "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
  - "CR017-S04-reader-api-and-policy-gates"
dependency_type:
  - upstream: "CR025-S02-semantic-diff-schema-artifact"
    type: "semantic-evidence-contract"
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "oms-contract"
  - upstream: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
    type: "order-intent-shadow-contract"
  - upstream: "CR017-S04-reader-api-and-policy-gates"
    type: "raw-execution-policy-gate"
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "engine/order_intent_draft.py"
    - "tests/test_cr025_order_intent_draft_contract.py"
  shared:
    - "trading/oms.py"
    - "trading/pretrade_risk.py"
  merge_owner: "CR025-S03-order-intent-draft-qmt-boundary"
  forbidden:
    - "QMT call"
    - "MiniQMT call"
    - "XtQuant import or call"
    - "order submit"
    - "order cancel"
    - "account query"
    - "broker lake write"
    - "service start"
lld_gate:
  required_inputs:
    - "process/HLD.md#34.7"
    - "process/HLD-QMT-TRADING.md#18"
    - "process/ARCHITECTURE-DECISION.md#ADR-077"
    - "process/stories/CR025-S03-order-intent-draft-qmt-boundary.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  backtrader_run_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 4
created_at: "2026-06-01T22:42:19+08:00"
updated_at: "2026-06-02T08:50:30+08:00"
change_id: "CR-025"
---

# CR025-S03：order_intent_draft_v1 与 QMT 后续边界

## 目标

定义 `order_intent_draft_v1` 草案合同，把 target portfolio、semantic diff evidence、lineage、limitations 和 raw execution policy 转为后续 QMT 路线可消费的离线草案。该 Story 不启动 CR-020，不调用 QMT / MiniQMT / XtQuant，不生成可提交订单。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、SM-37、SM-38、SM-41、TS-025-06、TS-025-09、TS-025-10 |
| 需求 | REQ-169、REQ-171、RA-064、RA-065 |
| HLD | `process/HLD.md` §34.7；`process/HLD-QMT-TRADING.md` §18 |
| ADR | ADR-077 |

## 开发上下文（dev_context）

**背景说明**：QMT 后续路线需要可解释的 intent 草案，但 CR-025 只提供离线 contract，不授予下单、撤单、账户查询、broker lake 写入或 gateway 启动权限。

**输入文件**：CR025-S02 semantic diff schema、CR015 OMS / shadow order intent、CR017 reader policy gates、CR-025 HLD / QMT companion HLD / ADR、本 Story 卡片。

**输出文件**：`engine/order_intent_draft.py`、`tests/test_cr025_order_intent_draft_contract.py`。

**接口约定**：

| 字段组 | 必填字段 |
|---|---|
| identity | `schema_version=order_intent_draft_v1`、`draft_id`、`source_run_id`、`created_at` |
| source | target portfolio id、semantic diff artifact id、lineage、limitations |
| order intent | symbol、side、target_qty / target_weight、estimated_price_policy、execution_price_policy、reason |
| gates | `raw_execution_policy_status`、`pretrade_required`、`qmt_allowed=false`、`blocked_reasons[]` |
| handoff | `consumer=CR-020..CR-024 later-gated`、`not_authorization=true` |

**设计约束**：`execution_price_policy != raw` 必须 hard block；draft 不等同于 order；draft 不写 broker lake；draft 不触发任何 QMT API。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR025-S02 | semantic-evidence-contract | diff schema 先冻结 | 不重新解释 semantic evidence | intent draft 引用 diff artifact id 与 limitations |
| CR015-S03 | oms-contract | OMS 状态机作为只读合同 | 不修改 OMS 行为 | draft 与订单状态隔离 |
| CR015-S06 | order-intent-shadow-contract | shadow intent 字段作为参考 | 不生成可提交订单 | CR-025 输出 draft_v1 |
| CR017-S04 | raw-execution-policy-gate | raw policy hard block 规则先冻结 | 不绕过 policy gate | 非 raw policy 不得进入 QMT handoff |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `engine/order_intent_draft.py`、`tests/test_cr025_order_intent_draft_contract.py` | 当前 Story 独占 |
| shared | `trading/oms.py`、`trading/pretrade_risk.py` | 只读或由 meta-po 串行合并；默认不修改 |
| forbidden | QMT / MiniQMT / XtQuant 调用、发单、撤单、账户查询、broker lake 写入、服务启动 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S03-T1 | 设计 | `engine/order_intent_draft.py` | 定义 `order_intent_draft_v1` 数据模型、字段校验与 blocked result |
| CR025-S03-T2 | 设计 | `tests/test_cr025_order_intent_draft_contract.py` | 设计字段覆盖、raw policy hard block、QMT 操作计数为 0 的合同测试 |
| CR025-S03-T3 | 约束 | `trading/oms.py`、`trading/pretrade_risk.py` | 明确只读消费或串行合并边界，不改真实交易流程 |
| CR025-S03-T4 | 文档输入 | QMT follow-up route | 明确 CR-020..CR-024 只消费 draft，不继承授权 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py`，但本阶段不执行。

**验证方式**：fixture-only schema contract；使用静态 target portfolio 与 semantic diff fixture，不连接 QMT。

**依赖环境**：本地 fixture；不得读取凭据、不得启动 gateway、不得 import `xtquant`、不得访问 broker / QMT。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| 完整 semantic diff + target portfolio | 生成 draft_v1 schema，`qmt_allowed=false` |
| execution_price_policy 非 raw | hard block，blocked reason 可审计 |
| 缺 lineage / limitations | fail closed，不生成 handoff |
| 扫描 QMT API / order / cancel / account query | 计数为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] `order_intent_draft_v1` 必填字段覆盖率为 100%。
- [ ] `execution_price_policy != raw` hard block 覆盖率为 100%。
- [ ] QMT API、MiniQMT、XtQuant、发单、撤单、账户查询、broker lake 写入、服务启动计数均为 0。
- [ ] CR-020..CR-024 不继承 CR-025 授权声明可由文档 / schema 消费。

## 阻塞说明

本 Story 已通过 CR-025 CP5 全量 LLD 批次确认；S02 semantic diff 合同、CR015 OMS / shadow intent 合同与 CR017 raw execution policy gate 均已 verified。meta-po 已调度 `meta-dev/dev-you` 进入 `in-development`，实现仅能创建离线 draft 合同，不授权 QMT / MiniQMT / XtQuant、真实 broker、发单、撤单、账户查询、broker lake 写入、服务启动或凭据读取。

## CP6 编码完成说明

本 Story 已完成受控离线实现并写入 `process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md`，CP6 结论为 `PASS`。实现产物为 `engine/order_intent_draft.py` 与 `tests/test_cr025_order_intent_draft_contract.py`；验证入口覆盖 `order_intent_draft_v1` schema、builder、validator、blocked result、CR-020..CR-024 later-gated handoff、`qmt_allowed=false`、`not_authorization=true`、非 raw execution price hard block、缺 lineage / limitations fail closed、forbidden-operation counters 全 0 和凭据 / 账户字段拒绝。

已执行验证命令：

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py`：`11 passed in 0.06s`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py`：`18 passed in 0.09s`
- `PYTHONPYCACHEPREFIX=/tmp/cr025-s03-pycompile uv run --python 3.11 python -m py_compile engine/order_intent_draft.py tests/test_cr025_order_intent_draft_contract.py`：PASS
- `git diff --name-only -- pyproject.toml uv.lock`：无输出

真实操作 / 禁止项计数均为 `0`；本轮未修改 `trading/oms.py`、`trading/pretrade_risk.py`、`pyproject.toml`、`uv.lock`、`STATE`、`STORY-STATUS`、CR index、docs 或其他文件，未读取 / 复制 / 迁移 `/home/hyde/download/backtrader/**`，未导入或调用 Backtrader / QMT / MiniQMT / XtQuant / broker，未读取凭据，未执行 provider fetch、lake write、publish、simulation/live，也未实现多因子研究主框架或 Qlib / Alphalens / vnpy.alpha 集成。

## CP7 验证完成说明

本 Story 已完成 `process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md`，CP7 结论为 `PASS`。验证确认 S03 fixture-only 测试 `11 passed`、CR025 当前回归 `33 passed`、py_compile、diff check、依赖 / shared trading 文件 diff 均通过；`order_intent_draft_v1` 保持 `qmt_allowed=false`、`not_authorization=true`、`consumer=CR-020..CR-024 later-gated`，非 raw execution price hard block，缺 lineage / limitations fail closed，`qmt_allowed=true` 输入 blocked，禁止项计数全部为 0。
