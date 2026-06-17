# Process Ledger

本项目的过程台账已经迁移到仓库外部 meta-flow-artifacts project，并通过 CR088 纠正到当前项目命名空间：

```text
/home/hyde/workspace/meta-flow-artifacts/process/quant-lab
```

当前业务项目只保留本地软链接入口：

```text
/home/hyde/workspace/quant-lab/process -> ../meta-flow-artifacts/process/quant-lab
```

`process/` 中的 `STATE.md`、`changes/`、`checks/`、`checkpoints/`、`context/`、`release/`、`stories/` 等文件由外部 process project 管理，不再由当前业务项目 Git 直接跟踪。CR087 进一步把过程 / 审计文档归档到同一个 namespace：

```text
/home/hyde/workspace/meta-flow-artifacts/process/quant-lab/docs
```

当前业务项目保留这些旧路径作为本地可读入口：

```text
/home/hyde/workspace/quant-lab/docs/design -> ../../meta-flow-artifacts/process/quant-lab/docs/design
/home/hyde/workspace/quant-lab/docs/features -> ../../meta-flow-artifacts/process/quant-lab/docs/features
/home/hyde/workspace/quant-lab/docs/quality -> ../../meta-flow-artifacts/process/quant-lab/docs/quality
/home/hyde/workspace/quant-lab/checkpoints -> ../meta-flow-artifacts/process/quant-lab/checkpoints
```

CR090 后，源码 `docs/` 只保留组件用户手册、安装 / 运行说明、quickstart / reference manual 和 `docs/release/RELEASE-NOTES.md`。`DEPLOY-CHECKLIST.md`、`ROLLBACK.md`、`MIGRATION.md`、`FEEDBACK.md`、路线图、CR 合同 / register、研究治理规格和内部 release manifest 均归档到：

```text
/home/hyde/workspace/meta-flow-artifacts/process/quant-lab/docs/source-archive/docs
```

当前项目 Git 仅跟踪本说明、`ledger.yaml`、`.gitignore` 规则、用户文档入口和 bootstrap 脚本；外部 process namespace 保存运行态与过程文档。

新环境恢复时：

1. 准备外部 meta-flow-artifacts project，并确保 `quant-lab` namespace 位于 `/home/hyde/workspace/meta-flow-artifacts/process/quant-lab`，且存在 `process/.meta-flow-process.yaml`。
2. 在当前项目根目录运行：

```bash
scripts/link-engineering-ledger.sh
```

如需使用其他路径：

```bash
PROCESS_LEDGER_ROOT=/path/to/process/quant-lab scripts/link-engineering-ledger.sh
```

CR081 / CR082 / CR087 / CR088 / CR090 不授权 `data/`、`reports/` 内容读取或迁移，不授权凭据读取，不授权 NAS 内容操作，不授权 QMT / MiniQMT runtime。旧 `/home/hyde/workspace/process/quant-lab` 仅作为遗留副本保留，未删除。
