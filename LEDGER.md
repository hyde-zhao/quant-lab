# Process Ledger

本项目的过程台账已经通过 CR081 迁移到仓库外部 process project，并通过 CR082 归档到项目命名空间：

```text
/home/hyde/workspace/process/quant-lab
```

当前业务项目只保留本地软链接入口：

```text
/home/hyde/workspace/quant-lab/process -> ../process/quant-lab
```

`process/` 中的 `STATE.md`、`changes/`、`checks/`、`checkpoints/`、`context/`、`release/`、`stories/` 等文件由外部 process project 管理，不再由当前业务项目 Git 直接跟踪。当前项目 Git 仅跟踪本说明、`ledger.yaml`、`.gitignore` 规则和 bootstrap 脚本。

新环境恢复时：

1. 准备外部 process project，并确保 `quant-lab` namespace 位于 `/home/hyde/workspace/process/quant-lab`。
2. 在当前项目根目录运行：

```bash
scripts/link-engineering-ledger.sh
```

如需使用其他路径：

```bash
PROCESS_LEDGER_ROOT=/path/to/process/quant-lab scripts/link-engineering-ledger.sh
```

CR081 / CR082 不授权 `data/`、`reports/` 内容读取或迁移，不授权凭据读取，不授权远端 Git push，不授权 QMT / MiniQMT runtime。
