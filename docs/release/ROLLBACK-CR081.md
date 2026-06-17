# CR081 Rollback

## Rollback Goal

Restore `quant-lab/process` from the backup directory if the external process symlink cannot be used.

## Backup

```text
/home/hyde/workspace/process.backup-cr081-20260617T083645
```

## Manual Rollback Steps

1. Ensure no process operation is running.
2. Remove or rename the symlink `/home/hyde/workspace/quant-lab/process`.
3. Move the backup directory back to `/home/hyde/workspace/quant-lab/process`.
4. Restore Git index if needed:

```bash
git restore --staged process
```

5. Verify:

```bash
test -f process/STATE.md
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .
```

## Not Authorized By CR081

Rollback does not authorize deleting `/home/hyde/workspace/process`, deleting backup directories, committing, pushing, data/reports operations, credentials, provider/lake/catalog or runtime.
