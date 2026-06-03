# CR017 Adjustment Policy Migration Summary

## Scope

This document freezes the CR017 migration statement for adjustment policy contracts. It is a
summary-only artifact: it does not read private lake paths, rewrite legacy reports, publish catalog
current pointers, or run provider fetches.

## Policy Views

| View | Policy | Role |
|---|---|---|
| `prices_raw` | `raw` | Source-of-truth unadjusted trading price for research lineage and QMT handoff. |
| `adj_factor` | factor contract | Source-of-truth adjustment factor with explicit `provider_factor_direction`. |
| `prices_qfq` | `qfq` | Derived forward-adjusted research view with `as_of_trade_date`. |
| `prices_hfq` | `hfq` | Derived backward-adjusted research view with base-date metadata. |
| `returns_adjusted` | `returns_adjusted` | Derived adjusted return view that must not mix price policies inside one run. |

## Legacy QFQ Baseline

| Field | Value |
|---|---|
| `legacy_qfq_baseline_preserved` | `true` |
| compatibility entry | `legacy_qfq_readonly` |
| new CR017 view id | `prices_qfq` |
| migration status | `summary_only` |
| single policy gate | `single_policy_gate_required` |

The legacy qfq baseline remains read-only. CR017 does not overwrite old qfq data, old reports,
or legacy report evidence. Consumers that still depend on the legacy qfq baseline must keep the
legacy reference explicit and must not infer that the new `prices_qfq` view has replaced it.

## Forbidden Operations

| Operation | Count |
|---|---:|
| provider_fetch | 0 |
| lake_write | 0 |
| credential_read | 0 |
| current_pointer_publish | 0 |
| dependency_change | 0 |
| legacy_qfq_overwrite | 0 |

## QMT Boundary

QMT execution consumers may use only `raw` / broker prices for order intent, order placement,
fill accounting, and reconciliation. `qfq`, `hfq`, and `returns_adjusted` are research metadata
only and must be blocked as execution prices.

## Consumer Guidance Matrix

| Consumer | Recommended policy | Allowed research policies | Execution policy | Blocked policy / claim |
|---|---|---|---|---|
| `chart` | `qfq` | `qfq`, `raw` | N/A | none, as long as the chart labels the policy explicitly |
| `long_horizon_research` | `hfq_or_returns_adjusted` | `hfq`, `returns_adjusted`, `qfq` | N/A | raw execution claim |
| `factor_research` | `returns_adjusted` | `returns_adjusted`, `qfq`, `hfq` | N/A | mixed policy in one run |
| `qmt_order_intent` | `raw` | `raw` metadata only | `raw-only` | `qfq`, `hfq`, `returns_adjusted` as execution price |

QMT order intent may carry `research_adjustment_policy` metadata for audit, but execution must stay
raw / broker reference. Non-raw execution allowed count: `0`. Adjusted execution price pass count:
`0`.

## Governance And Scale-Up Boundary

CR017-S06 is a documentation and metadata contract story; it does not mark the whole CR017 batch as
verified by itself.

| Field | Value before CR017 verified |
|---|---:|
| production adjustment governance claim allowed count | `0` |
| scale_up allowed count | `0` |
| provider_fetch | `0` |
| lake_write | `0` |
| credential_read | `0` |
| current_pointer_publish | `0` |
| real_order_call | `0` |
| real_cancel_call | `0` |
| account_query_call | `0` |
| dependency_change | `0` |
| legacy_qfq_overwrite | `0` |

The release condition for production adjustment governance is CR017 S01-S06 CP7 PASS plus an
explicit downstream production governance gate. The release condition for `scale_up` also requires
the CR016 scale-up gate and explicit user authorization.

## Unsupported Execution Features

This migration guide does not claim support for true VWAP, minute, tick, Level2, order-match, or
microstructure impact cost execution.

| Feature | Current status |
|---|---|
| `real_vwap_execution` | unsupported / blocked |
| `minute_execution` | unsupported / blocked |
| `tick_execution` | unsupported / blocked |
| `level2_execution` | unsupported / blocked |
| `order_match_execution` | unsupported / blocked |
| `microstructure_impact_cost` | unsupported / blocked |

## Compatibility Rule

The compatible transition path is:

1. Preserve the legacy qfq baseline as read-only evidence.
2. Introduce `prices_raw` and `adj_factor` as source-of-truth contracts.
3. Build `prices_qfq`, `prices_hfq`, and `returns_adjusted` as derived views with lineage.
4. Require consumers to declare exactly one `research_adjustment_policy` per run.
5. Keep catalog publish, old report overwrite, and legacy qfq overwrite at zero until a later Story
   explicitly authorizes a different operation.
