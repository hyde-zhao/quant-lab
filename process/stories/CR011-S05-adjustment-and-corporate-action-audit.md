---
story_id: "CR011-S05-adjustment-and-corporate-action-audit"
title: "复权与公司行动审计"
story_slug: "adjustment-and-corporate-action-audit"
status: "verified"
priority: "P1"
wave: "CR011-DATA-BATCH-A"
depends_on:
  - "CR010-S02-prices-adj-factor-history-backfill-loop"
  - "CR008-S04-quality-adjustment-label-window-gates"
dependency_contracts:
  - upstream: "CR010-S02-prices-adj-factor-history-backfill-loop"
    type: "runtime"
    required: "prices / adj_factor 历史覆盖、adjustment_policy、lineage 和 quality/readiness 可被只读消费"
  - upstream: "CR008-S04-quality-adjustment-label-window-gates"
    type: "contract"
    required: "质量、复权一致性和 label window gate 合同已冻结"
file_ownership:
  primary:
    - "tests/test_cr011_adjustment_audit.py"
  shared:
    - "market_data/readers.py"
    - "engine/research_dataset.py"
  merge_owner: "CR011-S05-adjustment-and-corporate-action-audit"
  forbidden:
    - "market_data/connectors/**"
    - "data/**"
    - ".env"
    - "reports/experiment_17_21/factor_strategy_report.md"
    - "delivery/**"
lld_gate:
  required_inputs:
    - "process/HLD.md#27.7"
    - "process/HLD-DATA-LAKE.md#14.2"
    - "process/ARCHITECTURE-DECISION.md#adr-040cr-011-adjustment-与-corporate-action-audit-分层声明"
    - "process/stories/CR011-S05-adjustment-and-corporate-action-audit.md"
  status: "approved"
  cp5_batch: "CR011-DATA-BATCH-A"
  cp5_precheck: "process/checks/CP5-CR011-S05-adjustment-and-corporate-action-audit-LLD-IMPLEMENTABILITY.md"
  manual_review: "checkpoints/CP5-CR011-DATA-BATCH-A-LLD-BATCH.md"
  confirmed_by: "user"
  confirmed_at: "2026-05-24T10:24:02+08:00"
  preconditions:
    - "CR-011 CP3 人工确认通过"
    - "CR-011 CP4 自动预检通过并由 meta-po 汇入 CP5"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  required_contracts:
    - "adjustment_policy and corporate_action_status metadata frozen"
    - "CR011-DATA-BATCH-A CP5 approved"
  file_conflict_free: true
  cp5_required: true
  implementation_allowed: true
  reason: "CR011-DATA-BATCH-A CP5 已 approved；CR010-S02 runtime 与 CR008-S04 adjustment/label window contract 均已 verified；S04 已 verified；S05 CP6 adoption PASS 且 CP7 PASS，当前 verified。"
created_at: "2026-05-23"
updated_at: "2026-05-24T14:11:03+08:00"
source_hld: "process/HLD.md"
companion_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-011"
---

# CR011-S05：复权与公司行动审计

## 目标

将 `adj_factor` lineage、复权一致性和 corporate action availability 纳入研究 metadata，使新版因子、收益、benchmark 和 portfolio 计算能证明复权口径一致，并区分“使用已复权价格”和“完整公司行动链路可审计”。该 Story 不声明缺公司行动时完整审计，不混用复权口径，不覆盖旧报告。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-08 |
| 需求 | REQ-075、REQ-080、REQ-081、CR011-AC-005 |
| HLD | `process/HLD.md` §27.1、§27.4、§27.5、§27.7；`process/HLD-DATA-LAKE.md` §14.2、§14.4、§14.5 |
| ADR | ADR-040 |
| Backlog / Plan | `process/STORY-BACKLOG.md` CR011-S05；`process/DEVELOPMENT-PLAN.yaml` wave `CR011-DATA-BATCH-A` |

## 开发上下文（dev_context）

**背景说明**：复权口径混用会直接污染因子收益和标签；公司行动审计是比 `adj_factor` 存在更强的声明。CR-011 需要将 adjustment policy、`adj_factor` lineage 和 corporate action status 分层写入研究 metadata。

