---
story_id: "CR041-S01-strategy-admission-package-reader"
status: "implemented"
owner: "meta-po"
implemented_at: "2026-06-10T23:55:00+08:00"
cp6: "PASS"
---

# CR041-S01 Implementation

## 实现对象

| 对象 | 路径 | 说明 |
|---|---|---|
| Engine | `engine/paper_simulation.py` | 实现 `load_strategy_admission_package`、`validate_strategy_admission_package`、`build_admission_view`、`assert_no_forbidden_operations`。 |
| Tests | `tests/test_cr041_paper_simulation.py` | 覆盖 research_baseline 准入、非零 counter、错误授权声明、敏感字段和 package status fail-closed。 |

## 设计契约映射

| LLD 契约 | 实现位置 | 验证 |
|---|---|---|
| 只读 JSON package，不写文件 | `load_strategy_admission_package` | `test_s01_strategy_admission_package_reader_accepts_research_baseline_without_upgrading_authorization` |
| `research_baseline` 且 `simulation_candidate=false` | `validate_strategy_admission_package` | 同上 |
| forbidden operation counters 全 0 | `_forbidden_counter_violations` | `test_s01_strategy_admission_package_validation_fails_closed_for_unsafe_or_invalid_inputs` |
| 敏感字段 fail-closed | `_sensitive_field_violations` | 同上 |
| 不升级 simulation/live/broker 授权 | `PaperSimulationAdmissionView` | 同上 |

## 验证结果

```text
uv run --python 3.11 python -m py_compile engine/paper_simulation.py scripts/run_paper_simulation.py tests/test_cr041_paper_simulation.py
PASS

PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr041_paper_simulation.py
21 passed in 0.11s
```

## 不授权边界

未引入 broker、Backtrader runtime、掘金、QMT、MiniQMT、XtQuant、账户、凭据、下单、撤单、provider fetch、lake write、catalog publish 或 simulation/live runtime。

## 结论

S01 实现完成，CP6 PASS，可进入 CP7 验证。
