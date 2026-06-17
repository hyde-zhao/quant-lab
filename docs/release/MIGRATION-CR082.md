# CR082 Migration

## Migration Summary

CR082 migrated the external process ledger from a flat root model to a project namespace model:

```text
/home/hyde/workspace/process
  README.md
  quant-lab/
    STATE.md
    changes/
    checks/
    checkpoints/
    context/
    release/
    stories/
    ...
```

The business project entry is:

```text
/home/hyde/workspace/quant-lab/process -> ../process/quant-lab
```

## Bootstrap

```bash
cd /home/hyde/workspace/quant-lab
scripts/link-engineering-ledger.sh
```

For a custom namespace path:

```bash
PROCESS_LEDGER_ROOT=/path/to/process/quant-lab scripts/link-engineering-ledger.sh
```

## Compatibility

Relative `process/...` references from the quant-lab project remain valid because the project symlink points directly to the namespace.

Historical CR081 evidence may still mention `/home/hyde/workspace/process` as the quant-lab ledger root; those records are retained as audit history.
