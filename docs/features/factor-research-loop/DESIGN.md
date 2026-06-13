---
status: "draft-current-index"
version: "1.0"
feature_id: "FEAT-03"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
source_blueprint: "docs/design/BLUEPRINT.md"
change: "CR-031"
---

# Feature Design: factor-research-loop

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增多因子研究闭环 Feature 设计索引 |

## Feature 摘要

| 项 | 内容 |
|---|---|
| Feature 目标 | 统一项目自有多因子研究闭环，覆盖 FactorSpec、FactorRunSpec、FactorPanel、LabelWindow、FactorEvaluationReport、MultiFactorCombiner、ExperimentManifest、StrategyAdmissionPackage |
| Owner | FEAT-03 |
| 主要代码面 | `engine/factor_*`、`engine/multifactor_*`、`engine/research_*`、`experiments/*factor*` |
| 主要设计来源 | `process/HLD.md` §35、ADR-079..086、CR-030 Story / LLD |
| 非授权声明 | 不授权外部项目运行、依赖变更、provider/lake/publish、QMT/simulation/live 或凭据读取 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 |
|---|---|---|---|
| ResearchDataset | 消费 `research_input_v1` 和 production current truth | 写湖 / publish | FEAT-02 |
| FactorSpec / FactorRunSpec | 因子定义、运行配置、错误码和 failure policy | 外部框架默认 schema | FEAT-04 |
| FactorPanel / LabelWindow | 因子面板四层值、标签窗口、泄漏 fail-closed | 原始数据生产 | FEAT-02 |
| Evaluation / Combiner | IC、RankIC、分层收益、多因子组合和报告 | 实盘执行 | FEAT-06 |
| StrategyAdmissionPackage | 准入证据、blocked reasons、order intent draft 引用 | runtime authorization | FEAT-07 |

## 输入 / 输出契约

| 方向 | 契约 |
|---|---|
| 输入 | published data release、research_input_v1、factor definitions、label window、cost config、benchmark policy |
| 输出 | factor panel、factor evaluation report、multifactor portfolio plan、experiment manifest、research report catalog、strategy admission package |
| 错误输出 | `schema_invalid`、`label_window_leakage`、`required_missing`、`blocked_claims`、`admission_blocked` |

## 失败路径

| 失败点 | 行为 |
|---|---|
| 数据或 benchmark 缺失 | 生成 `required_missing`，不得输出 production admission pass |
| label window 泄漏风险 | fail-closed，不继续评价 |
| 外部项目只能静态参考 | clone / install / run / qrun / notebook / provider 下载均 blocked |
| admission package incomplete | 输出 blocked reason，不进入 QMT stage |

## Gotchas

- StrategyAdmissionPackage 是准入证据，不是交易授权。
- CR-030 不从零发明 schema，必须回链已有 `research_input_v1`、实验 17-21 和 CR-011 审计合同。
- Qlib / Alphalens / Zipline / LEAN 只能 cross-check，不成为 truth。

