---
handoff_id: "META-QA-REGRESSION-W0-STORY-003-BUG-STORY-003-001-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-qa"
phase: "story-execution"
wave: "W0"
story_id: "STORY-003"
story_slug: "parquet-quality-report"
bug_id: "BUG-STORY-003-001"
severity: "BLOCKING"
status: "dispatched"
created_at: "2026-05-15"
source_bugfix_handoff: "process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md"
source_verification_report: "process/VERIFICATION-REPORT.md"
---

# Handoff: meta-qa 回归验证 STORY-003 bugfix

## 1. 分派结论

meta-dev 已完成 `BUG-STORY-003-001` 限定范围 bugfix，并将 `STORY-003` 重新提交到 `ready-for-verification`。meta-po 已读取并复核 `process/STATE.md`、`process/STORY-STATUS.md`、`process/stories/STORY-003-parquet-quality-report.md`、`DEV-LOG.md`、上一轮 `process/VERIFICATION-REPORT.md` 与 bugfix handoff。

本轮 bugfix 范围复核通过，可分派 `meta-qa` 执行 STORY-003 bugfix regression。验证重点是关闭 `BUG-STORY-003-001`，并复验原 STORY-003 关键验收路径未回归。meta-qa 不得推进 `STORY-004+`。

## 2. meta-po 范围复核事实

