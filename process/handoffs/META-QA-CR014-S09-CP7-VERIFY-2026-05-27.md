---
handoff_id: "META-QA-CR014-S09-CP7-VERIFY-2026-05-27"
from: "meta-po"
to: "meta-qa"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
batch_id: "CR014-REAL-RUN-BATCH-B"
status: "dispatched"
created_at: "2026-05-27T11:40:10+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6785-1a23-7953-bfe9-daa014abcc1e"
  agent_name: "qa-jin the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-27T11:40:40+08:00"
  completed_at: "2026-05-27T11:47:51+08:00"
  closed_at: "2026-05-27T11:47:51+08:00"
---

# META-QA CR014-S09 CP7 Verification Handoff

## Task

Perform CP7 verification for `CR014-S09-windowed-real-fetch-lake-write-run` and write:

- `process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md`

## Required Inputs

- `process/stories/CR014-S09-windowed-real-fetch-lake-write-run.md`
- `process/stories/CR014-S09-windowed-real-fetch-lake-write-run-LLD.md`
- `process/checks/CP5-CR014-S09-windowed-real-fetch-lake-write-run-LLD-IMPLEMENTABILITY.md`
- `checkpoints/CP5-CR014-S09-REAL-RUN-BATCH-B-LLD-REVIEW.md`
- `process/checks/CP6-CR014-S09-windowed-real-fetch-lake-write-run-CODING-DONE.md`
- `market_data/windowed_run.py`
- `market_data/runtime.py`
- `market_data/manifest.py`
- `market_data/lake_layout.py`
- `market_data/cli.py`
- `tests/test_cr014_windowed_real_run_contract.py`

## Verification Scope

- Verify S09 contract implementation only.
- Use fake provider, tmp paths, fixture/isolated tests, static scans and CP6 evidence.
- Confirm the default pilot window is `2026-01-01..2026-05-26`.
- Confirm S09 run gate is fail-closed without authorization and without explicit gate result.
- Confirm window planning, fake success, partial failure, resume conflict, rollback preview,
  manifest publish boundary, no publish/current pointer, no retention execute, no DuckDB open/write/dependency.
- Confirm path guard rejects old repo `data/**`, old `reports/**`, credential-like paths, and `.duckdb` roots.

## Required Commands

- Compile touched Python files.
- Run `tests/test_cr014_windowed_real_run_contract.py`.
- Run the CR014 regression subset:
  - `tests/test_cr014_p0_pipeline_contract.py`
  - `tests/test_cr014_catalog_publish_gate.py`
  - `tests/test_cr014_incremental_replay_retention.py`
- Run `.duckdb` file scan.
- Run DuckDB dependency scan on `pyproject.toml` and `uv.lock`.
- Run static scans proving no `real_run_authorized=true` or positive real side-effect counters are present in S09 evidence.

## Forbidden Scope

- Do not execute a real provider fetch.
- Do not write a real lake outside tmp paths.
- Do not read `.env`, credentials, tokens, cookies, passwords, or environment variable values.
- Do not publish current pointer.
- Do not execute retention.
- Do not open/write DuckDB, add DuckDB dependency, or create `.duckdb` files.
- Do not modify docs, README, dependency files, `.env`, `data/**`, `reports/**`, or unrelated tests.

## CP7 Required Content

- Entry Criteria.
- Checklist.
- Exit Criteria.
- Deliverables.
- 8-dimension verification summary.
- Agent Dispatch Evidence with this handoff and spawned agent id.
- Command results.
- Forbidden-operation counters.
- Final PASS/FAIL conclusion.
- Explicit statement: CP7 PASS, if achieved, verifies S09 code contract only and still does not authorize the real 2026 YTD run.

## Completion Summary

- CP7 produced: `process/checks/CP7-CR014-S09-windowed-real-fetch-lake-write-run-VERIFICATION-DONE.md`.
- CP7 status: `PASS`.
- Targeted S09 tests passed: `10 passed`.
- CR014 regression subset passed: `24 passed`.
- No `.duckdb` files, no DuckDB dependency, no real provider fetch, no real lake write, no credential read.
- CP7 verifies the S09 code contract only; the real 2026 YTD run still requires per-run authorization.
