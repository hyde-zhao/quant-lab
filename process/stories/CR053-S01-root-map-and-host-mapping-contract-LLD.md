---
story_id: "CR053-S01-root-map-and-host-mapping-contract"
title: "迁移 root map 与主机映射合同"
story_slug: "root-map-and-host-mapping-contract"
lld_version: "1.0"
tier: "M"
status: "confirmed"
confirmed: true
created_by: "meta-dev"
created_at: "2026-06-14T11:16:58+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-14T11:52:15+08:00"
shared_fragments:
  - "docs/design/HLD-CR053-QUANT-LAB-MIGRATION-INVENTORY-AND-DRY-RUN.md#5-nas-逻辑目录映射"
  - "docs/design/ARCHITECTURE-DECISION-CR053.md#adr-cr053-001nas-目录映射使用逻辑-root"
feature_design_refs:
  - "docs/features/quant-lab-migration-dry-run/DESIGN.md"
  - "docs/features/quant-lab-migration-dry-run/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "nas-root-map"
    - "linux-host-mapping"
    - "windows-package-exchange"
    - "lake-alias-boundary"
  rationale: "root map 会影响后续 inventory、backup plan 和 CR058 输入，必须 full-lld 冻结字段、host role 和不授权边界。"
open_items: 0
---

# LLD: CR053-S01 — 迁移 root map 与主机映射合同

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| CP5 Context | `process/context/CP5-CR053-LLD-CONTEXT.yaml` | CP5 批次、S01 evidence_path、不授权清单 |
| HLD | `docs/design/HLD-CR053-QUANT-LAB-MIGRATION-INVENTORY-AND-DRY-RUN.md` | NAS 三分区逻辑视图、Linux / Windows 主机映射、数据湖 alias 边界 |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR053.md` | ADR-CR053-001、006、007 |
| Feature Matrix | `docs/design/FEATURE-DESIGN-MATRIX.md` | FEAT-10-CR053；S01 full-lld 判定 |
| Feature DESIGN | `docs/features/quant-lab-migration-dry-run/DESIGN.md` | IF-CR053-03 NAS map、SEC-CR053-01..05 |
| TEST-PLAN | `docs/features/quant-lab-migration-dry-run/TEST-PLAN.md` | TC-CR053-01、TC-CR053-02、SEC-CR053-01 |
| TASKS | `docs/features/quant-lab-migration-dry-run/TASKS.md` | CR053-T01、CR053-R03 |

## 1. Goal

定义 `quant-lab` migration dry-run 的逻辑 root map、主机角色映射和不授权边界，为后续 `docs/release/NAS-MAPPING-CR053.md` 静态报告提供可实现合同；本 Story 不验证真实路径、不挂载、不扫描、不创建目录。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- root map 必须覆盖 Repo workspace、Hot cache、Package exchange、Research archive、Market data lake alias、Cold backup、Trading evidence 7 类 root。
- Linux 研究机逻辑视图只允许表达 `/mnt/quant-lab/hot`、`/mnt/quant-lab/archive`、`/mnt/quant-lab/cold-backup`；三分区物理层不得混并。
- Windows 交易机只允许映射 package exchange，默认只读；不得映射完整 archive、cold backup、full lake 或完整研究 workspace。
- 现有 `MARKET_DATA_LAKE_ROOT` / `--lake-root` 保持当前数据湖合同；`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作为文档 alias / pointer。
- 输出必须能被 S02 inventory、S04 backup plan 和 S05 CR058 input 消费。

### 2.2 Non-Functional

