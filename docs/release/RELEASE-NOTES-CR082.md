# CR082 Release Notes

## Status

Release decision: `READY_WITH_RISK`.

## Changes

- External process ledger container remains at `/home/hyde/workspace/process`.
- Quant-lab process ledger now lives at `/home/hyde/workspace/process/quant-lab`.
- Project symlink now points to `../process/quant-lab`.
- `LEDGER.md`, `ledger.yaml`, `.gitignore` comments and `scripts/link-engineering-ledger.sh` were updated.
- Root process README now describes the multi-project namespace convention.

## Risks

- R-CR082-001: staged `process/**` removals remain and must be governed by CR078.
- R-CR082-002: future process projects must use namespace convention.
- R-CR082-003: historical evidence may mention the old CR081 flat root path.

## Not Included

- Git commit / push / remote governance
- data/reports content work
- credentials
- NAS content work
- provider / lake / catalog operation
- QMT / MiniQMT runtime
- CR046 recovery
- cleanup or backup deletion
