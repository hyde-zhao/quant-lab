# CP7 CR-036 Verification Done - Chapter 5 Anomalies

## Entry Criteria

| Item | Result | Evidence |
|---|---|---|
| CP6 implementation complete | PASS | `process/checks/CP6-CR036-CHAPTER5-ANOMALIES-CODING-DONE.md` |
| CR-034 factor panel inputs available | PASS | `reports/chapter3_factor_panel/` |
| CR-035 model return inputs available | PASS | `reports/chapter4_factor_models/run-cr035-chapter4-factor-models-20260610/factor_model_returns.parquet` |

## Checklist

| Check | Result | Evidence |
|---|---|---|
| Real local runner completed | PASS | `run-cr036-chapter5-anomalies-20260610` |
| In-sample window verified | PASS | `in_sample_2000_2019`: 2,550,289 panel rows, 447,186 label rows, 969,286 anomaly panel rows |
| Observation window verified | PASS | `observation_2020_2026_ytd`: 1,957,024 panel rows, 371,877 label rows, 777,587 anomaly panel rows |
| Alpha tests generated | PASS | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/alpha_tests.csv` |
| Admission summary generated | PASS | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/ANOMALY-ADMISSION-SUMMARY.json` |
| Gap register generated | PASS | `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/gap_register.csv` |
| Forbidden operations remained zero | PASS | provider_fetch=0, lake_write=0, catalog_publish=0, qmt_operation=0, simulation_or_live=0 |
| Boundary claims blocked | PASS | production_valid, qmt_ready, simulation_ready and live_ready are blocked in admission summary |

## Exit Criteria

| Item | Result | Evidence |
|---|---|---|
| Runner status is PASS | PASS | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.json` |
| Human-readable report exists | PASS | `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.md` |
| Memory budget satisfied | PASS | Runner completed with `--max-memory-gb 16` |
| Strict source gap visible | PASS | `CR036-GAP-BOOK-CHAPTER5-SOURCE` remains `open-with-proxy-implemented` |

## Deliverables

- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_panel.parquet`
- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_returns.csv`
- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/alpha_tests.csv`
- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_correlation.csv`
- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/gap_register.csv`
- `reports/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/anomaly_manifest.json`
- `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.md`
- `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/CHAPTER5-RUN-REPORT.json`
- `process/research/chapter5_anomalies/run-cr036-chapter5-anomalies-20260610/ANOMALY-ADMISSION-SUMMARY.json`

## Result

PASS_WITH_RISK. CR-036 has local verification evidence and can be reviewed. Remaining risk is explicit: the repository does not contain the Chapter 5 book Markdown source, so the result is a project-executable anomaly replication with proxy definitions, not a claim of strict verbatim replication.