- 安全：禁止 NAS mount / scan / mkdir / copy / delete、`.env` 读取、数据湖路径替换和 Windows full archive 暴露。
- 可审计：每个 root 必须声明主设备 / 层、允许内容、禁止内容、备份等级和验证状态。
- 可迁移：真实路径绑定只能作为后续 CR058 / CR060 的输入占位，不在 CR053 执行。
- 兼容：不得破坏 legacy `local_backtest` 路径、现有数据湖 CLI 或已验证 backup / restore / publish gate。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| RootMapContract | 定义 root_id、env_var、logical_path、device_tier、allowed_content、forbidden_content、backup_class、verification_status | 用于 `NAS-MAPPING-CR053.md` 的主表 |
| HostMappingContract | 定义 host_role、os_family、allowed_roots、forbidden_roots、access_mode、notes | 区分 Linux 研究机、Windows 交易机和外置数据湖 |
| LakeAliasBoundary | 明确 `MARKET_DATA_LAKE_ROOT` 不调整，`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅 pointer | 防止 S01 被误实现成 `.env` 或 CLI 变更 |
| NoOperationGuardrail | 记录 not-authorized 操作和失败行为 | 供 CP5 / CP6 / CP7 静态验证消费 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md` | 本 full-lld 设计证据 |
| 修改 | `process/stories/CR053-S01-root-map-and-host-mapping-contract.md` | 状态推进到 `lld-ready-for-review`，写入 lld_gate / dev_gate |
| 创建 | `process/checks/CP5-CR053-S01-root-map-and-host-mapping-contract-LLD-IMPLEMENTABILITY.md` | CP5 自动预检 |
| 未来创建 | `docs/release/NAS-MAPPING-CR053.md` | CP5 批准后的静态 root map 报告；当前不生成真实映射证据 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `RootMap.root_id` | enum | `repo_workspace` / `hot_cache` / `package_exchange` / `research_archive` / `market_data_lake_alias` / `cold_backup` / `trading_evidence` | 7 类 root 必须 100% 覆盖 |
| `RootMap.env_var` | string | 可为空；数据湖必须保留 `MARKET_DATA_LAKE_ROOT` 为现有入口 | `QUANT_LAB_*` 仅用于迁移文档合同 |
| `RootMap.logical_path` | string | 逻辑路径，不代表真实存在 | Linux 可写 `/mnt/quant-lab/*` 逻辑视图 |
| `RootMap.device_tier` | enum | `research_pc_ssd` / `nas_hot_ssd` / `nas_warm_raid` / `external_lake` / `nas_cold_hdd` / `trading_pc_ssd` | 三分区职责不可混合 |
| `RootMap.access_mode` | enum | `read-write-planned` / `read-only-planned` / `pointer-only` / `not-authorized` | Windows package exchange 默认为 read-only |
| `RootMap.verification_status` | enum | `logical-only` / `requires-runtime-authorization` | CR053 只能使用 `logical-only` 或 `requires-runtime-authorization` |
| `HostMap.host_role` | enum | `linux_research_pc` / `windows_trading_pc` / `external_lake_mount` | 定义主机职责 |
| `HostMap.forbidden_roots` | list[string] | 必填 | Windows 必须禁止 archive / cold / full lake |

无新增数据库或持久化存储；未来报告为 Markdown 静态文档。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| IF-CR053-S01-root-map-contract | HLD logical roots、ADR-CR053-001/006/007、Feature DESIGN IF-CR053-03 | RootMap 表、HostMap 表、NoOperationGuardrail 表 | S02 / S04 / S05 / CP6 静态报告生成 | 测试入口 TC-CR053-01 / 02 |
| IF-CR053-S01-lake-alias-boundary | 现有 `MARKET_DATA_LAKE_ROOT` 合同、HLD 数据湖兼容性 | alias 声明和禁止替换规则 | S04 backup plan、S05 CR058 gate | 测试入口 TC-CR053-02 |
| IF-CR053-S01-safety-boundary | CP5 Context not_authorized 清单 | 禁止操作表和 fail-closed 行为 | CP5 / CP6 / CP7 | 测试入口 SEC-CR053-01 |

## 7. 核心处理流程

1. 读取 HLD / ADR / Feature DESIGN 中已确认的 logical root、host role 和不授权边界。
2. 将 root 拆成 7 个 `RootMap` 条目，逐项写入允许内容、禁止内容、备份等级和验证状态。
3. 将主机拆成 Linux 研究机、Windows 交易机、外置数据湖三类 `HostMap` 条目。
4. 写明 Linux 研究机统一视图只是命名空间，底层 hot / archive / cold-backup 仍是物理分层。
5. 写明 Windows 交易机只读 package exchange，full archive / cold / full lake 均 blocked。
6. 写明 `MARKET_DATA_LAKE_ROOT` 不调整，`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅作为 alias / pointer。
7. 将禁止操作和未验证真实路径写入报告字段，供 S02 / S04 / S05 下游消费。

```mermaid
flowchart TD
  HLD[HLD / ADR confirmed logical roots] --> RootMap[RootMapContract]
  HLD --> HostMap[HostMappingContract]
  RootMap --> Linux[/mnt/quant-lab logical view]
  RootMap --> Lake[MARKET_DATA_LAKE_ROOT unchanged]
  HostMap --> Win[Windows package exchange read-only]
  Linux --> Guard[No real mount / scan / mkdir]
  Win --> Guard
  Lake --> Guard
  Guard --> Report[NAS-MAPPING-CR053.md static report]
