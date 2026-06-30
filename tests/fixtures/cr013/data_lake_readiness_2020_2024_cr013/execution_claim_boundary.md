# Execution / VWAP Claim Boundary

| field | value |
|---|---|
| execution_price_status | `required_missing` |
| true_vwap_available_count | `0` |
| vwap_status | `required_missing` |
| derived_vwap_policy | `amount/volume` 不得派生为真实 VWAP |

## Forbidden Operation Counters

| counter | value |
|---|---:|
| provider_fetches | 0 |
| lake_writes | 0 |
| credential_reads | 0 |
| legacy_data_reads | 0 |
| old_report_overwrites | 0 |
