# CR013 Backfill Roadmap Fixture

This fixture records an offline claim boundary only. It is not a real lake validation result.

| field | value |
|---|---|
| supported_window | `2025-02-11..2026-02-18` |
| blocked_window | `2020-01-01..2024-12-31` |
| old_baseline_preserved | `true` |
| full_history_status | `research_limited_only` |
| readiness_exit | `new readiness audit pass` |
| vwap_release_criteria | `vwap_status=available`; `execution audit pass`; separate authorization |

## Forbidden Operation Counters

| counter | value |
|---|---:|
| provider_fetches | 0 |
| lake_writes | 0 |
| credential_reads | 0 |
| legacy_data_reads | 0 |
| old_report_overwrites | 0 |

All current real operations are `not_authorized`: provider_fetch, lake_write, credential_read, legacy_data_read, old_report_overwrite.
