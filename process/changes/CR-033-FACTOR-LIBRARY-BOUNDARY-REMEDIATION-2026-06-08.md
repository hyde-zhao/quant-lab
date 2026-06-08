---
cr_id: CR-033
title: 因子库边界整改：拆分第三章复刻模块与通用因子能力
status: implemented
created_at: 2026-06-08
owner: codex
change_type: modify
impact_level: medium
workflow_mode: fast-lane
rollback_to: "36e1782 Implement chapter 3 factor remediation"
related_changes:
  - CR-030
  - CR-032
---

# CR-033 因子库边界整改

## 变更原因

用户审查 CR-032 第三章因子复刻实现后指出两个问题：

1. 因子长期以 `chapter3` 命名不合理；第三章只能作为来源和复刻场景，不能成为通用因子的身份。
2. `engine/chapter3_factor_replication.py` 同时承载因子定义、因子计算、统计检验和第三章数据 policy，边界不清晰，不利于后续多因子策略开发。

本变更不改写 CR-032 历史，而是在其基础上做边界整改，保留可追溯链。

## 五维度影响分析

| 维度 | 影响 | 处理结论 |
|---|---|---|
| 需求层 | 新增“通用因子能力不能绑定书籍章节命名空间”的约束。 | 因子 ID 保持 `value_bm`、`momentum_12_1` 等通用语义；第三章来源写入 `source_refs`。 |
| 场景层 | 第三章复刻仍可运行；后续新增因子有更清晰入口。 | 第三章 runner 保留 wrapper；新增因子使用 `engine.factor_library` / `engine.factor_calculators`。 |
| 计划层 | 影响 CR-032 实现文件拆分和测试分层。 | fast-lane 小步整改，不触碰真实数据接入、不进入标准多阶段流程。 |
| 安全层 | 不涉及凭据、外部 provider、lake、publish、QMT、simulation 或 live。 | 保持纯离线 DataFrame 处理；验证命令均使用 `uv run`。 |
| 交付层 | 新增 3 个通用模块、3 个测试文件，更新第三章 README。 | CP6/CP7 检查点记录实现与验证证据。 |

## 文档处理决策

| 文档 | 决策 | 旧基线保留方式 |
|---|---|---|
| `process/research/chapter3_factor_replication/README.md` | 原文档更新 | 追加“2026-06-08 边界整改记录”，保留 CR-032 原始结论和剩余授权事项。 |
| `process/changes/CR-032-CHAPTER3-FACTOR-GAP-REMEDIATION-2026-06-08.md` | 不变 | CR-032 作为第三章缺口整改历史基线保留，不重写。 |
| `engine/chapter3_factor_replication.py` | 原代码整改 | 保留第三章复刻适配层和兼容入口，通用能力迁移到新模块。 |

## 实施范围

新增：

- `engine/factor_library.py`
- `engine/factor_calculators.py`
- `engine/factor_statistics.py`
- `tests/test_factor_library.py`
- `tests/test_factor_calculators.py`
- `tests/test_factor_statistics.py`
- `process/checks/CP6-CR033-factor-library-boundary-remediation-CODING-DONE.md`
- `process/checks/CP7-CR033-factor-library-boundary-remediation-VERIFICATION-DONE.md`

修改：

- `engine/chapter3_factor_replication.py`
- `tests/test_chapter3_factor_replication.py`
- `process/research/chapter3_factor_replication/README.md`

## 设计决策

| 决策 | 推荐方案 | 备选 | 结论 |
|---|---|---|---|
| 因子身份 | 使用通用因子 ID，第三章仅作为 `source_refs`。 | 所有因子加 `chapter3_` 前缀。 | 采用推荐方案，避免污染通用因子库。 |
| 通用定义合同 | `engine.factor_library` 导出 CR030 `FactorSpec`。 | 另造新 FactorDefinition 合同。 | 采用推荐方案，复用 CR030 主合同。 |
| 第三章模块定位 | 保留为复刻适配层。 | 删除第三章模块，只保留通用模块。 | 保留适配层以保存书籍口径和复刻入口。 |
| 统计工具归属 | 迁移到 `engine.factor_statistics`。 | 继续放在第三章模块。 | 迁移，支持后续论文/书籍复用。 |
| 长期扩展方式 | 因子定义注册 + calculator registry。 | 每新增因子都修改第三章模块或硬编码 if/else。 | 采用推荐方案，后续新增因子不依赖第三章模块。 |

## 不授权范围

本 CR 不授权：

- 读取 `.env` 或任何凭据。
- provider fetch。
- lake write。
- catalog publish。
- QMT、simulation、live。
- 账户、订单或外部交易能力。
- 真实 A 股全市场第三章实证重跑。

## 回滚策略

如需回滚，仅回退 CR-033 的增量提交即可恢复 CR-032 单文件第三章复刻形态：

```bash
git revert <CR033提交>
```

回滚不影响 CR-032 已提交的第三章缺口整改基线。

## 验收标准

- 通用因子 canonical 定义位于 `engine/factor_library.py`。
- 因子 ID 不含 `chapter3` 前缀。
- 七个因子能导出 CR030 `FactorSpec` 并通过合同校验。
- 自定义因子定义可通过 `build_equity_factor_library(...)` 合入通用库。
- 章节命名空间因子 ID 可被 `validate_equity_factor_library(...)` 拒绝。
- 通用因子计算位于 `engine/factor_calculators.py`。
- 自定义因子计算器可通过 `calculator_registry` 接入。
- 通用排序和统计位于 `engine/factor_statistics.py`。
- `engine/chapter3_factor_replication.py` 只作为第三章口径适配层。
- 第三章测试、通用因子测试和 CR030 回归测试通过。
