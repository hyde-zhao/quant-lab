---
story_id: "CR014-S07-research-consumer-readonly-docs-runbook-boundary"
title: "research consumer read-only contract 与 docs/runbook 后续边界"
status: "verified"
priority: "P1"
wave: "CR014-W4-CONSUMER-BOUNDARY"
depends_on:
  - "CR014-S04-duckdb-readonly-query-audit-parity-boundary"
  - "CR014-S05-full-history-readiness-gap-claim-boundary"
  - "CR014-S06-incremental-refresh-replay-retention-contract"
cp5_batch: "CR014-FULL-HISTORY-LAKE-BATCH-A"
implementation_allowed: true
created_at: "2026-05-27"
updated_at: "2026-05-27T10:12:25+08:00"
change_id: "CR-014"
---

# CR014-S07：research consumer read-only contract 与 docs/runbook 后续边界

## Story 摘要

冻结研究消费层只读 published current truth、blocked claims 和 required_missing 的合同，并定义 README / USER-MANUAL / runbook 后续刷新边界。研究消费层不得直接 DuckDB 写入、不得 publish、不得扫描未发布 lake、不得触发 provider 或凭据读取。

## dev_context

**输入依据**：`process/HLD.md` §30.2、§30.3；ADR-049、ADR-051、ADR-052；REQ-093、REQ-094、REQ-095。

**未来实现候选文件**：`engine/research_dataset.py`、`experiments/reporting.py`、`README.md`、`docs/USER-MANUAL.md`、`tests/test_cr014_research_consumer_boundary.py`。

**开发合同**：

| 消费方 | 允许输入 | 输出 | 禁止 |
|---|---|---|---|
| research dataset builder | published current truth、blocked_claims、required_missing | research input / metadata | provider fetch、lake write、credential read |
| experiments/reporting | research input、claim boundary | report metadata / limitation | 直接 DuckDB 写入、publish、扫 candidate |
| docs/runbook | CP5 后确认的行为合同 | 用户说明 | Story Plan 阶段修改 README/docs |

## validation_context

**验证方式**：静态 import / boundary test；确认 consumer 层不导入 provider/runtime/storage/publish 写路径。

**关键验证场景**：

| 场景 | 期望 |
|---|---|
| consumer 读取数据 | 只读 published current truth |
| blocked claims | 进入报告 metadata，不被声明为 available |
| candidate path | 不被研究消费层默认扫描 |
| docs 后续刷新 | 只作为 LLD 输入，本阶段不改文档 |

## acceptance_criteria

| ID | 标准 | 验收方式 |
|---|---|---|
| AC-01 | consumer provider/lake/credential/old data 操作次数为 0 | 静态检查 / 单元测试 |
| AC-02 | 实验入口直接 DuckDB 写入或 publish 次数为 0 | 静态检查 |
| AC-03 | 未发布 candidate 不作为 research current truth | contract test |
| AC-04 | README/docs 修改次数在 Story Plan 阶段为 0 | CP4 文件范围检查 |

## 依赖与文件影响范围

| 类型 | 内容 |
|---|---|
| 上游依赖 | CR014-S04、CR014-S05、CR014-S06 |
| 下游依赖 | 后续 CP5 / 文档刷新 Story |
| 主所有权 | `engine/research_dataset.py`、`experiments/reporting.py`、`tests/test_cr014_research_consumer_boundary.py` |
| 共享文件 | `README.md`、`docs/USER-MANUAL.md` 仅为后续刷新边界，不在本阶段修改 |
| 禁止范围 | `.env`、`data/**`、`reports/**`、直接 DuckDB 写入、publish、未发布 lake 扫描、README/docs 当前阶段修改 |

## LLD 输入

- HLD.md §30 的研究消费层边界。
- S04 DuckDB read-only、S05 claim boundary、S06 replay/retention。
- ADR-049 / ADR-051 / ADR-052。
- 本阶段不改 README/docs，CP5 后另行按授权刷新。
