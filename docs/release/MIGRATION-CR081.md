# CR081 Migration

## Migration Summary

`process/**` was migrated from in-repo ownership to an external sibling process project.

```text
Before:
/home/hyde/workspace/quant-lab/process/

After:
/home/hyde/workspace/process/
/home/hyde/workspace/quant-lab/process -> ../process
```

## Git Index Impact

`git rm --cached -r process` was executed. This stages removals for tracked process files without deleting the working tree content. No commit or push was executed.

## Bootstrap

```bash
scripts/link-engineering-ledger.sh
```

Optional override:

```bash
PROCESS_LEDGER_ROOT=/path/to/process scripts/link-engineering-ledger.sh
```

## Compatibility

Tools that read `process/STATE.md`, `process/checks`, `process/checkpoints` or `process/changes` continue to work through the symlink.
