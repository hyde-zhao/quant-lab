---
story_id: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
title: "Backtrader 模块 reference / no-copy guardrail"
story_slug: "backtrader-module-reference-no-copy-guardrail"
status: "verified"
priority: "P0"
wave: "CR025-W1-FEED-GOVERNANCE"
depends_on: []
dependency_type: []
cp5_batch: "CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/CR025-BACKTRADER-MODULE-REFERENCE.md"
    - "tests/test_cr025_backtrader_no_copy_guardrail.py"
  shared:
    - "process/HLD.md"
  merge_owner: "CR025-S04-backtrader-module-reference-no-copy-guardrail"
  forbidden:
    - "/home/hyde/download/backtrader/** source copy"
    - "backtrader/** vendored source"
    - "Backtrader samples/tests/datas copy"
    - "Backtrader live store copy or wrapper"
    - "Backtrader line/metaclass runtime migration"
    - "Backtrader as multifactor research framework"
    - "process/HLD.md mutation during story execution"
lld_gate:
  required_inputs:
    - "process/HLD.md#34.5"
    - "process/HLD.md#34.14"
    - "process/ARCHITECTURE-DECISION.md#ADR-075"
    - "process/ARCHITECTURE-DECISION.md#ADR-076"
    - "process/ARCHITECTURE-DECISION.md#ADR-078"
    - "process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md"
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
updated_at: "2026-06-02T07:55:45+08:00"
change_id: "CR-025"
---

# CR025-S04：Backtrader 模块 reference / no-copy guardrail

## 目标

把 HLD §34.5 的 Backtrader 模块分类矩阵落入 Story / LLD 输入：`reference_only`、`adapt_interface`、`migration_candidate` 和 `exclude` 必须有清晰边界；当前 `migration_candidate` 为空。该 Story 建立 no-copy / no-source-migration guardrail，不复制、裁剪、改写或源码级移植 Backtrader GPLv3 源码。矩阵只服务 lightweight execution engine 的执行语义参考，不把 Backtrader indicators / Strategy / analyzer 体系升级为多因子研究主框架。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-19、SM-39、TS-025-07、TS-025-11 |
| 需求 | REQ-172、REQ-173、RA-066 |
| HLD | `process/HLD.md` §34.5、§34.14 |
| ADR | ADR-075、ADR-076、ADR-078 |

## 开发上下文（dev_context）

**背景说明**：Backtrader GPLv3 源码只能作为外部 reference 被研究和调用；本项目不得通过复制、裁剪、改写、源码级移植或 vendoring 的方式吸收其实现。CR-025 的合规目标是定义执行语义 reference 边界和扫描策略，而不是迁移 Backtrader 内部机制，也不是用 Backtrader 承接 FactorSpec、IC / RankIC、分层收益、多因子组合或实验追踪。

**输入文件**：CR-025 HLD §34.5 module matrix、ADR-075 / ADR-076、本 Story 卡片。

**输出文件**：`docs/CR025-BACKTRADER-MODULE-REFERENCE.md`、`tests/test_cr025_backtrader_no_copy_guardrail.py`。

**接口约定**：

| 分类 | 当前处理 |
|---|---|
| `reference_only` | 可读作行为 reference，不复制代码；示例：Cerebro orchestration / broker semantics / analyzer semantics |
| `adapt_interface` | 可定义本项目自己的接口适配层，但不得移植 Backtrader internals |
| `migration_candidate` | 当前为空；任何候选必须另起 CR / legal review / CP3 决策 |
| `exclude` | live store、line/metaclass runtime、samples/tests/datas、GPLv3 source tree、真实 broker 集成 |
| `multifactor_research_boundary` | FactorSpec、FactorRunSpec、IC / RankIC、分层收益、多因子组合、实验追踪和策略准入包另起后续 CR，参考 Qlib / Alphalens / vnpy.alpha |

**设计约束**：禁止把 `/home/hyde/download/backtrader` 或任何 Backtrader 源码树复制到仓库；禁止复制 tests / samples / datas；禁止实现 line/metaclass runtime 等源码级移植；禁止把 Backtrader indicators / Strategy / analyzer 体系写成本项目多因子研究主框架。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| 无 | n/a | 可与 S01 并行起草 LLD | CP5 前不得实现 | S04 为 S02 提供 license guardrail 输入 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`、`tests/test_cr025_backtrader_no_copy_guardrail.py` | 当前 Story 独占 |
| shared | `process/HLD.md` | 只读引用，不在 Story 执行中修改 |
| forbidden | Backtrader source tree、vendored source、samples/tests/datas、live store、line/metaclass runtime、Backtrader-as-multifactor-framework | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR025-S04-T1 | 设计 | `docs/CR025-BACKTRADER-MODULE-REFERENCE.md` | 定义模块分类矩阵、可引用行为和不可复制边界 |
| CR025-S04-T2 | 设计 | `tests/test_cr025_backtrader_no_copy_guardrail.py` | 设计 forbidden source-copy / migration scan 和 migration_candidate 空集合测试 |
| CR025-S04-T3 | 约束 | LLD / Story 输入 | 明确任何 migration_candidate 或多因子研究框架能力必须另起 CR 和人工确认 |
| CR025-S04-T4 | 约束 | Backtrader reference | 明确 Backtrader 源码、samples、tests、datas、live store 和多因子研究闭环不进入 CR-025 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr025_backtrader_no_copy_guardrail.py`，但本阶段不执行。

**验证方式**：静态扫描与文档合同测试；不读取 Backtrader 源码内容，不复制源码，不运行 Backtrader。

**依赖环境**：仅检查仓库文件与合同声明；不得访问外部 broker / provider / credentials。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| migration_candidate | 当前为空 |
| forbidden source path | 仓库不出现 vendored Backtrader source / samples / tests / datas |
| live store / line runtime | 不进入 adapt_interface 或 migration_candidate |
| legal boundary | docs 明确 no-copy / no-source-migration |
| multifactor boundary | docs 明确 Backtrader 不承接 FactorSpec / IC / RankIC / 多因子组合等研究能力 |

## 量化验收标准（acceptance_criteria）

- [ ] `migration_candidate` 当前为空。
- [ ] forbidden path 覆盖源码、samples、tests、datas、live store、line/metaclass runtime 共 6 类。
- [ ] Backtrader GPLv3 源码复制 / 裁剪 / 改写 / 源码级移植项为 0。
- [ ] Backtrader 承接 FactorSpec、IC / RankIC、分层收益、多因子组合、实验追踪或策略准入包的次数为 0。
- [ ] Backtrader run、provider fetch、lake write、credential read、QMT 调用均为 0。

## 阻塞说明

本 Story 是合规 guardrail，已通过 CR-025 CP5 全量 LLD 批次确认，并由 `meta-dev/dev-xu` 完成受控离线实现与 CP6 PASS，当前进入 `ready-for-verification`。任何希望把 Backtrader 内部代码迁入本项目的想法都必须作为新 CR / legal review / CP3 决策处理。任何希望建设多因子研究闭环的想法也必须作为 CR-030 或后续 CR 处理，正式启动时再验证 Qlib / Alphalens / vnpy.alpha 等项目的 license、维护状态和适配边界。
