---
handoff_id: "META-DEV-LLD-W0-STORY-003-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-dev"
created_at: "2026-05-14"
phase: "story-execution"
wave: "W0"
story_id: "STORY-003"
task_type: "lld-draft"
status: "dispatched"
governance: "LLD 门控；不得实现"
---

# meta-dev 交接：STORY-003 LLD 起草

## 任务边界

请仅为 `STORY-003` 起草 LLD，输出目标为 `process/stories/STORY-003-parquet-quality-report-LLD.md`，并将 Story 状态推进到 `ready-for-lld-review` 后交回 meta-po 发起人工确认。

本交接不授权实现代码、生成 parquet、生成质量报告、写入 `delivery/**` 或生成安装脚本。LLD 未经人工确认前，不得创建或修改 `engine/normalizer.py`、`engine/quality.py`、`data/*.parquet`、`reports/data_quality_report.*`。

## 入口事实

| 项 | 状态 | 证据 |
|---|---|---|
| 当前阶段 | `story-execution` | `process/STATE.md` |
| 当前 Wave | W0，串行 | `process/DEVELOPMENT-PLAN.yaml` 中 `parallel=false` |
| STORY-001 | `verified` | `process/STORY-STATUS.md`、`process/VERIFICATION-REPORT.md` |
| STORY-002 | `verified` | `process/VERIFICATION-REPORT.md` 中 STORY-002 结论 PASS，无 BLOCKING/REQUIRED 失败项 |
| STORY-003 | `approved` | `process/stories/STORY-003-parquet-quality-report.md` |

## 必须读取的最小上下文

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、active story、门控状态 |
| `process/STORY-STATUS.md` | W0 状态、依赖收敛证据 |
| `process/DEVELOPMENT-PLAN.yaml` | W0 串行计划、STORY-003 依赖与输出边界 |
| `process/STORY-BACKLOG.md` | STORY-003 范围、验收目标、依赖图 |
| `process/stories/STORY-003-parquet-quality-report.md` | Story 卡、任务清单、验收标准 |
| `process/HLD.md` | §8.3、§8.5、§12.1、§12.4、§16 M0 设计依据 |
| `process/ARCHITECTURE-DECISION.md` | ADR-003、ADR-006 及质量阈值/降级决策 |
| `process/stories/STORY-002-data-prep-throttle-manifest.md` | 上游 raw/manifest 消费契约 |
| `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md` | 上游 manifest/raw 具体形态与异常约束 |
| `process/VERIFICATION-REPORT.md` | STORY-002 PASS 证据与不得越界事项 |
| `process/TEST-STRATEGY.md` | 当前 QA 口径与验证边界，作为后续 LLD 测试设计参考 |
| `engine/contracts.py`、`engine/manifest.py`、`engine/data_prep.py` | 只读理解上游实现契约，不得在 LLD 阶段修改 |

## LLD 输出要求

- 保持 `STORY-*-LLD.md` 的 14 个可见章节契约。
- frontmatter 必须包含 `story_id=STORY-003`、`tier`、`confirmed=false`、`shared_fragments`、`open_items`。
- 必须定义 raw 到 parquet 的映射、schema version 策略、质量报告输出格式、缺失率计算分母、交易日新鲜度算法、异常价格判定、错误处理与回滚策略。
- 必须覆盖测试设计：raw fixture 派生、parquet schema、quality report 阈值、重复键、`close <= 0`、数据源失败但本地 parquet 合规时的 warn/pass 行为。
- 必须显式说明不触发联网、不调用 AKShare、不实现策略回测、不自动清理 raw。

## 不应加载或修改

- 不加载历史草稿、旧失败轮次或无关 Story 的 LLD。
- 不修改 `delivery/**`。
- 不生成安装脚本。
- 不写真实 `data/raw/**`、`data/manifests/**`、`data/*.parquet` 或 `reports/data_quality_report.*`。
- 不实现 `engine/normalizer.py`、`engine/quality.py`；实现必须等待 STORY-003 LLD 人工确认。

## 交回条件

完成 LLD 起草后，请回写：

- `process/stories/STORY-003-parquet-quality-report-LLD.md`
- `process/stories/STORY-003-parquet-quality-report.md` 的状态为 `ready-for-lld-review`
- `process/STORY-STATUS.md`
- `process/STATE.md`

交回时说明：未实现代码、未生成数据文件、未写 `delivery/**`、未生成安装脚本。
