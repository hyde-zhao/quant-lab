# CR082 Rollback

## Rollback Trigger

Use rollback only if the project `process` symlink cannot read `STATE.md`, bootstrap fails, or the namespace layout blocks normal process ledger access.

## Rollback Steps

From `/home/hyde/workspace/quant-lab`:

```bash
ln -sfn ../process process
```

Then move the namespace content back to the flat root only if explicitly authorized by a separate rollback instruction. Do not delete `/home/hyde/workspace/process/quant-lab` or CR081 backup automatically.

## Verification

```bash
readlink process
test -f process/STATE.md
```

Expected rollback symlink:

```text
../process
```

## Boundaries

Rollback does not authorize Git commit/push, data/reports access, credential read, NAS content access, provider/lake/catalog operation, runtime, CR046 recovery or cleanup.
