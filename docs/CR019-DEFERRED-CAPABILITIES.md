---
title: "CR019 Deferred Capability Register"
change_id: "CR-019"
story_id: "CR019-S09-deferred-capability-register"
status: "controlled-offline-register"
created_at: "2026-05-31T09:33:00+08:00"
stage6_p0_dependency_additions: 0
real_operation_permission_claims: 0
---

# CR019 Deferred Capability Register

This register is a static scope contract for CR-019. It does not enable a runtime
feature, add a dependency, start a provider connection, request market data, or
grant trading permission. Every entry below remains outside the Stage 6 P0
admission and QMT C/S bridge implementation scope until a later CR completes its
own CP2 / CP3 / Story Plan / CP5 / CP6 / CP7 path.

## Global Boundary

| Boundary | Value |
|---|---|
| Stage 6 P0 dependency additions | `0` |
| QMT C/S bridge dependency additions | `0` |
| Runtime feature flags introduced here | `0` |
| Real provider or broker operations | `0` |
| Credential reads | `0` |
| Data acquisition jobs | `0` |
| Real trading permission claims | `0` |

## Follow-up Tracking Index

后续跟踪台账为 `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md`。当前 register 只登记后置能力边界；所有候选项必须先创建独立 CR / Spike 并重新通过 CP2 / CP3 / CP5 / CP6 / CP7，不能由本 register 自动启用。

| capability_id | follow-up candidate | tracking status |
|---|---|---|
| `backtrader_w6` | `CR-025 Backtrader optional execution backend hardening` | `candidate` |
| `qlib_w7` | `CR-026 Qlib isolated runner / factor workflow boundary` | `candidate` |
| `minute_spike` | `CR-027 Minute data feasibility Spike` | `spike_candidate` |
| `level2_spike` | `CR-028 Level2 rights and microstructure Spike` | `spike_candidate` |

## Deferred Capability Register

### backtrader_w6

| Field | Value |
|---|---|
| Current status | `deferred` |
| Non-P0 reason | Stage 6 P0 focuses on daily multifactor admission, benchmark readiness, and QMT bridge contracts. Promoting Backtrader into W6 execution semantics would add event-driven order, fill, position, and risk-analysis scope beyond the current admission gate. |
| Trigger conditions | 1. Clean OHLCV / factor / score feed is published through quality gate, PIT check, adjustment policy, and benchmark policy.<br>2. Candidate Stage 6 strategies remain stable after production-current-truth reruns and ablation / robustness checks.<br>3. The team needs an execution-semantics comparison that the lightweight daily engine cannot answer. |
| Blocked reason | `backtrader_w6_deferred`: clean feed and execution-comparison evidence are not sufficient to change Stage 6 P0 admission or QMT bridge behavior in this CR. |
| Required evidence | Clean feed contract, quality gate pass, PIT / adjustment proof, benchmark readiness, candidate strategy stability report, lightweight-engine comparison gap, and W6 risk / cost model assumptions. |
| Next CR / CP entry | New CR with CP2 scope decision, CP3 HLD / ADR refresh, Story Plan, CP5 LLD approval, CP6 coding, and CP7 verification before any W6 implementation or dependency change. |
| Forbidden claims | No new package requirement in this Story; no replacement of the lightweight engine; no automatic data repair; no connector or credential access; no trading or broker operation permission. |
| Revisit condition | Revisit only when the Stage 6 daily path is stable and the missing event-driven execution evidence is the top blocker for admission or QMT dry-run interpretation. |

### qlib_w7

