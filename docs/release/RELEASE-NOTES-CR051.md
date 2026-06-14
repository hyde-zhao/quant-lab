---
status: "READY"
version: "1.0"
change_id: "CR-051"
release_artifact_profile: "compact"
created_at: "2026-06-14T09:00:24+08:00"
---

# Release Notes: CR051 Strategy Research Lifecycle Framework

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版 CR051 发布说明，面向策略研究生命周期、归档治理、项目身份和后续 CR gate |

## 发布结论

| 字段 | 内容 |
|---|---|
| release_decision | READY |
| profile | compact |
| 验证 | CP6 PASS、CP7 PASS |
| 真实发布状态 | 未执行真实发布；CP8 approve 不等于 RELEASED |

## 用户可见变化

- 新增 `docs/research/LIFECYCLE.md`：定义策略研究生命周期和 `delivery_candidate` 边界。
- 新增 `docs/research/STRATEGY-TAXONOMY.md`：定义首版 8 类策略族和后续扩展规则。
- 新增 `docs/research/ARCHIVE-GOVERNANCE.md` 与 `RESEARCH-ARCHIVE-MANIFEST-SPEC.md`：定义 Git、research archive、market data lake、broker archive 和冷热分层。
- 新增 `docs/research/HOST-WORKFLOW.md`：定义研究主机、NAS 和交易主机职责。
- 新增 `docs/research/RESEARCH-REGISTRY-SPEC.md`：定义 RunManifest、ValidationEvidence、ProjectIdentity、MigrationInventory 和 ArchivePointer。
- 新增 `docs/research/PROJECT-IDENTITY-MIGRATION.md`：确认 `quant-lab` canonical name，保留 `local_backtest` legacy alias。

## 明确非范围

- 不重命名当前目录或远端仓库。
- 不执行 NAS 操作或 archive migration。
- 不执行 provider fetch、lake write、catalog publish。
- 不连接或运行 QMT / MiniQMT。
- 不读取凭据、账户、token、`.env`。
- 不 submit、cancel、simulation 或 live trading。

## 后续路线

CR052..CR056 作为候选路线保留，必须在 CR051 CP8 关闭后按独立 CR 启动；本发布不自动启动后续 CR。

