---
status: "confirmed"
version: "0.2"
change_id: "CR-053"
complexity: "standard"
selected_option: "logical-nas-map-plus-manifest-first-transfer-and-cold-backup"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-14T10:59:13+08:00"
real_migration_authorized: false
nas_scan_authorized: false
nas_copy_authorized: false
git_push_authorized: false
---

# HLD CR053：quant-lab Migration Inventory and Dry-run

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-14 | host-orchestrator | 初版 CP3 HLD，覆盖 NAS 目录映射、传输方案、备份方案、dry-run 合同和真实迁移后置门禁 |
| 0.2 | 2026-06-14 | host-orchestrator | 按用户确认补充：Linux 研究机可统一映射 NAS 三分区但物理分层不混并；现有 `MARKET_DATA_LAKE_ROOT` 不调整；Windows 交易机只映射 package exchange |

## 1. 问题定义

CR051 已确认 `quant-lab` 是未来 canonical 项目名，`local_backtest` 作为 legacy alias 保留。CR053 要在真实迁移前给出可评审的 inventory / dry-run 方案，特别是 NAS 不扫描的前提下仍要明确 NAS 的逻辑目录如何使用、研究主机 / NAS / 交易主机之间如何传输数据、哪些数据需要备份以及如何备份。

### 目标

| 优先级 | 目标 | 度量方式 |
|---|---|---|
| P0 | 定义 6 个逻辑存储 root 和目录映射 | HLD 表格覆盖 repo、hot、warm、cold、package exchange、market data lake |
| P0 | 定义 4 条数据传输链路 | HLD 覆盖 research_pc->hot、hot->warm、warm->cold、hot->trading_pc |
| P0 | 定义备份 / 恢复策略 | 至少覆盖备份对象、频率、保留期、校验、恢复演练 |
| P0 | 保持不授权边界 | 明确 CR053 不扫描 NAS、不复制 / 删除 / 移动、不 push、不读凭据 |
| P1 | 为 CR058 真实迁移提供输入 | 输出 dry-run report contract 和后续 gate |

### 成功标准

- [ ] 目录映射表包含 6 个逻辑 root、每个 root 的主设备、允许内容、禁止内容和环境变量。
- [ ] 数据传输方案包含 4 条流向、每条流向的 staging、checksum、manifest 和失败处理。
- [ ] 备份方案包含 hot / warm / cold / Git / package exchange 五类对象的备份策略，且定义不少于 3 个恢复验收点。
- [ ] CP3 Decision Brief 包含不少于 5 个待人工决策项。
- [ ] 全文中真实 NAS 扫描、复制、删除、目录重命名、git push、凭据读取和 runtime 操作均为 not-authorized。

### 非目标

- 不扫描 NAS 当前真实目录。
- 不移动、复制、删除任何文件。
- 不创建真实 NAS 目录。
- 不读取 `.env`、token、账号、密码、session、cookie、private key。
- 不进行 provider fetch、lake write、catalog publish。
- 不连接 QMT / MiniQMT，不执行 submit / cancel / simulation / live。
- 不重命名当前工作目录，不改远端仓库名，不 git push / tag publish。

## 2. 架构灰区与方案形成记录

**CP3 讨论日志**：`process/discussions/CP3-CR053-HLD-DISCUSSION-LOG.md`
**CP3 讨论恢复点**：`process/checks/CP3-CR053-DISCUSSION-CHECKPOINT.json`

### Architecture Gray Areas