| Field | Value |
|---|---|
| Current status | `deferred` |
| Non-P0 reason | Qlib W7 requires an isolated factor / ML workflow, runner I/O contract, and report catalog. Those concerns are outside the current daily admission package and QMT C/S bridge contract. |
| Trigger conditions | 1. Factor panel and label windows are frozen with PIT / `available_at` proof.<br>2. Research report catalog and experiment lineage can be consumed without turning Qlib output into the sole source of truth.<br>3. Isolated runner inputs, outputs, error model, and storage boundary are defined in a separate HLD / ADR. |
| Blocked reason | `qlib_w7_deferred`: factor panel, report catalog, and isolated runner contracts are not frozen for implementation in this Story. |
| Required evidence | Factor panel schema, label / horizon contract, PIT proof, report catalog schema, isolated runner I/O contract, failure-mode matrix, dependency isolation plan, and source-of-truth boundary. |
| Next CR / CP entry | New CR for W7 isolated runner and factor workflow, followed by CP2 / CP3 / CP5 gates and fixture-only CP6 / CP7 before any runtime integration. |
| Forbidden claims | No provider path or URI value; no runtime initialization call; no direct feature pull from Qlib data APIs; no dependency addition; no claim that Qlib output replaces current lake / engine truth. |
| Revisit condition | Revisit when Stage 6 factor research needs ML workflow comparison and the factor panel plus report catalog are stable enough to test in an isolated runner. |

### minute_spike

| Field | Value |
|---|---|
| Current status | `spike_candidate` |
| Non-P0 reason | Minute-bar work changes storage volume, data quality policy, latency assumptions, cost model, and execution realism. It is a data / microstructure Spike, not part of the current daily P0 admission gate. |
| Trigger conditions | 1. Daily execution assumptions fail a documented realism test or create an unresolvable slippage / timing gap.<br>2. A source, schema, storage, quality audit, and retention plan for minute bars are approved.<br>3. A bounded experiment defines symbols, dates, expected cost-model questions, and rollback criteria. |
| Blocked reason | `minute_spike_blocked`: no approved minute-bar source, storage contract, quality audit, or bounded experiment exists in CR-019 S09. |
| Required evidence | Experiment gap report, source / interface allowlist, minute-bar schema, quality denominator, retention and cost estimate, PIT / availability rule, and fixture-only parser plan. |
| Next CR / CP entry | New Spike CR with CP2 scope, CP3 data architecture, CP5 LLD, and a CP6 / CP7 fixture-only validation before any real acquisition request. |
| Forbidden claims | No historical minute-bar pull; no live collection; no provider operation; no lake write; no execution-price claim upgrade; no claim that minute bars are required by current Stage 6 P0. |
| Revisit condition | Revisit when daily-bar evidence cannot explain execution gaps and the team can fund a bounded source / storage / quality experiment. |

### level2_spike

| Field | Value |
|---|---|
| Current status | `spike_candidate` |
| Non-P0 reason | Level2 work depends on paid market-data rights, order-book schema, queue modeling, impact-cost validation, storage scale, and audit controls. These are outside Stage 6 daily admission and QMT bridge contracts. |
| Trigger conditions | 1. L1 and minute-bar evidence are insufficient for a material order-book, queue, or impact-cost risk.<br>2. Data rights, cost, retention, redaction, and audit rules are documented without exposing any credential or private entitlement detail.<br>3. A microstructure Spike defines replay scope, error model, and success / rollback criteria. |
| Blocked reason | `level2_spike_blocked`: no approved data-rights evidence, order-book schema, queue model, storage plan, or microstructure audit exists for this Story. |
| Required evidence | Data-rights confirmation artifact, order-book schema, queue / impact-cost hypothesis, storage estimate, quality audit matrix, redaction rule, and bounded replay fixture. |
| Next CR / CP entry | New Level2 Spike CR with explicit data-rights review, CP3 architecture decision, CP5 LLD, CP6 fixture implementation, and CP7 safety verification. |
| Forbidden claims | No claim of paid access; no sample order-book data; no real feed connection; no live quote capture; no broker or QMT permission; no upgrade of current VWAP / order-match claims. |
| Revisit condition | Revisit only when order-book depth, queue position, or impact cost becomes a primary quantified blocker and simpler L1 / minute evidence cannot close the gap. |

## Non-Goals

- Do not add dependencies or modify lock files.
- Do not connect any provider, broker, QMT, MiniQMT, XtQuant, service, socket, lake,
  publisher, simulation, or live run path.
- Do not read `.env`, token, password, account, cookie, session, private key, or
  other credential material.
- Do not write a real Qlib provider setting, Level2 access statement, minute-bar
  acquisition configuration, or real market-data sample.
- Do not add any of these capabilities to Stage 6 P0 admission, QMT C/S bridge
  required dependencies, or current run permission.
