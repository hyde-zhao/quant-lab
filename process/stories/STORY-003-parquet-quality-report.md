---
story_id: "STORY-003"
title: "标准化 parquet 与数据质量报告"
story_slug: "parquet-quality-report"
status: "verified"
priority: "P0"
wave: "W0"
depends_on: ["STORY-001", "STORY-002"]
created_at: "2026-05-14"
updated_at: "2026-05-15"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
approved_by: "meta-po"
approved_at: "2026-05-14"
lld_handoff: "process/handoffs/META-DEV-LLD-W0-STORY-003-2026-05-14.md"
lld_path: "process/stories/STORY-003-parquet-quality-report-LLD.md"
implementation_handoff: "process/handoffs/META-DEV-IMPLEMENT-W0-STORY-003-2026-05-15.md"
bugfix_handoff: "process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md"
verification_result: "PASS"
blocking_bug: "BUG-STORY-003-001"
blocking_bug_status: "CLOSED / REGRESSION_PASS"
cr004_batch_d_lld_revision:
  status: "cp5-approved"
  lld_path: "process/stories/STORY-003-parquet-quality-report-LLD.md"
  cp5_precheck: "process/checks/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-PRECHECK.md"
  cp5_review: "checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md"
  cp5_status: "approved"
  confirmed_by: "user"
  confirmed_at: "2026-05-17T15:53:20+08:00"
  implementation_allowed: true
  scope_note: "Legacy quality CR-004 alignment addendum approved; only allows bounded follow-up handling of CR-004 quality field alignment and does not reopen verified runtime behavior beyond that scope."
verified_by: "meta-qa"
verified_at: "2026-05-15"
---

# STORY-003：标准化 parquet 与数据质量报告

## 目标

从 raw 缓存派生标准化 parquet，并基于 parquet 与 manifest 输出数据质量报告、质量状态和数据新鲜度字段。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-021, REQ-022, REQ-052, REQ-053, REQ-054, REQ-056, REQ-057 |
| HLD | §8.3, §8.5, §12.1, §12.4, §16 M0 |
| ADR | ADR-003, ADR-006 |

## 开发上下文（dev_context）

**背景说明**：回测主路径只读取标准化 parquet、manifest 和质量报告。本 Story 是 M0 到 M1 的数据契约桥梁。

**输入文件**：`data/raw/**`、`data/manifests/data_prep_manifest.jsonl`、`engine/contracts.py`、`config/data_prep.yaml`。

**输出文件**：`engine/normalizer.py`、`engine/quality.py`、`data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`、`reports/data_quality_report.*`。

**接口约定**：Normalizer 读取 raw_path 和 schema_version，输出标准化 parquet；Quality Reporter 读取 parquet 与 manifest，输出覆盖、缺失、失败、重复、异常价格、回补和新鲜度。

**错误约定**：必需字段缺失、不可解析日期、未解决重复键、异常非缺失价格或请求区间缺失率 > 5% 时 `quality_status=fail`；0 < 缺失率 <= 5% 时 `warn`。

**设计约束**：`prices.parquet` 必需字段为 `trade_date`、`symbol`、`close`；`index_members.parquet` 必需字段为 `symbol`；`trade_calendar.parquet` 必需字段为 `trade_date`。

**命名规范**：标准化文件路径固定；质量报告必须通过 `manifest_run_id` 关联 manifest。

**平台目标**：本地 Python 研究工具；标准化 parquet 只由数据准备/更新流程写入。

### 文件布局边界

