# CP6 CR-036 Coding Done - Chapter 5 Anomalies

## Entry Criteria

| Item | Result | Evidence |
|---|---|---|
| CR-036 activated after CR-035 closure | PASS | `process/changes/CR-036-CHAPTER5-ANOMALY-REPLICATION-2026-06-10.md` |
| CR-034 / CR-035 local research inputs exist | PASS | `reports/chapter3_factor_panel/`, `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/` |
| No QMT / provider / lake / publish authorization required | PASS | CR-036 boundary and runner operation counters |

## Checklist

| Check | Result | Evidence |
|---|---|---|
| Engine implementation added | PASS | `engine/chapter5_anomalies.py` |
| Runner implementation added | PASS | `scripts/run_chapter5_anomalies.py` |
| Unit tests added | PASS | `tests/test_chapter5_anomalies.py` |
| Three anomaly families implemented | PASS | `valuation_extreme_spread`, `fundamental_anchor_reversal`, `idiosyncratic_volatility_proxy` |
| Alpha tests consume CR-035 model returns | PASS | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet` |
| Strict gaps retained instead of silent source substitution | PASS | `build_gap_register()` and generated `gap_register.csv` |
| Forbidden operation counters available | PASS | `FORBIDDEN_OPERATION_COUNTS` |

## Exit Criteria

| Item | Result | Evidence |
|---|---|---|
| Code compiles | PASS | `PYTHONPYCACHEPREFIX=/tmp/cr036-chapter5-pycompile uv run --python 3.11 python -m py_compile engine/chapter5_anomalies.py scripts/run_chapter5_anomalies.py tests/test_chapter5_anomalies.py` |
| Focused tests pass | PASS | `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_chapter5_anomalies.py` -> 4 passed |
| Implementation remains local-readonly except report writes | PASS | Runner writes only `reports/chapter5_anomalies/` and `process/research/chapter5_anomalies/` |

## Deliverables

- `engine/chapter5_anomalies.py`
- `scripts/run_chapter5_anomalies.py`
- `tests/test_chapter5_anomalies.py`

## Result

PASS. CR-036 implementation is ready for CP7 verification. This checkpoint does not authorize provider fetch, lake write, catalog publish, QMT, simulation, live, account/order operations, credential reads, or dependency changes.
