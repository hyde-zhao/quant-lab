# CR082 Deploy Checklist

## Local Deployment

| Step | Status | Evidence |
|---|---|---|
| Create namespace `/home/hyde/workspace/process/quant-lab` | done | Execution evidence |
| Move flat root ledger into namespace | done | Execution evidence |
| Update project symlink | done | `readlink process` -> `../process/quant-lab` |
| Update pointer files | done | `LEDGER.md`, `ledger.yaml`, script |
| Validate bootstrap | done | `scripts/link-engineering-ledger.sh` PASS |

## Before Any Git Publication

| Step | Status | Notes |
|---|---|---|
| Review staged `process/**` removals | pending | CR078 scope |
| Decide commit boundary | pending | CR078 scope |
| Decide remote push | pending | CR078 scope |

## Non-Authorized

Do not perform Git commit/push, remote write, NAS content operation, data/reports content access, credential read, runtime, CR046 recovery or cleanup under CR082 CP8 approval.
