---
handoff_id: "META-DEV-CR014-S09-IMPLEMENTATION-2026-05-27"
from: "meta-po"
to: "meta-dev"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
batch_id: "CR014-REAL-RUN-BATCH-B"
status: "shutdown-incomplete"
created_at: "2026-05-27T11:10:21+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e676b-9ab1-7fa3-860b-f32430ce9e65"
  agent_name: "dev-qin the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-27T11:12:50+08:00"
  completed_at: ""
  closed_at: "2026-05-27T11:29:03+08:00"
shutdown_reason: "Agent remained running after two waits and did not produce CP6; meta-po closed the agent and will dispatch a narrower completion task."
---

# META-DEV CR014-S09 Implementation Handoff

## Task

Implement the S09 windowed run contract and produce CP6 coding-done evidence.

## Required Inputs

- `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md`
- `process/stories/CR014-S09-windowed-real-fetch-lake-write-run-LLD.md`
- `process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md`
- `checkpoints/CP5-CR014-S09-REAL-RUN-BATCH-B-LLD-REVIEW.md`
- `market_data/runtime.py`
- `market_data/manifest.py`
- `market_data/lake_layout.py`
- `market_data/cli.py`

## Allowed Write Scope

- `market_data/windowed_run.py`
- `market_data/runtime.py`
- `market_data/manifest.py`
- `market_data/lake_layout.py`
- `market_data/cli.py`
- `tests/test_cr014_windowed_real_run_contract.py`
- `process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md`
- `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md`

## Implementation Requirements

- Implement S09 windowed run contract for `2026-01-01..2026-05-26` as default pilot option, without executing real provider calls.
- Provide pure/isolated functions or dataclasses for:
  - S09 authorization building and missing-field diagnostics.
  - Window planning for month / quarter / trading-day chunk policies.
  - Run gate that fails closed when CP5, dev gate, implementation allowance, `authorization_id`, dataset/date/source/lake/window/resume/rollback/credential policies are missing.
  - Window execution against a fake provider / test writer using `tmp_path`.
  - Failure metadata, resume token, request fingerprint and resume conflict detection.
  - Run summary with `current_pointer_changes=0`, `publish_count=0`, `retention_execute_count=0`, `duckdb_*` counters 0.
- Integrate CLI only as offline-safe plan/gate entry if needed; default behavior must remain no real fetch.
- Keep `real_run_authorized=false` in Story / evidence; do not produce a real-run command.
- Add tests in `tests/test_cr014_windowed_real_run_contract.py` covering unauthorized fail-closed, 2026 YTD window split, fake success write, partial failure, resume conflict, rollback preview, no publish, no DuckDB.
- Produce CP6 with Entry Criteria, Checklist, Exit Criteria, Deliverables, Agent Dispatch Evidence, command results, forbidden counters, and final PASS/FAIL.

## Forbidden Scope

- Do not modify docs, README, `pyproject.toml`, `uv.lock`, `.env`, `data/**`, `reports/**`, old reports, catalog current pointer files, DuckDB files, or unrelated tests.
- Do not execute real provider fetch, real lake write outside `tmp_path`, credential read, publish, retention execute, DuckDB open/write, or S09 real run.
- Do not introduce DuckDB dependency or create `.duckdb` files.
- Do not mark S09 `verified`; meta-po and meta-qa own CP7 and final status.

## Required Verification

- Run targeted py_compile for changed Python files.
- Run `tests/test_cr014_windowed_real_run_contract.py`.
- If feasible, run relevant CR014 regression subset touching runtime / manifest / layout / CLI:
  - `tests/test_cr014_p0_pipeline_contract.py`
  - `tests/test_cr014_catalog_publish_gate.py`
  - `tests/test_cr014_incremental_replay_retention.py`
- Confirm forbidden operation counters remain 0 and no `.duckdb` file exists.

## Shutdown Note

This handoff produced partial S09 code and tests in the workspace but did not produce
`process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md`
before shutdown. A follow-up completion handoff owns CP6 closure.
