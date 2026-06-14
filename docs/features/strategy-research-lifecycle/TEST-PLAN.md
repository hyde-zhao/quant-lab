---
status: "draft-cp4"
version: "1.0"
feature_id: "FEAT-10"
feature_name: "Strategy Research Lifecycle and Project Migration Governance"
source_design: "docs/features/strategy-research-lifecycle/DESIGN.md"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX.md"
---

# Test Plan: Strategy Research Lifecycle and Project Migration Governance

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初始 FEAT-10 测试计划，覆盖生命周期、archive、迁移、alias、no-real-operation 和 Story 完整性 |

## 测试策略

| 维度 | 策略 | 证据 |
|---|---|---|
| 静态文档一致性 | 校验 FEAT-10 在蓝图、领域图、依赖图、Feature Matrix、Story 卡片中一致 | CP4 / CP5 检查 |
| 结构化解析 | YAML frontmatter、Development Plan、CR index 和 context capsule 必须可解析 | `uv run --python 3.11 python ...` |
| DAG / 并行安全 | CR051-S01..S06 依赖无环，跨 Wave 文件所有权无冲突 | CP4 自动预检 |
| 安全边界 | 不授权 provider/lake/publish、QMT/MiniQMT、NAS 操作、目录重命名、git push、凭据读取 | no-real-operation checklist |
| 迁移可回滚性 | migration inventory 必须有 Git 归档点、验证规则和回滚引用 | CP5 LLD review |

## 用例矩阵

| Test ID | 目标 | 输入 | 预期结果 | 覆盖 Story |
|---|---|---|---|---|
| TC-CR051-01 | 生命周期状态机完整 | StrategyIdea -> ResearchProject -> ValidationEvidence | 状态只允许按 SM-13 递进，delivery_candidate 不等于 runtime_candidate | S01 |
| TC-CR051-02 | archive / lake / broker facts 隔离 | ArchiveManifest、data release ref、broker facts ref | Git / research archive / market data lake / broker lake 边界清晰，禁止交叉写入 | S02 / S04 |
| TC-CR051-03 | 硬件冷热分层 | NAS 512G SSD、4T RAID、14T HDD、研究主机 2T SSD、交易主机 512G SSD | 每类设备职责唯一，交易主机只消费 package | S02 / S03 |
| TC-CR051-04 | 项目身份兼容 | canonical `quant-lab`、legacy alias `local_backtest` | 新文档使用 canonical，历史审计名保留，不批量重写 | S06 |
| TC-CR051-05 | 后续 CR gate | CR052..CR056 candidate | 每个后续 CR 有进入条件、消费对象、不授权项和解除条件 | S05 |
| TC-CR051-06 | Story 完整性 | Story cards / Feature Matrix / Development Plan | 6 个 Story 均有 lld_policy、feature_design_refs、cp5_batch、file ownership | S01..S06 |

## 安全测试

| Security TC | 禁止项 | 检查方法 | 失败处理 |
|---|---|---|---|
| SEC-TC-01 | Git 存 raw data / large artifact / credentials / broker facts | 静态扫描和人工 review | CP7 / CP8 blocked |
| SEC-TC-02 | CP4 / CP5 执行 NAS 扫描、挂载、搬迁、删除或目录重命名 | 命令记录和 no-real-operation counter review | fail closed |
| SEC-TC-03 | delivery_candidate 声称 runtime verified / trade-ready | 文档 guardrail | 修正文档并重跑 review |
| SEC-TC-04 | 批量重写历史 `local_backtest` 审计证据 | diff review | blocked，改为 alias policy |
| SEC-TC-05 | 交易主机挂载 full research archive 或承担研究开发 | migration plan review | blocked，保留 package consumer |

## 验证命令候选

| 阶段 | 命令 / 检查 | 说明 |
|---|---|---|
| CP4 | `uv run --python 3.11 python scripts/check_cr_tracking_consistency.py --project-root .` | CR tracking 一致性 |
| CP4 | YAML/frontmatter parse | `process/STATE.md`、`process/changes/CR-INDEX.yaml`、`process/DEVELOPMENT-PLAN.yaml` |
| CP4 | `git diff --check` | Markdown / YAML 空白检查 |
| CP5 | Story LLD implementability review | 校验 S01..S04 full-lld 和 S05..S06 technical-note |
| CP7 | static docs / guardrail review | 校验 no-real-operation 和 alias / migration 声明 |

## 出口准则

- CP4 自动预检 PASS，阻断项为 0。
- CP5 前不得实现、迁移、重命名、NAS 操作或 runtime。
- CP5 批次必须覆盖 S01..S06 全部设计证据。