| 灰区 ID | 关键问题 | 为什么会影响架构 | 影响面 | 推荐讨论顺序 | canonical refs | 状态 |
|---|---|---|---|---|---|---|
| AGA-CR053-01 | NAS 不扫描时如何设计目录映射？ | 决定 root 命名、路径抽象、后续 CR058 迁移输入 | 数据 / 安全 / 文档 / 验证 | 1 | CR051 archive governance、用户新增要求 | selected |
| AGA-CR053-02 | 研究主机、NAS 和交易主机之间如何传输？ | 决定 package exchange、checksum、manifest 和交易主机权限 | 模块 / 安全 / 验证 | 2 | HOST-WORKFLOW.md、CR053 CP2 | selected |
| AGA-CR053-03 | 哪些数据要备份，备份到哪里？ | 决定 warm / cold 分层、保留期、恢复演练和风险接受 | 数据 / 运维 / 回退 | 3 | ARCHIVE-GOVERNANCE.md、用户新增要求 | selected |
| AGA-CR053-04 | dry-run 与真实迁移边界如何切分？ | 决定 CR053 / CR058 / CR059 职责，不切清会误授权 | 范围 / 安全 / 交付 | 4 | CP2 DQ-CR053-05 | selected |

### Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 逻辑 root + manifest-first transfer + warm/cold backup | 不扫描 NAS 也能设计；路径不硬编码；适合后续 dry-run 和回滚 | 需要后续 CR 才能验证真实容量和目录存在性 | 目录映射 / 传输 / 备份 / 安全 / 文档 | 推荐 | 当前不授权 NAS；若后续发现 NAS 权限和真实路径稳定，可在 CR058/CR060 扩展为真实路径验证 |
| B. 立即扫描 NAS 并按真实目录生成映射 | 真实度高，可发现现有目录差异 | 需要 NAS 授权；可能触碰大文件和敏感路径；超出 CR053 CP2 | NAS / 安全 / 运行授权 | 不推荐 | 仅当用户明确授权 NAS read-only inventory 且给出路径范围时切换 |
| C. 不设计 NAS，只设计 Git 内迁移 | 最小范围，最快 | 无法回答用户关于数据传输、目录映射和备份的问题 | 迁移 / 备份 / 后续 CR | 不推荐 | 仅当用户取消 NAS 相关需求时采用 |

## 3. 候选架构方案对比

### 方案 A：逻辑目录映射 + manifest-first 传输 + warm/cold 备份

核心思路：Git 内只保存逻辑 root、manifest、checksum、pointer 和 dry-run 报告；真实 NAS 路径由用户环境或后续 CR 授权挂载提供。传输采用 staging -> checksum -> manifest -> promote 的两阶段流程。

| 维度 | 评估 |
|---|---|
| 优点 | 不需要扫描 NAS；权限最小；可审计；后续 CR058 可直接消费 |
| 缺点 | 当前无法证明真实 NAS 目录已存在或容量足够 |
| 复杂度 | medium |
| 实施成本 | 中等，主要是报告和清单设计 |
| 可扩展性 | 可扩展到 NAS read-only inventory 和真实迁移 |
| 风险 | 真实路径与逻辑路径后续可能不一致 |
| 适用前提 | CP3 只做设计，不执行真实 NAS 操作 |

### 方案 B：真实 NAS read-only inventory

核心思路：授权只读扫描 NAS 后生成真实目录映射。

| 维度 | 评估 |
|---|---|
| 优点 | 能发现真实路径、容量和历史目录 |
| 缺点 | 需要外部存储授权，可能触碰大文件和敏感路径 |
| 复杂度 | high |
| 实施成本 | 高，需要权限、路径白名单、执行窗口和日志脱敏 |
| 可扩展性 | 高，但必须另起授权门 |
| 风险 | 越权读取、长耗时、误扫敏感目录 |
| 适用前提 | 用户明确授权 NAS read-only inventory |

### 方案 C：Git-only migration

核心思路：完全不考虑 NAS，只完成 repo relayout dry-run。

| 维度 | 评估 |
|---|---|
| 优点 | 最快，风险最低 |
| 缺点 | 不满足 NAS 目录映射、传输、备份需求 |
| 复杂度 | low |
| 实施成本 | 低 |
| 可扩展性 | 低，需要后续重做 NAS 设计 |
| 风险 | CR058 真实迁移时缺少 archive / backup 输入 |
| 适用前提 | 用户取消 NAS 方案要求 |

**推荐方案**：方案 A。

## 4. 推荐方案总览

**复杂度模式**：`standard`

