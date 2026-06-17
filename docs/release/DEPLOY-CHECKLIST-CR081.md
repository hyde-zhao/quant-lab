# CR081 Deploy Checklist

| Item | Status | Evidence |
|---|---|---|
| External process directory exists | PASS | `/home/hyde/workspace/process` |
| Process symlink exists | PASS | `/home/hyde/workspace/quant-lab/process -> ../process` |
| `STATE.md` readable through symlink | PASS | `test -f process/STATE.md` |
| External README exists | PASS | `/home/hyde/workspace/process/README.md` |
| Backup exists | PASS | `/home/hyde/workspace/process.backup-cr081-20260617T083645` |
| Bootstrap script executable and repeatable | PASS | `scripts/link-engineering-ledger.sh` |
| Git index externalization visible | PASS_WITH_RISK | 1572 staged `process/**` removals |
| Remote write skipped | PASS | Not authorized |

## Operator Notes

Do not commit or push the staged `process/**` removals until CP8 is approved and the user explicitly decides the Git publication boundary.