```

## 8. 技术设计细节

- 关键规则：root map 是逻辑合同，不是当前机器或 NAS 的事实声明；所有真实路径字段必须带 `verification_status=requires-runtime-authorization` 或 `logical-only`。
- 依赖选择与复用点：复用 HLD §5 root 表和 ADR-CR053-001/006/007；不新增 Python schema 或运行时解析器。
- 兼容性处理：保留现有 `MARKET_DATA_LAKE_ROOT`，不要求用户替换 `.env`、CLI 参数或运行脚本。
- 图示类型选择：使用流程图，因为涉及 HLD / root map / host map / guardrail / report 五个节点。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 将 NAS mount / scan / mkdir / copy / delete、数据湖替换、Windows full archive mount 写为 forbidden；`.env` 和凭据不进入输入 | SEC-CR053-01；CP5 文件审查 |
| 性能 | 当前只生成静态文档设计，不做真实路径遍历或容量扫描 | 检查无 NAS scan / untracked bulk scan 入口 |
| 隐私 | 不记录真实私有路径、账号或凭据；真实路径只允许后续授权时作为占位输入 | 报告字段审查 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TC-CR053-01 root map schema 覆盖 | CP5 approved 后生成静态报告 | 审查 `NAS-MAPPING-CR053.md` root 表 | 7 类 root 100% 出现，且字段完整 | 静态报告审查 |
| TC-CR053-02 数据湖 alias 不替换 | 静态报告存在 | 搜索报告中的数据湖变量声明 | `MARKET_DATA_LAKE_ROOT` 保持现状，`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作 alias / pointer | 文本审查 |
| SEC-CR053-01 禁止操作计数 | 本 Story 设计证据与 CP6 输出 | 检查 not-authorized 表 | NAS / lake / credential / git push / runtime 操作计数为 0 | CP5 / CP7 静态审查 |
| S01-NEG-Windows-full-archive | Windows host map 存在 | 检查 Windows allowed / forbidden roots | allowed 仅 package exchange，archive / cold / full lake 均 forbidden | 静态报告审查 |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR053-T01-01 | 创建 | `process/stories/CR053-S01-root-map-and-host-mapping-contract-LLD.md` | 写入 0-14 节 full-lld，冻结 RootMap / HostMap / Guardrail 合同 | CP5 自动预检 |
| CR053-T01-02 | 修改 | `process/stories/CR053-S01-root-map-and-host-mapping-contract.md` | 状态改为 `lld-ready-for-review`，写入 lld_gate / dev_gate，保持 implementation_allowed=false | CP5 自动预检 |
| CR053-T01-03 | 创建 | `process/checks/CP5-CR053-S01-root-map-and-host-mapping-contract-LLD-IMPLEMENTABILITY.md` | 记录 Entry / Checklist / Exit / Deliverables 和 PASS 结论 | CP5 自动预检 |
| CR053-R03-01 | 未来创建 | `docs/release/NAS-MAPPING-CR053.md` | CP5 approved 后生成静态 logical map 报告，不执行真实 NAS 操作 | TC-CR053-01 / 02 / SEC-CR053-01 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无阻断 clarification | 沿用 CP3 已确认方案：Linux 研究机三分区统一逻辑视图、Windows 只读 package exchange、数据湖变量不替换 | 已由 CP3 approve 接受 | 接口 / 安全 / 文档 / 跨 Story 契约 | HLD v0.2、ADR-CR053-001/006/007 | 真实 NAS path binding、数据湖迁移或 Windows import 方式变化 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 逻辑路径被误读为已挂载真实路径 | 误触发 mount / mkdir / copy | 每个路径带 `logical-only`；CP6/CP7 检查 forbidden counter |
| Windows 交易机暴露 full archive | 扩大敏感面 | HostMap 中将 full archive / cold / full lake 标为 forbidden |
| 数据湖 alias 被误实现为变量替换 | 破坏现有 CLI / backup / restore | 明确 `QUANT_LAB_MARKET_DATA_LAKE_ROOT` 仅文档 pointer |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| N/A | N/A | 无 OPEN / Spike | N/A | N/A |

## 13. 回滚与发布策略

- 发布方式：CP5 仅发布设计证据到 Story LLD 和 CP5 自动预检；CP5 人工确认前不进入 CP6 实现。
- 回滚触发条件：CP5 人工审查要求修改 root map、host mapping 或 lake alias；或发现与 HLD / ADR 冲突。
- 回滚动作：修改本 LLD 与 Story lld_gate；不回滚真实文件系统，因为本 Story 不执行真实文件系统操作。

## 14. Definition of Done

- [x] 14 个章节全部填写完成
- [x] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [x] 实现灰区与取舍记录已显式写“无阻断 clarification”
- [x] `confirmed=false` 时不进入实现
- [x] frontmatter 已填写 `tier`
- [x] OPEN / Spike 已清点为 0
- [x] 明确 NAS 三分区逻辑映射、现有 `MARKET_DATA_LAKE_ROOT` 不调整、Windows 只读 package exchange

## 人工确认区

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | 第 2 / 10 / 14 节 |
| 2 | 与 HLD / ADR 一致 | 待检查 | 第 0 / 8 / 12 节 |
| 3 | 文件影响范围明确 | 待检查 | 第 4 / 11 节 |
| 4 | 接口契约完整 | 待检查 | 第 6 节 |
| 5 | 测试与 dev_gate 可计算 | 待检查 | 第 10 / 14 节 |
| 6 | clarification queue 已收敛 | 待检查 | 第 12.1 节 |

人工确认由 host-orchestrator 在 CP5 批次审查稿中统一发起；本文件不单独请求用户确认。
