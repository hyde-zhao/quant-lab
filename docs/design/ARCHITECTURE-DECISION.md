---
status: "current-index"
version: "1.1"
change: "CR-046"
legacy_source: "process/ARCHITECTURE-DECISION.md"
current_change_sources:
  - "docs/design/ARCHITECTURE-DECISION-CR046.md"
  - "docs/design/ARCHITECTURE-DECISION-CR053.md"
---

# Architecture Decision Current Index

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-07 | meta-po | 新增 ADR 长期索引，按 Feature / Epic 聚合 legacy ADR 范围 |
| 1.1 | 2026-06-13 | meta-po | 按 CR-046 增补双目标策略交付框架 ADR 入口 |
| 1.2 | 2026-06-14 | host-orchestrator | 按 CR-053 增补 quant-lab migration inventory / dry-run ADR 入口 |

## 定位

正式 ADR 正文仍在 `process/ARCHITECTURE-DECISION.md`。本文只提供按能力域聚合的 current index，帮助后续 CR 快速定位决策簇。

## ADR 聚合索引

| Feature | ADR 范围 | 主题 |
|---|---|---|
| FEAT-01 本地研究与轻量回测核心 | ADR-001..012、ADR-023..029 | 数据准备与回测隔离、轻量主路径、复权口径、T+1 成交、manifest、quality、research input、benchmark 字段隔离 |
| FEAT-02 生产级市场数据湖 | ADR-013..022、ADR-030..035、ADR-048..054、ADR-062..066 | Tushare 写湖、dataset readiness、生产数据湖、publish gate、全 A current truth、DuckDB readonly、复权双视图、rollback |
| FEAT-03 多因子研究闭环 | ADR-036..043、ADR-079..086 | benchmark/PIT/tradability/execution/adjustment/exposure/capacity/factor audit、FactorSpec、FactorRunSpec、LabelWindow、StrategyAdmissionPackage |
| FEAT-04 执行语义与可选后端 | ADR-074..078 | Backtrader optional semantic reference、module reference/no-copy、order intent draft、依赖隔离 |
| FEAT-05 QMT C/S Gateway 与只读准入 | ADR-067..073、ADR-087..093 | Stage6 admission、QMT C/S bridge、HMAC pairing、endpoint matrix、gateway runtime、login/session ready、query_positions readonly |
| FEAT-06 OMS / 风控 / Broker Lake / 阶段激活 | ADR-055..061 | QMT adapter、broker lake、OMS、pre-trade risk、stage gate、reconciliation、kill switch、cross-node deployment |
| FEAT-07 安全授权治理 | ADR-051、ADR-061、ADR-071..073、ADR-086、ADR-090..093 | 真实操作授权、redaction、HMAC / scope、fallback、no-real-operation、安全边界 |
| FEAT-08 文档 / Runbook | ADR 派生，不单独编号 | README、USER-MANUAL、QMT runbook 和 CP8 只作为用户操作与审计入口，不提供 runtime authorization |
| FEAT-09 QMT / MiniQMT 双目标策略交付框架 | ADR-CR046-001..006 | 独立 FEAT-09、平台无关策略核心、MiniQMT runner 安装设计、验证证据分级、CR047/CR051 后置 |
| FEAT-10 Strategy Research Lifecycle / quant-lab Migration Governance | ADR-CR053-001..005 | NAS 逻辑目录映射、manifest-first 数据传输、warm/cold 备份、真实迁移 CR058 后置、交易主机只读 package exchange |

## 使用规则

| 判断问题 | 读取方式 |
|---|---|
| 是否已有架构决策 | 先查上表，再读 `process/ARCHITECTURE-DECISION.md` 对应 ADR |
| 是否允许新增依赖 | 查对应 ADR 和 `docs/design/DEPENDENCY-MAP.md`；默认不允许外部框架 / QMT / DuckDB 依赖变更 |
| 是否允许真实操作 | ADR 只能给出设计边界；真实操作必须另有 CP / per-run authorization |
| 审查 CR046 ADR | 读取 `docs/design/ARCHITECTURE-DECISION-CR046.md` |
| 审查 CR053 ADR | 读取 `docs/design/ARCHITECTURE-DECISION-CR053.md` |
| ADR 与蓝图冲突 | 以 legacy ADR 正文和 HLD 事实为准，修订蓝图索引 |
