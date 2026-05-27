---
handoff_id: "META-DEV-BUGFIX-W0-STORY-003-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-003"
story_slug: "parquet-quality-report"
bug_id: "BUG-STORY-003-001"
severity: "BLOCKING"
status: "dispatched"
created_at: "2026-05-15"
source_report: "process/VERIFICATION-REPORT.md"
---

# Handoff: meta-dev 修复 STORY-003 BLOCKING 缺陷

## 1. 路由结论

meta-qa 已完成 STORY-003 正式验证，结论为 `FAIL`，不是环境 `BLOCKED`。meta-po 判定 `BUG-STORY-003-001` 为 STORY-003 实现缺陷，严重级别 `BLOCKING`，不升级为 CR，不交人工接管，路由给 `meta-dev` 做限定范围 bugfix。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、bugfix 门控和禁止范围 |
| Story 状态 | `process/STORY-STATUS.md` | 确认 STORY-003 已退回 `in-development`，BUG 为 BLOCKING |
| Story 卡片 | `process/stories/STORY-003-parquet-quality-report.md` | 获取 Story 目标、验收标准、缺陷状态和禁止范围 |
| 已确认 LLD | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 作为修复设计边界，重点读取第 6、7、10、13 节 |
| 验证报告 | `process/VERIFICATION-REPORT.md` | 读取 STORY-003 报告中 `BUG-STORY-003-001`、失败证据与回归要求 |
| 测试策略 | `process/TEST-STRATEGY.md` | 确认 STORY-003 回归验证矩阵 |
| 目标实现 | `engine/quality.py` | 修复必需字段缺失路径 |
| 相关上下文 | `engine/contracts.py`, `engine/normalizer.py` | 只读或最小必要调整，保持 STORY-003 边界 |

不得加载无关 Story 的 LLD、历史草稿或 STORY-004+ 设计作为实现依据。

## 3. 缺陷定义

| 字段 | 内容 |
|---|---|
| Bug ID | `BUG-STORY-003-001` |
| 严重级别 | `BLOCKING` |
| 当前状态 | `OPEN` |
| 失败表现 | `prices.parquet` 缺少必需字段 `close` 时，`engine/quality.py` 抛出裸 `KeyError: 'close'` |
| 证据位置 | `process/VERIFICATION-REPORT.md` STORY-003 报告；定位到 `engine/quality.py` 第 446 行、第 466 行直接访问 `prices["close"]` / `in_range[..., "close"]` |
| 违反契约 | Story / LLD 要求必需字段缺失时输出 `missing_required_fields`，并使 `quality_status=fail` |

## 4. 整改目标

meta-dev 必须修复 `engine/quality.py` 中必需字段缺失路径：

- 缺少任一 prices 必需字段时，不得抛裸 `KeyError`。
- `calculate_quality` / `_price_metrics` 必须在读取指标前尊重 schema 检查结果。
- 缺失字段必须进入结构化输出 `missing_required_fields`，字段命名至少覆盖 `prices.close`、`prices.symbol`、`prices.trade_date`。
- 返回的质量记录必须包含 `quality_status=fail`。
- 报告渲染仍需输出 CSV/Markdown 固定字段，不得因缺字段中断。

## 5. 允许修改范围

| 路径 | 允许动作 |
|---|---|
| `engine/quality.py` | 修复必需字段缺失路径、补充结构化质量记录和必要的内部测试辅助逻辑 |
| `engine/contracts.py` | 仅当现有常量缺少必要字段命名时做最小常量补充；必须保持纯常量模块 |
| `engine/normalizer.py` | 默认不改；仅当修复需要对齐 STORY-003 已确认 LLD 的结构化 schema 错误时做最小调整 |
| `process/stories/STORY-003-parquet-quality-report.md` | 修复完成后回写 Story 状态为 `ready-for-verification`，并标记 `BUG-STORY-003-001` 已提交复验 |
| `process/STORY-STATUS.md` | 修复完成后回写 STORY-003 状态与 W0 计数 |
| `process/STATE.md` | 修复完成后回写 `last_action`、`next_action`、history，下一步交 meta-po 复核并分派 meta-qa 回归 |

## 6. 严格禁止范围

- 不得修改需求、HLD、ADR、已确认 LLD 或 Story 计划。
- 不得实现、创建或验证 `STORY-004+` 范围。
- 不得创建或修改 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 不得修改 `engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py` 的 STORY-002 已验证行为。
- 不得真实调用 AKShare、聚宽或其他远程数据源。
- 不得写真实 `data/*.parquet`、真实 `data/raw/**`、真实 `data/manifests/**`、真实 `reports/data_quality_report.*`。
- 不得写 `delivery/**`、安装脚本、README 或 USER-MANUAL。
- 不得创建 `scripts/check_delivery_guardrails.py`；该缺口是观察项，不属于本 bugfix。

## 7. 回归验证要求

meta-dev 修复后至少自检以下场景，并在交回时列出命令和结果：

| 回归项 | 期望 |
|---|---|
| 缺 `prices.close` | 不抛 `KeyError`；`missing_required_fields` 含 `prices.close`；`quality_status=fail` |
| 缺 `prices.symbol` | 不抛 `KeyError`；`missing_required_fields` 含 `prices.symbol`；`quality_status=fail` |
| 缺 `prices.trade_date` | 不抛 `KeyError`；`missing_required_fields` 含 `prices.trade_date`；`quality_status=fail` |
| 完整数据 pass | 既有 `T-QUALITY-PASS-01` 仍为 `quality_status=pass` |
| 少量缺失 warn | 既有 `T-QUALITY-WARN-01` 仍为 `quality_status=warn` |
| 缺失率 `>5%` / 覆盖缺口 / 重复键 / `close<=0` | 既有 fail 路径仍返回 `quality_status=fail` |
| 边界复核 | 不写真实 data/report，不写 `delivery/**`，不推进 STORY-004+ |

修复完成后不得直接标记 `verified`。meta-dev 只能提交到 `ready-for-verification`，由 meta-po 复核后重新分派 `meta-qa` 针对 `BUG-STORY-003-001` 和 STORY-003 关键路径做回归验证。
