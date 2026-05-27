---
handoff_id: "META-DEV-CR014-S06-IMPLEMENTATION-2026-05-27"
from: "meta-po"
to: "meta-dev"
change_id: "CR-014"
story_id: "CR014-S06-incremental-refresh-replay-retention-contract"
status: "completed"
created_at: "2026-05-27T08:31:01+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e66d8-99d0-7823-9a85-5d850d07e8e7"
  agent_name: "dev-zhu"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-27T08:32:14+08:00"
  completed_at: "2026-05-27T08:40:10+08:00"
  closed_at: "2026-05-27T08:46:07+08:00"
---

# META-DEV CR014-S06 Implementation Handoff

## Task

Implement `CR014-S06-incremental-refresh-replay-retention-contract` while S04 CP7 runs in parallel.

## Allowed Write Scope

- `market_data/incremental.py`
- `market_data/replay.py`
- `market_data/retention.py`
- `tests/test_cr014_incremental_replay_retention.py`
- `process/checks/CP6-CR014-S06-incremental-refresh-replay-retention-contract-CODING-DONE.md`

## Read-Only Shared Inputs

- `market_data/catalog.py`
- `market_data/runtime.py`
- `market_data/manifest.py`
- `market_data/lake_layout.py`
- `market_data/contracts.py`
- S02/S03 CP6 / CP7 inputs as contract references.

## Forbidden Scope

- S04-owned files: `market_data/duckdb_query.py`, `market_data/audit.py`, `tests/test_cr014_duckdb_readonly_boundary.py`
- S03-owned files: `market_data/cli.py`, `market_data/runtime.py`, `market_data/normalization.py`, `market_data/validation.py`, `tests/test_cr014_p0_pipeline_contract.py`
- S01/S02 shared contract files: `market_data/contracts.py`, `market_data/manifest.py`, `market_data/catalog.py`, `market_data/publish.py`, `market_data/lake_layout.py`
- `.env`, `data/**`, `reports/**`, `pyproject.toml`, `uv.lock`, README/docs, DEV-LOG, Story files, STATE, STORY-STATUS, S05/S07/S08/S09 files

## Required Evidence

- Replay side-effect counters must stay 0: `provider_fetches=0`、`credential_reads=0`、`raw_writes=0`、`current_pointer_changes=0`.
- Retention must default to dry-run recommendation; no delete, archive, migration, or published truth mutation.
- Resume conflict must return structured output and never silently overwrite.
- Incremental plan must output affected partitions and stable idempotency / skip / retry plan without provider or lake side effects.
- CP6 must include Entry Criteria, Checklist, Exit Criteria, Deliverables, command results, Agent Dispatch Evidence, forbidden-operation counters, and final PASS/FAIL.

## Result

- CP6 status: `PASS`
- Result file: `process/checks/CP6-CR014-S06-incremental-refresh-replay-retention-contract-CODING-DONE.md`
- Summary: S06 targeted tests `7 passed`；S02/S03/S06 regression `24 passed`；S01/S02/S03/S06 regression `32 passed`；market_data compatibility regression `36 passed`；static forbidden-op scan and cache scan clean；all forbidden-operation counters remain 0.
