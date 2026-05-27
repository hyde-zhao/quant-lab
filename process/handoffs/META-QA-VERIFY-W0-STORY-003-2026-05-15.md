---
handoff_id: "META-QA-VERIFY-W0-STORY-003-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-qa"
phase: "story-execution"
wave: "W0"
story_id: "STORY-003"
story_slug: "parquet-quality-report"
status: "dispatched"
created_at: "2026-05-15"
---

# Handoff: meta-qa 验证 STORY-003

## 1. 分派结论

meta-dev 已报告 `STORY-003` 实现完成，并将 Story 推进到 `ready-for-verification`。meta-po 已读取并复核 `process/STATE.md`、`process/STORY-STATUS.md`、STORY-003 Story 卡、STORY-003 LLD、implementation handoff 与 `DEV-LOG.md`。

本轮实现范围静态复核通过，可分派 `meta-qa` 执行 STORY-003 正式验证。验证只覆盖 `STORY-003`，不得推进或验证 `STORY-004+`。

## 2. meta-po 复核事实

| 复核项 | 结论 | 证据 |
|---|---|---|
| Story / LLD 允许实现文件 | 通过 | `STORY-003` Story、LLD 与实现 handoff 允许创建/修改 `engine/normalizer.py`、`engine/quality.py`，并在 `engine/contracts.py` 做最小常量追加 |
| 实际实现文件范围 | 通过 | 文件系统中 STORY-003 源实现对象为 `engine/normalizer.py`、`engine/quality.py`、`engine/contracts.py` |
| `engine/contracts.py` 边界 | 通过 | 当前补充为 schema version、dataset 名称、parquet 文件名、质量报告字段/格式和默认披露常量；meta-qa 仍需验证其保持纯常量模块 |
| 真实数据写入 | 通过 | `data/` 下仅有 `data/.gitkeep`；未发现真实 `data/*.parquet`、`data/raw/**` 或 `data/manifests/**` 文件 |
| 真实报告写入 | 通过 | `reports/` 下仅有 `reports/.gitkeep`；未发现真实 `reports/data_quality_report.*` |
| delivery 边界 | 通过 | `delivery/` 下未发现文件；不得生成安装脚本 |
| STORY-004+ 越界 | 通过 | 未发现 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py` 或 `strategies/**` 的 STORY-004+ 新实现 |
| 网络边界 | 待 QA 验证 | meta-dev 声明未真实调用 AKShare；meta-po 静态扫描未在 STORY-003 目标模块中发现 `akshare`、`AkshareAdapter`、`run_data_prep` 令牌 |
| guardrail 脚本缺口 | QA 观察项 | `scripts/check_delivery_guardrails.py` 不存在，且 `scripts/` 目录不存在；meta-qa 需要判断该缺口对 STORY-003 验证结论的影响，不得自行创建该脚本 |

说明：当前工作区不是 Git 仓库，meta-po 本轮范围复核基于文件系统清单、路径存在性、时间戳、源码静态扫描、状态文档和开发日志交叉验证。

## 3. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、门控、QA 观察项和禁止范围 |
| Story 状态汇总 | `process/STORY-STATUS.md` | 确认 `STORY-003=ready-for-verification`，W0 仍未完成 |
| Story 卡片 | `process/stories/STORY-003-parquet-quality-report.md` | 获取目标、验收标准、任务清单、依赖和禁止范围 |
| 已确认 LLD | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 验证接口设计、核心流程、异常路径、测试设计、回滚策略和 OPEN/Spike 状态 |
| LLD 检查点 | `checkpoints/STORY-003-LLD-CHECKPOINT.md` | 确认 LLD 人工门控已通过 |
| 实现 handoff | `process/handoffs/META-DEV-IMPLEMENT-W0-STORY-003-2026-05-15.md` | 复核 meta-dev 实现边界和禁止范围 |
| 验证环境 | `process/VALIDATION-ENV.yaml` | 确认正式验收环境仍为 `approval.confirmed=true` |
| 开发日志 | `DEV-LOG.md` | 获取 meta-dev 声明的验证命令、临时目录边界、已知限制和未执行项 |
| 实现文件 | `engine/normalizer.py`、`engine/quality.py`、`engine/contracts.py` | STORY-003 验证对象 |
| 上游实现只读上下文 | `engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py`、`config/data_prep.yaml` | 只读理解 raw/manifest 语义；不得改变 STORY-002 已验证行为 |

可按需读取：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `pyproject.toml`
- `uv.lock`

不得加载无关历史草稿或其他 Story 的 LLD。当前验证以 STORY-003 已确认 LLD 为准。

## 4. 验证要求

meta-qa 必须先刷新 `process/TEST-STRATEGY.md` 使其目标指向 `STORY-003`，再执行并刷新 `process/VERIFICATION-REPORT.md`。验证至少覆盖：

- `engine/normalizer.py` 支持 raw `.jsonl` metadata/data/payload 解析、manifest 关联、损坏行结构化错误。
- exact interface 或显式 `target_dataset` 只能映射到 `prices`、`index_members`、`trade_calendar`，不得使用模糊匹配。
- 三类标准化 parquet schema 覆盖 LLD 必需字段；写入必须使用临时目录，且使用同目录临时文件后原子替换。
- `engine/quality.py` 支持 manifest/parquet 质量计算、缺失率分母、交易日新鲜度、自然日新鲜度、数据源失败降级和 `pass/warn/fail` 判定。
- `close <= 0`、未解决重复键、必需字段缺失、覆盖缺口、缺失率 `> 5%` 均导致 `quality_status=fail`。
- `0 < missing_rate <= 5%` 导致 `quality_status=warn`。
- 数据源失败但本地 parquet 覆盖请求区间且 schema 合规时，报告披露失败批次，并按 LLD 允许路径输出 `warn/pass`。
- CSV/Markdown 报告字段覆盖 Story 验收标准中至少 14 类字段，并包含 `manifest_run_id`、`available_at_rule`、`adjustment_policy`、`is_pit_universe`、`survivorship_bias_note`。
- 静态检查确认 `engine/normalizer.py`、`engine/quality.py` 不导入 AKShare、不触发联网、不调用 `run_data_prep` 或 `AkshareAdapter`。
- 验证必须使用临时目录，不写真实 `data/*.parquet`、真实 `reports/data_quality_report.*`、真实 `data/raw/**` 或真实 `data/manifests/**`。
- 确认未写入 `delivery/**`、未生成安装脚本、未实现 `STORY-004+`。
- 将 `scripts/check_delivery_guardrails.py` 缺失记录为观察项或缺口，并判断是否影响 STORY-003 验证结论；不得为通过验证而创建该脚本。
- 按项目规则清理或避免 `.venv`、`__pycache__`、`*.pyc`、`.pytest_cache` 等验证过程缓存入库。

## 5. 禁止范围

- 禁止推进 `STORY-004+`，禁止起草其 LLD、实现其代码或生成其验证报告。
- 禁止创建或修改 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 禁止修改 `engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py` 的 STORY-002 已验证行为。
- 禁止真实调用 AKShare、聚宽或其他远程数据源。
- 禁止向真实 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet` 写入验证样例。
- 禁止向真实 `reports/data_quality_report.csv` 或 `reports/data_quality_report.md` 写入验证样例。
- 禁止写入 `delivery/**`、安装脚本、README、USER-MANUAL。
- 禁止创建缺失的 `scripts/check_delivery_guardrails.py`；该缺口只允许在验证报告中状态化。

## 6. 期望回写

若验证通过，meta-qa 应刷新：

- `process/TEST-STRATEGY.md`
- `process/VERIFICATION-REPORT.md`

验证报告必须明确列出：

- 验证命令与结果；
- `STORY-003` 的 PASS / FAIL / BLOCKED 结论；
- BLOCKING / REQUIRED / OBSERVATION findings；
- `scripts/check_delivery_guardrails.py` 缺失是否阻断 STORY-003；
- 是否发现真实 data/report、`delivery/**`、安装脚本或 STORY-004+ 越界。

meta-qa 不直接将 Story 推进为 `verified`。验证结论为 PASS 且无 BLOCKING/REQUIRED 失败项后，由 meta-po 回收并判断 W0 是否完成。
