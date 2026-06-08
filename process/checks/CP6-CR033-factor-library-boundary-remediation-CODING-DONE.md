# CP6 CR033 因子库边界整改编码完成检查

## Entry Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| CR033 已创建 | PASS | `process/changes/CR-033-FACTOR-LIBRARY-BOUNDARY-REMEDIATION-2026-06-08.md` |
| 变更范围限定为因子库边界整改 | PASS | 不触碰 provider/lake/QMT/simulation/live；不读取 `.env`。 |
| CR032 历史基线保留 | PASS | 未改写 `process/changes/CR-032-CHAPTER3-FACTOR-GAP-REMEDIATION-2026-06-08.md`。 |

## Checklist

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 通用因子定义已脱离第三章模块 | PASS | `engine/factor_library.py` |
| 2 | 七个因子 ID 未使用 `chapter3` 前缀 | PASS | `DEFAULT_EQUITY_CORE_FACTOR_IDS` |
| 3 | 第三章来源只作为 metadata | PASS | `EquityFactorDefinition.source_refs` |
| 4 | 通用因子定义可导出 CR030 `FactorSpec` | PASS | `to_factor_spec(...)`；`tests/test_factor_library.py` |
| 5 | 通用因子库支持长期扩展 | PASS | `validate_equity_factor_library(...)`、`build_equity_factor_library(...)`、`to_factor_specs(...)` |
| 6 | 通用因子计算从第三章模块迁出 | PASS | `engine/factor_calculators.py` |
| 7 | 计算器支持 registry 扩展 | PASS | `FactorCalculationContext`、`calculator_registry`、`core_equity_factor_calculators()` |
| 8 | 通用统计检验从第三章模块迁出 | PASS | `engine/factor_statistics.py` |
| 9 | 第三章模块保留为适配层 | PASS | `engine/chapter3_factor_replication.py` 调用 `compute_equity_factor_matrices(...)` |
| 10 | 第三章兼容入口保留 | PASS | `chapter3_factor_definitions()`、`factor_matrices_to_panel(...)` wrapper |
| 11 | 过程文档更新 | PASS | `process/research/chapter3_factor_replication/README.md`、`docs/CR030-FACTOR-RESEARCH-QUICKSTART.md` |
| 12 | 新增测试覆盖分层边界和长期扩展 | PASS | `tests/test_factor_library.py`、`tests/test_factor_calculators.py`、`tests/test_factor_statistics.py` |

## Implemented Files

| 文件 | 动作 | 说明 |
|---|---|---|
| `engine/factor_library.py` | 新增 | 通用权益因子定义、source refs、CR030 FactorSpec 导出。 |
| `engine/factor_calculators.py` | 新增 | 七个通用因子矩阵计算、calculator registry、方向处理、缩尾、zscore、面板输出。 |
| `engine/factor_statistics.py` | 新增 | 单变量排序、双重排序、条件双重排序、Newey-West、Fama-MacBeth。 |
| `engine/chapter3_factor_replication.py` | 修改 | 改为第三章 policy / data issue / runner adapter，复用通用模块。 |
| `tests/test_factor_library.py` | 新增 | 验证因子 ID、source refs、CR030 FactorSpec。 |
| `tests/test_factor_calculators.py` | 新增 | 验证七个因子矩阵、缺输入 limitations 和自定义 calculator registry。 |
| `tests/test_factor_statistics.py` | 新增 | 验证排序、Newey-West、Fama-MacBeth。 |
| `tests/test_chapter3_factor_replication.py` | 保留 | 继续覆盖第三章口径和兼容入口。 |

## Exit Criteria

| 条目 | 结果 | 说明 |
|---|---|---|
| 编码范围完整 | PASS | 通用定义、计算、统计和第三章适配层已拆分。 |
| 无真实外部操作 | PASS | 仅本地代码和 fixture 测试。 |
| 可进入 CP7 验证 | PASS | 测试入口明确。 |

## Deliverables

- `engine/factor_library.py`
- `engine/factor_calculators.py`
- `engine/factor_statistics.py`
- `engine/chapter3_factor_replication.py`
- `tests/test_factor_library.py`
- `tests/test_factor_calculators.py`
- `tests/test_factor_statistics.py`
- `process/research/chapter3_factor_replication/README.md`
