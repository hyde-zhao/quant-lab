# CR081 Release Notes

## Decision

Release readiness: `READY_WITH_RISK`.

## What Changed

- Created external process project at `/home/hyde/workspace/process`.
- Mirrored existing `quant-lab/process/**` into that external process project.
- Added `/home/hyde/workspace/process/README.md`.
- Replaced `/home/hyde/workspace/quant-lab/process` with symlink `../process`.
- Added `LEDGER.md`, `ledger.yaml` and `scripts/link-engineering-ledger.sh` to the main project.
- Updated `.gitignore` so the current project no longer tracks the local `process` entry.
- Stopped Git index tracking for existing `process/**` files with `git rm --cached -r process`.

## Known Risks

- R-CR081-001: `process/**` staged removals require a later commit decision.
- R-CR081-002: `process/` depends on sibling external directory availability.
- R-CR081-003: new clones must run bootstrap to recreate the symlink.

## Not Included

- No Git commit or push.
- No remote Git governance.
- No `data/` or `reports/` content validation.
- No credential, NAS content, provider/lake/catalog or runtime operation.