```text
engine/
├── normalizer.py
└── quality.py
data/
├── prices.parquet
├── index_members.parquet
└── trade_calendar.parquet
reports/
└── data_quality_report.*
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S003-T1 | 创建 | `engine/normalizer.py` | 实现 raw 到 prices/index_members/trade_calendar parquet 的派生接口 |
| S003-T2 | 创建 | `engine/quality.py` | 实现质量统计、阈值判定和新鲜度计算 |
| S003-T3 | 修改 | `engine/contracts.py` | 固化报告字段、质量状态和 schema version |
| S003-T4 | 创建 | `reports/data_quality_report.*` | 由实现运行生成，LLD 需指定 CSV/Markdown/JSON 形态 |

## 验证上下文（validation_context）

**验证入口**：raw fixture 派生测试、parquet schema 测试、quality report 阈值测试。

**验证方式**：单元测试 + 人工检查报告字段。

**依赖环境**：Python 3.11+、uv、pandas、pyarrow；不要求联网。

**关键验证场景**：完整数据 pass、少量缺失 warn、缺失率 >5% fail、重复键 fail、`close <= 0` fail、最近 5 个交易日回补统计。

## 量化验收标准（acceptance_criteria）

- [ ] 三类 parquet 均包含 HLD §8.3 的全部必需字段。
- [ ] 质量报告至少输出 14 类字段：覆盖区间、缺失率、失败数、失败 symbol/date、字段缺失、重复记录、异常价格、回补交易日、回补记录、最近成功更新时间、交易日新鲜度、自然日新鲜度、`quality_status`、`manifest_run_id`。
- [ ] `quality_status` 仅取 `pass`、`warn`、`fail`。
- [ ] 删除标准化 parquet 但保留 raw 与 manifest 时，设计上可重新派生等价 schema 的 parquet。
- [ ] 数据源失败但本地 parquet 合规时，质量报告可披露失败项且允许 M1 按 warn/pass 继续。

## 后续 LLD 输入约束

LLD 必须定义 raw 格式映射、schema version 升级策略、质量报告输出格式、缺失率计算分母、交易日新鲜度算法和异常价格判断。

## 阻塞说明

STORY-001 与 STORY-002 均已通过 meta-qa 正式验证，并由 meta-po 标记为 `verified`。W0 为串行 Wave，STORY-003 的前置依赖已满足；meta-po 已将本 Story 推进到 `approved`，仅允许 meta-dev 起草 LLD。

meta-dev 已按 `process/handoffs/META-DEV-LLD-W0-STORY-003-2026-05-14.md` 起草 `process/stories/STORY-003-parquet-quality-report-LLD.md`，frontmatter `confirmed=true`、`tier=L`、`open_items=0`。用户已回复 `确认通过`，meta-po 已将本 Story 推进到 `lld-approved`，并创建 `process/handoffs/META-DEV-IMPLEMENT-W0-STORY-003-2026-05-15.md` 分派 meta-dev 在已确认 LLD 限定范围内实现。

当前允许 meta-dev 仅实现 `engine/normalizer.py`、`engine/quality.py`，并在 `engine/contracts.py` 中追加 STORY-003 所需常量；测试可在临时目录生成 parquet 与质量报告样例。仍不得写真实 `data/*.parquet`、真实 `reports/data_quality_report.*`、安装脚本或 `delivery/**` 文件，不得进入 STORY-004+ 范围。

## 缺陷状态

| Bug ID | 严重级别 | 状态 | 路由 | 整改目标 |
|---|---|---|---|---|
| BUG-STORY-003-001 | BLOCKING | CLOSED / REGRESSION_PASS | closed | `engine/quality.py` 必需字段缺失路径已通过 meta-qa 回归；STORY-003 可收敛为 verified |

### 验证失败结论

meta-qa 已完成 STORY-003 正式验证，`process/VERIFICATION-REPORT.md` 中 STORY-003 结论为 `FAIL`，不是环境 `BLOCKED`。失败项为 `BUG-STORY-003-001`：`prices.parquet` 缺少必需字段 `close` 时，`engine/quality.py` 直接访问 `prices["close"]` / `in_range[..., "close"]` 并抛出 `KeyError: 'close'`，未按 Story / LLD 输出 `missing_required_fields=['prices.close']` 与 `quality_status=fail`。

meta-po 已将本 Story 退回 `in-development`，并创建 `process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md` 分派 meta-dev 进行限定范围整改。整改不得修改需求、HLD、LLD 或 STORY-004+ 范围，不得写真实 `data/*.parquet`、真实 `reports/data_quality_report.*`、`delivery/**` 或安装脚本。

### 修复提交结论

meta-dev 已按 `process/handoffs/META-DEV-BUGFIX-W0-STORY-003-2026-05-15.md` 完成限定范围修复，仅修改 `engine/quality.py`。修复后缺 `prices.close`、缺 `prices.symbol`、缺 `prices.trade_date` 均不再抛裸 `KeyError`，`missing_required_fields` 分别包含对应字段，且 `quality_status=fail`。

本 Story 已提交到 `ready-for-verification`，等待 meta-po 复核并重新分派 meta-qa 对 `BUG-STORY-003-001` 与 STORY-003 关键质量路径做回归验证。

### 回归收敛结论

meta-qa 已完成 `BUG-STORY-003-001` 回归验证，`process/VERIFICATION-REPORT.md` 中回归结论为 PASS，Bug 状态建议为 `CLOSED / REGRESSION_PASS`。三类必需字段缺失路径 `prices.close`、`prices.symbol`、`prices.trade_date` 均已结构化返回 `missing_required_fields` 与 `quality_status=fail`，不再抛裸 `KeyError`。

meta-po 已据此关闭 `BUG-STORY-003-001`，并将 STORY-003 从 `ready-for-verification` 收敛为 `verified`。本轮非阻断观察项 `scripts/check_delivery_guardrails.py` 缺失与 `process/VALIDATION-ENV.yaml story_id` 元数据滞后已状态化到 `process/STATE.md` 与 `process/STORY-STATUS.md`，不阻断 W0 收敛。