| 复核项 | 结论 | 证据 |
|---|---|---|
| 当前阶段 | 通过 | `process/STATE.md` 为 `story-execution`，`active_story=STORY-003`，`blocked=false` |
| Story 状态 | 通过 | `process/STORY-STATUS.md` 与 Story 卡均为 `STORY-003=ready-for-verification` |
| bugfix handoff 范围 | 通过 | `process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md` 要求优先修复 `engine/quality.py`，仅必要时最小触达 `engine/contracts.py` / `engine/normalizer.py` |
| meta-dev 声明的实现范围 | 通过 | `DEV-LOG.md` 记录本次 bugfix 实现文件清单仅为 `engine/quality.py` |
| 目标实现只读复核 | 通过 | `_price_metrics(...)` 已在 `prices.empty or schema_errors` 分支早返回，避免 schema 缺失路径继续访问 `prices["close"]` / `in_range[...]` |
| 真实 data 写入 | 通过 | `data/` 下仅有 `data/.gitkeep`；未发现真实 `data/*.parquet`、`data/raw/**` 或 `data/manifests/**` 文件 |
| 真实 report 写入 | 通过 | `reports/` 下仅有 `reports/.gitkeep`；未发现真实 `reports/data_quality_report.*` |
| delivery 边界 | 通过 | `delivery/` 下未发现文件；未生成安装脚本 |
| STORY-004+ 越界 | 通过 | 未发现 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py` 或 `strategies/**` 的 STORY-004+ 新实现 |
| Git diff 限制 | 已状态化 | 当前工作区不是 Git 仓库，无法用 `git diff` 输出变更统计；本轮以过程文件、目标文件只读复核和文件系统边界扫描交叉确认 |

## 3. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、bugfix regression 门控和禁止范围 |
| Story 状态汇总 | `process/STORY-STATUS.md` | 确认 `STORY-003=ready-for-verification`，W0 仍未完成 |
| Story 卡片 | `process/stories/STORY-003-parquet-quality-report.md` | 获取目标、验收标准、缺陷状态和禁止范围 |
| 已确认 LLD | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 复验接口设计、核心流程、异常路径、测试设计和回滚策略 |
| LLD 检查点 | `checkpoints/STORY-003-LLD-CHECKPOINT.md` | 确认 LLD 人工门控已通过 |
| 原验证 handoff | `process/handoffs/META-QA-VERIFY-W0-STORY-003-2026-05-15.md` | 复用原 STORY-003 验证范围和禁止范围 |
| bugfix handoff | `process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md` | 确认 `BUG-STORY-003-001` 整改目标和回归要求 |
| 上一轮验证报告 | `process/VERIFICATION-REPORT.md` | 读取上一轮 FAIL 证据、BLOCKING finding 与观察项 |
| 开发日志 | `DEV-LOG.md` | 获取 meta-dev 声明的 bugfix 文件、命令、临时目录回归和边界自检 |
| 实现文件 | `engine/quality.py` | 本次 bugfix regression 的主验证对象 |
| 原 STORY-003 实现上下文 | `engine/normalizer.py`、`engine/contracts.py` | 复验原关键验收路径，确认无回归 |
| 验证环境 | `process/VALIDATION-ENV.yaml` | 确认正式验收环境仍为 `approval.confirmed=true` |
| 测试策略 | `process/TEST-STRATEGY.md` | 刷新或追加 STORY-003 bugfix regression 口径 |

可按需读取 `pyproject.toml`、`uv.lock`、`engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py` 和 `config/data_prep.yaml` 作为只读上游语义。不得加载无关 Story 的 LLD、历史草稿或 STORY-004+ 设计作为本轮依据。

## 4. 必须回归的缺陷

| 回归项 | 期望 |
|---|---|
| 缺 `prices.close` | `calculate_quality(...)` 不抛裸 `KeyError`；`missing_required_fields` 含 `prices.close`；`quality_status=fail` |
| 缺 `prices.symbol` | 不抛裸 `KeyError`；`missing_required_fields` 含 `prices.symbol`；`quality_status=fail` |
| 缺 `prices.trade_date` | 不抛裸 `KeyError`；`missing_required_fields` 含 `prices.trade_date`；`quality_status=fail` |
| 报告渲染 | schema 缺失路径仍能渲染 CSV/Markdown 固定字段，不因缺字段中断 |
| finding 关闭判定 | 若以上均通过，将 `BUG-STORY-003-001` 标记为 CLOSED / PASS；否则继续保持 BLOCKING |

## 5. 原 STORY-003 关键验收路径复验

meta-qa 至少复验以下路径，确认 bugfix 未破坏原 STORY-003 能力：

| 路径 | 期望 |
|---|---|
| `T-QUALITY-PASS-01` 完整数据 | `quality_status=pass` |
| `T-QUALITY-WARN-01` 少量缺失 | `0 < missing_rate <= 5%` 时 `quality_status=warn` |
| `T-QUALITY-FAIL-01` 缺失率 | `missing_rate > 5%` 时 `quality_status=fail` |
| 覆盖缺口 | 请求区间未覆盖时 `quality_status=fail` |
| 重复键 | 未解决重复键计入 `duplicate_record_count`，并导致 `quality_status=fail` |
| `close <= 0` | 异常非缺失价格计入 `abnormal_price_count`，并导致 `quality_status=fail` |
| 数据源失败但本地 parquet 合规 | 披露 failed batch；按 LLD 允许路径输出 `warn/pass` |
| CSV / Markdown 报告字段 | 覆盖 Story 验收标准中至少 14 类字段，并包含 `manifest_run_id`、`available_at_rule`、`adjustment_policy`、`is_pit_universe`、`survivorship_bias_note` |
| 静态边界 | `engine/normalizer.py`、`engine/quality.py` 不导入 AKShare，不调用 `run_data_prep` / `AkshareAdapter`，无危险 shell / 网络调用 |

## 6. 禁止范围

- 禁止修改实现代码；meta-qa 只验证，不修复。
- 禁止推进 `STORY-004+`，禁止起草其 LLD、实现其代码或生成其验证报告。
- 禁止创建或修改 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 禁止修改 `engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py` 的 STORY-002 已验证行为。
- 禁止真实调用 AKShare、聚宽或其他远程数据源。
- 禁止向真实 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet` 写入验证样例。
- 禁止向真实 `reports/data_quality_report.csv` 或 `reports/data_quality_report.md` 写入验证样例。
- 禁止写入 `delivery/**`、安装脚本、README 或 USER-MANUAL。
- 禁止创建缺失的 `scripts/check_delivery_guardrails.py`；该缺口只允许在验证报告中状态化。

## 7. 期望回写

meta-qa 可回写：

- `process/TEST-STRATEGY.md`
- `process/VERIFICATION-REPORT.md`

验证报告必须明确列出：

- `BUG-STORY-003-001` 的 PASS / FAIL 结论；
- 原 STORY-003 关键验收路径是否 PASS；
- BLOCKING / REQUIRED / OBSERVATION findings；
- `scripts/check_delivery_guardrails.py` 缺失是否阻断 STORY-003；
- 是否发现真实 data/report、`delivery/**`、安装脚本或 STORY-004+ 越界。

meta-qa 不直接将 Story 推进为 `verified`。若回归 PASS 且无 BLOCKING/REQUIRED 失败项，由 meta-po 回收报告后判断 `STORY-003` 和 W0 是否可收敛。