**输入文件**：`process/HLD.md`、`process/HLD-DATA-LAKE.md`、`process/ARCHITECTURE-DECISION.md`、`process/REQUIREMENTS.md`、`process/USE-CASES.md`、`market_data/readers.py`、`engine/research_dataset.py`。

**输出文件**：`market_data/readers.py`、`engine/research_dataset.py`、`tests/test_cr011_adjustment_audit.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| adjustment reader | price dataset、adj_factor dataset、catalog/readiness、quality policy | `adjustment_policy`、`adj_factor_lineage`、source_run_id、lineage checksum | 缺 `adj_factor` lineage 时 `adjustment_audit_status` fail |
| corporate action availability | symbol/date、corporate action artifact metadata、available_at | `corporate_action_status`、event type、missing reason | 缺公司行动时不得声明完整公司行动审计 |
| adjustment audit gate | 因子、收益、benchmark、portfolio 输入 metadata | `adjustment_audit_status`、mixed policy count、blocked claims | 复权口径混用进入因子计算次数为 0 |

**设计约束**：

- CP3 / CP4 未通过前不得进入 LLD；`CR011-DATA-BATCH-A` CP5 批次确认前不得实现。
- `adj_factor_lineage` 与 `corporate_action_status` 必须分层表达。
- 公司行动缺 explicit `available_at` 时不得进入事件型决策。
- 不读取 `.env`，不触发真实 provider，不操作旧 `data/**`，不覆盖旧报告，不写 `delivery/**`。

**命名规范**：保留 `adjustment_policy`、`adj_factor_lineage`、`corporate_action_status`、`adjustment_audit_status`、`lineage_raw_checksum`、`mixed_adjustment_policy_count`。

**平台目标**：本地 Python 因子研究工具；uv 管理依赖；无安装脚本；无 `delivery/**` 输出。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR011-S05-T1 | 修改 | `market_data/readers.py` | 暴露 adj_factor lineage、adjustment policy 和 corporate action availability / missing reason |
| CR011-S05-T2 | 修改 | `engine/research_dataset.py` | 增加 adjustment audit gate，阻断复权口径混用和过强公司行动审计声明 |
| CR011-S05-T3 | 创建 | `tests/test_cr011_adjustment_audit.py` | 覆盖 4 个必填字段、混用复权 fail、公司行动缺失 blocked claims 和 no old report overwrite |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr011_adjustment_audit.py`。

**验证方式**：prices / adj_factor fixture、mixed policy fixture、corporate action missing fixture、metadata 快照和 forbidden path 扫描。

**依赖环境**：Python 3.11、uv、pytest；不需要真实公司行动数据、不需要 token、不联网。

**关键验证场景**：

- `adjustment_policy`、`adj_factor_lineage`、`corporate_action_status`、`adjustment_audit_status` 4 字段均输出。
- 复权口径混用进入因子计算次数为 0。
- 公司行动缺失时只允许“使用已复权价格”声明，不允许“公司行动链路可审计”声明。
- 默认路径不触发真实源、不读取凭据、不操作旧数据、不覆盖旧报告。

## 量化验收标准（acceptance_criteria）

- [ ] `adjustment_policy`、`adj_factor_lineage`、`corporate_action_status`、`adjustment_audit_status` 4 字段必填。
- [ ] 复权口径混用进入因子计算次数为 0。
- [ ] 公司行动缺失时完整公司行动审计声明输出次数为 0。
- [ ] `adjustment_audit_status` 至少支持 `pass / required_missing / quality_failed` 或等价枚举。
- [ ] 默认验证路径 `network_calls=0`、`lake_writes=0`、`credential_reads=0`、`legacy_data_operations=0`。

## 阻塞说明

OPEN：CR-011 CP3 / CP4 尚未通过，本 Story 不得进入 LLD。OPEN：`CR011-DATA-BATCH-A` CP5 尚未完成，不得实现。OPEN：真实 corporate action source/interface 是否可用不在本 Story draft 阶段决策，缺失时必须保留 required_missing / blocked claims。