**系统核心思路**：CR053 以逻辑 root 为单一设计面，生成可被 CR058 真实迁移消费的目录映射、数据传输和备份合同。真实路径、真实 NAS 读写、真实文件移动仍后置到独立授权门。

**核心能力边界**：

- 做：逻辑目录、传输流、备份策略、dry-run report contract、后续真实迁移 gate。
- 不做：真实 NAS scan、真实 copy/delete/move、真实 remote rename/push、真实凭据/runtime 操作。

## 5. NAS 逻辑目录映射

> 下面是逻辑映射，不是当前 NAS 真实目录声明；CR053 不创建目录、不扫描目录。

| 逻辑 root | 建议环境变量 | 主设备 / 层 | 建议相对目录 | 允许内容 | 禁止内容 | 备份等级 |
|---|---|---|---|---|---|---|
| Repo workspace | `QUANT_LAB_REPO_ROOT` | 研究主机 2T SSD | `~/workspace/quant-lab` | Git checkout、代码、docs、schema、小 fixture | raw data、凭据、大 artifact | Git commit / bundle |
| Hot cache | `QUANT_LAB_HOT_CACHE_ROOT` | NAS 512G SSD | `quant-lab/hot/cache` | 近期 run cache、临时 staging、可重建中间文件 | 唯一副本、凭据、broker raw facts | 可丢弃，不作为唯一备份 |
| Package exchange | `QUANT_LAB_PACKAGE_EXCHANGE_ROOT` | NAS 512G SSD | `quant-lab/hot/package-exchange` | zip、manifest、sha256、docs bundle | full research archive、未授权 runtime 文件 | warm manifest mirror |
| Research archive | `QUANT_LAB_RESEARCH_ARCHIVE_ROOT` | NAS 4T RAID | `quant-lab/archive/research` | run artifact、报告、模型、source attachment pointer、checksum | market data current truth、凭据 | primary durable |
| Market data lake alias | `QUANT_LAB_MARKET_DATA_LAKE_ROOT` | 既有 NAS data lake / 外置 lake | `quant-lab/lake/market-data` 或 legacy pointer | published market data、catalog pointer | research run artifact、broker facts | 按数据湖策略 |
| Cold backup | `QUANT_LAB_COLD_BACKUP_ROOT` | NAS 14T HDD | `quant-lab/cold-backup` | warm archive snapshot、git bundle、manifest snapshot、retired project backup | active workspace、未登记临时文件 | cold durable |
| Trading evidence | `QUANT_LAB_TRADING_EVIDENCE_ROOT` | 交易主机 512G SSD 或 broker archive | `quant-lab/trading-evidence` | 脱敏运行摘要、小型证据 | 凭据、未脱敏账户、full archive | 后续交易 CR |

### 主机映射约束

| 主机 | 推荐映射 | 允许范围 | 禁止范围 | 说明 |
|---|---|---|---|---|
| Linux 研究机 | 可同时挂载 NAS 512G SSD、4T RAID、14T HDD，并汇总到 `/mnt/quant-lab/*` 逻辑视图 | `/mnt/quant-lab/hot`、`/mnt/quant-lab/archive`、`/mnt/quant-lab/cold-backup` | 不把三个分区 overlay / merger 成一个职责不明的大盘 | Linux 研究机是主要挂载端；统一路径只是命名空间，物理层仍保持 hot / warm / cold 分离。 |
| Windows 交易机 | 只映射 package exchange | `Q:\quant-lab\package-exchange` 或 UNC `\\NAS\\<hot-share>\\quant-lab\\hot\\package-exchange` | 不映射 research archive、cold backup、完整 market data lake、完整研究 Git workspace | 交易机只读消费 zip / manifest / sha256 / docs bundle；可选写回脱敏 evidence inbox。 |
| 数据湖现有挂载 | 保持 `MARKET_DATA_LAKE_ROOT` / `--lake-root` 合同 | 由用户系统层挂载，项目只消费外置 lake root | CR053 不迁移、不改名、不替换现有 lake root 变量 | `QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅作为未来文档 alias / pointer，不作为现阶段代码入口。 |

### Linux 研究机逻辑视图建议

```text
/mnt/quant-lab/
  hot/                 -> NAS 512G SSD
    cache/
    package-exchange/
  archive/             -> NAS 4T RAID
    research/
    lake-pointers/
    package-manifest-mirror/
  cold-backup/         -> NAS 14T HDD
    git-bundles/
    archive-snapshots/
    restore-tests/
    retired-projects/
  lake/                -> 现有 MARKET_DATA_LAKE_ROOT 的挂载点或只读 pointer，不在 CR053 调整
```

底层可由用户系统层分别挂载，例如：

```text
/mnt/nas-ssd512/quant-lab/hot
/mnt/nas-raid4t/quant-lab/archive
/mnt/nas-hdd14t/quant-lab/cold-backup
```

再通过 bind mount 或 symlink 暴露到 `/mnt/quant-lab/*`。CR053 不创建这些目录，不执行 mount，不验证真实路径。

### 目录树建议

```text
<NAS_512G_SSD>/
  quant-lab/
    hot/
      cache/
      package-exchange/
        inbox/
        outbox/
        manifests/
        checksums/
        docs-bundles/
        staging/

<NAS_4T_RAID>/
  quant-lab/
    archive/
      research/
        projects/
        runs/
        reports/
        models/
        attachments/
        manifests/
        registry/
      lake-pointers/
      package-manifest-mirror/

<NAS_14T_HDD>/
  quant-lab/
    cold-backup/
      git-bundles/
      archive-snapshots/
        daily/
        weekly/
        monthly/
      restore-tests/
      retired-projects/
```

## 6. 数据传输方案

| 流向 | 传输对象 | 推荐方式 | 校验 | 失败处理 | 当前授权 |
|---|---|---|---|---|---|
| research_pc -> Git | code / docs / schema / manifest spec | `git add/commit` | tests / diff / review | revert commit | 已授权常规 Git 本地提交 |
| research_pc -> hot cache | 可重建 cache / staging | 后续授权后使用 mount / rsync / robocopy 等工具 | size + checksum for durable items | staging 清理，原始源不删 | not-authorized |
| hot cache -> warm archive | run artifact / report / model / package manifest mirror | manifest-first：先写 staging，再校验 sha256，再 promote | manifest + checksum + count | 不 promote，保留失败 manifest | not-authorized |
| warm archive -> cold backup | archive snapshot / git bundle / manifest snapshot | 增量 + 周期性完整快照 | snapshot manifest + restore sample | 标记 backup_failed，不删除 warm | not-authorized |
| package exchange -> trading_pc | strategy package zip / sha256 / manifest / docs bundle | 交易主机只读消费 package exchange | sha256 + source_commit + manifest schema | 缺 checksum / manifest 阻断导入 | not-authorized |
| trading_pc -> archive | 脱敏 runtime evidence summary | 后续 trading evidence gate | redaction_status + checksum | fail closed | not-authorized |

### 两阶段传输协议

1. `stage`：写入 `staging/`，生成临时 manifest。
2. `checksum`：计算 sha256、文件数量、总大小和 manifest hash。
3. `promote`：校验通过后原子移动到目标目录，写入 final manifest。
4. `record`：Git 中只保存 manifest pointer、schema、摘要和 checksum，不保存大文件正文。
5. `rollback`：promote 前失败只清 staging；promote 后失败用 manifest 反查并恢复到上一 snapshot。

## 7. 备份方案

### 数据湖映射兼容性

现有数据湖映射不在 CR053 中调整。当前仓库和 CLI 已以 `MARKET_DATA_LAKE_ROOT`、`MARKET_DATA_LAKE_ARCHIVE_ROOT`、`MARKET_DATA_LAKE_BACKUP_ROOT`、`MARKET_DATA_LAKE_RESTORE_ROOT` 作为数据湖运维合同；CR053 只确认这些 root 应继续保持在仓库外，并由用户系统层完成 NAS / 外置路径挂载。若未来需要移动真实 lake root，必须另起数据湖迁移 CR，先执行 backup / restore drill，再切换 `.env` 或运行参数。

### 备份等级

| 对象 | 主位置 | 备份位置 | 频率建议 | 保留期建议 | 恢复验收 |
|---|---|---|---|---|---|
| Git repo | 研究主机 2T SSD | NAS 14T `git-bundles/` | 每个迁移 gate 前生成 bundle | 至少保留到 CR058 CP8 + 30 天 | `git bundle verify` |
| manifest / registry | NAS 4T RAID | NAS 14T `archive-snapshots/*` | 每日增量 | daily 14 天、weekly 8 周、monthly 12 月 | 随机抽样读取 manifest |
| research reports / models | NAS 4T RAID | NAS 14T `archive-snapshots/*` | 每周完整或增量 | weekly 8 周、monthly 12 月 | 按 manifest 恢复 1 个 run |
| package exchange manifests | NAS 512G SSD + NAS 4T mirror | NAS 14T snapshot | 每次 package promote 后 | 与 package 生命周期一致 | sha256 复验 |
| hot cache | NAS 512G SSD | 无强制备份 | 不备份或短期快照 | TTL 7-14 天 | 可由源重新生成 |
| market data lake | 外置 lake | 沿用数据湖备份策略 | 不由 CR053 定义真实备份 | 按 CR010 / 数据湖策略 | 后续数据湖 gate |
| trading evidence | trading PC / broker archive | 后续交易证据备份 | 不由 CR053 执行 | 后续交易 CR | redaction + checksum |

### 备份原则

- Hot cache 不是可靠存储，不允许保存唯一副本。
- NAS 4T RAID 是 research archive 主层，不等于备份。
- NAS 14T HDD 是 cold backup / retired projects 层。
- Git 只备份代码、文档、schema、manifest 和小 fixture；不备份凭据或 raw data。
- 任何备份都必须有 manifest、checksum、created_at、source_root、target_root、redaction_status。
- 每次真实迁移前必须至少完成一次 restore rehearsal：从 cold backup 恢复 1 个 manifest + 1 个小型报告样本。

## 8. Dry-run Report Contract

| 报告 | 路径建议 | 内容 | 当前 CR053 是否执行 |
|---|---|---|---|
| Path inventory | `docs/release/MIGRATION-INVENTORY-CR053.md` 或 `process/research/migration/` | Git 内路径分类、owner、move_action、risk | 后续 CP6 才可能生成 |
| Path references | `docs/release/PATH-REFERENCES-CR053.md` | `local_backtest` / legacy env / docs links 引用清单 | 后续 CP6 才可能生成 |
| NAS logical map | `docs/release/NAS-MAPPING-CR053.md` | 本 HLD 的 logical root 到实际配置占位映射 | 后续 CP6 才可能生成 |
| Backup plan | `docs/release/BACKUP-PLAN-CR053.md` | 备份对象、频率、保留、恢复演练 | 后续 CP6 才可能生成 |
| Migration plan | `docs/release/MIGRATION-PLAN-CR053.md` | CR058 真实迁移步骤、回滚点和验收命令 | 后续 CP6 才可能生成 |

## 9. Use Case → Architecture Traceability

| Use Case | 支撑模块 / 组件 | 关键流程 | 异常 / 失败路径 | 验证方式 |
|---|---|---|---|---|
| SC-CR053-01 仓库路径 inventory | PathInventory | repo path -> classification -> report | 路径无法分类则标 `unknown-owner` | 静态报告审查 |
| SC-CR053-02 路径引用 dry-run | PathReferenceScanner | text refs -> owner -> action | 引用不可自动改写则标 manual-review | fixture / review |
| SC-CR053-03 禁止内容分类 | ForbiddenContentPolicy | pattern rules -> risk class | 命中 sensitive 则 fail closed | policy test |
| SC-CR053-04 Git 归档点设计 | GitArchivePlan | pre-inventory -> pre-move -> post-fix | 缺 rollback_ref 阻断 CR058 | checklist |
| 用户新增 NAS 目录 / 传输 / 备份需求 | NasMapping / TransferPlan / BackupPlan | logical roots -> transfer lanes -> backup classes | 真实路径缺失时保持 placeholder，不执行 | CP3 review |

## 10. 关键场景模拟

| 模拟 ID | 场景 | 输入 / 前置条件 | 推荐架构执行路径 | 预期输出 | 失败 / 回退路径 | 结果 |
|---|---|---|---|---|---|---|
| SIM-CR053-01 | 不扫描 NAS 也给出目录映射 | 已知 NAS 层级：512G SSD / 4T RAID / 14T HDD | 逻辑 root -> 相对目录 -> env var -> 禁止项 | NAS logical map | 真实路径未知时标 `requires-runtime-authorization` | PASS |
| SIM-CR053-02 | 研究报告入 archive | research_pc 生成 report | staging -> checksum -> manifest -> warm archive -> cold snapshot | report manifest + backup manifest | checksum mismatch 时不 promote | PASS |
| SIM-CR053-03 | 交易主机消费 package | package 已进入 hot exchange | trading_pc read-only -> sha256 verify -> docs review | package 可导入候选 | 缺 manifest/checksum 阻断 | PASS |
| SIM-CR053-04 | 真实迁移前恢复演练 | cold backup 有 manifest snapshot | restore sample -> verify checksum -> compare manifest | restore evidence | restore fail 阻断 CR058 | PASS |

## 11. ADR 候选点

| ADR ID | 决策 | 推荐方案 | 备选 | CP3 决策项 |
|---|---|---|---|---|
| ADR-CR053-001 | NAS 目录映射 | 逻辑 root + 环境变量 + 相对目录，不硬编码真实路径 | 立即扫描 NAS / Git-only | DQ-CP3-CR053-01 |
| ADR-CR053-002 | 数据传输方式 | manifest-first 两阶段传输 | 直接复制 / 同步整目录 | DQ-CP3-CR053-02 |
| ADR-CR053-003 | 备份分层 | 4T RAID 主 archive + 14T cold backup + Git bundle | 只依赖 RAID / 全量云备份 | DQ-CP3-CR053-03 |
| ADR-CR053-004 | 真实迁移时点 | CR058 CP6 执行 repo-local mechanical move | CR053 内执行 / 延后无限期 | DQ-CP3-CR053-04 |
| ADR-CR053-005 | 交易主机边界 | 只读 package exchange，不挂 full archive | 交易主机挂 archive | DQ-CP3-CR053-05 |
| ADR-CR053-006 | 现有数据湖映射 | 保持 `MARKET_DATA_LAKE_ROOT` / `--lake-root`，`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作 alias / pointer | 立即替换数据湖变量 / 在 CR053 中迁移 lake | DQ-CP3-CR053-01 refinement |
| ADR-CR053-007 | 主机挂载策略 | Linux 研究机挂三分区统一视图；Windows 交易机只映射 package exchange | 三分区混并 / Windows 交易机映射 full archive | DQ-CP3-CR053-05 refinement |

## 12. 待人工决策项

| 决策 ID | 类型 | 问题 | 推荐方案 | 备选方案 | 风险 / 回退 |
|---|---|---|---|---|---|
| DQ-CP3-CR053-01 | architecture | 是否采用逻辑 NAS root 映射？ | 是，按 512G hot、4T warm、14T cold 映射 | 立即扫描 NAS；只做 Git-only | 若真实路径不同，CR058 前调整 env mapping |
| DQ-CP3-CR053-02 | implementation | 是否采用 manifest-first 两阶段传输？ | 是，staging/checksum/promote/record | 直接复制；rsync mirror | 直接复制失败难回滚 |
| DQ-CP3-CR053-03 | architecture | 是否采用 warm archive + cold backup 分层？ | 是，4T RAID 主 archive，14T cold backup | 只依赖 RAID；hot SSD 也备份 | 只依赖 RAID 不满足备份 |
| DQ-CP3-CR053-04 | runtime_authorization | 真实迁移何时执行？ | CR058 CP5 approved 后的 CR058 CP6 | CR053 CP6 执行；暂不规划 | CR053 仍不授权真实迁移 |
| DQ-CP3-CR053-05 | security | 交易主机是否只读消费 package exchange？ | 是，不挂 full archive | 交易主机挂 archive；交易主机保存完整研究仓库 | 降低交易主机暴露面 |

### 已确认细化项

| 细化项 | 决策 | 影响 |
|---|---|---|
| NAS 三分区能否一起映射 | 可以在 Linux 研究机统一映射到 `/mnt/quant-lab/*`，但底层仍是三个独立分区，不做职责混并。 | CP4/CP5 设计应生成 logical map / mount map schema，但不执行 mount。 |
| 当前数据湖映射是否调整 | 不调整。继续使用 `MARKET_DATA_LAKE_ROOT` / 显式 `--lake-root`；`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作为文档 alias / pointer。 | 避免破坏已验证的数据湖 CLI、backup / restore 和 publish gate。 |
| Windows 交易机是否映射 | 只映射 package exchange，默认 read-only；不映射 research archive / cold backup / full lake。 | package import 后续必须校验 manifest / sha256。 |
| Linux 研究机是否都可映射 | 可以，是主要映射端；可同时挂载 hot / archive / cold-backup 三层。 | 后续真实路径绑定仍需用户授权或提供配置。 |

## 13. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 逻辑目录与真实 NAS 路径不一致 | MEDIUM | CR058 前要求用户提供实际 mount / share mapping 或授权 read-only inventory |
| 备份策略未真实执行 | MEDIUM | CR053 只写计划；CR058 / CR060 必须有 backup evidence gate |
| Hot cache 被误当长期存储 | HIGH | HLD 明确 hot cache 无强制备份、TTL 7-14 天、不得保存唯一副本 |
| 交易主机暴露 full archive | HIGH | 交易主机只读 package exchange，full archive mount blocked |
| 凭据被备份 | HIGH | `.env` / token / account / key 默认 blocked-sensitive，不进入 Git / archive / backup |

## 14. Gotchas

- RAID 不是备份；NAS 4T RAID 只是 warm archive 主层，真正 cold backup 在 14T HDD。
- Hot cache 不是长期保存层，任何只有 hot cache 一份的 artifact 都视为未归档。
- `QUANT_LAB_*_ROOT` 只是逻辑变量，不代表当前机器已有挂载路径。
- CR053 CP3 approve 仍不授权创建 NAS 目录、复制数据或运行 inventory。
- 交易主机只消费 package，不承担 research archive 或研究开发职责。

## 15. 分阶段落地建议

| 阶段 | 内容 | 输出 | 是否真实迁移 |
|---|---|---|---|
| CR053 CP3 | 本 HLD / ADR / CP3 决策 | HLD、ADR、CP3 checkpoint | 否 |
| CR053 CP4/CP5 | Story / LLD 批次 | inventory / backup / transfer 设计证据 | 否 |
| CR053 CP6 | 生成 Git 内静态报告 | dry-run reports | 否，除非后续明确授权 repo-local 静态命令 |
| CR053 CP8 | dry-run 关闭 | release decision | 否 |
| CR058 CP6 | repo-local mechanical migration | 文件移动、引用修正、验证 | 是，仅限本地 Git 仓库 |
| CR060+ | NAS / archive 实迁 | NAS copy / sync / backup evidence | 需独立授权 |

## 16. 自审

| 检查项 | 结果 | 说明 |
|---|---|---|
| 至少 2 个候选方案 | PASS | A/B/C 三个方案 |
| Architecture Gray Areas | PASS | AGA-CR053-01..04 |
| Use Case Traceability | PASS | 覆盖 SC-CR053-01..04 和用户新增 NAS 需求 |
| 场景模拟 | PASS | 4 个模拟均 PASS |
| CP3 决策项 | PASS | DQ-CP3-CR053-01..05 |
| 不授权项 | PASS | 全文明确不扫描 NAS、不复制、不迁移、不 push、不读凭据 |
