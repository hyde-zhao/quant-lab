---
story_id: "STORY-002"
title: "数据准备节流重试与 manifest"
story_slug: "data-prep-throttle-manifest"
status: "verified"
priority: "P0"
wave: "W0"
depends_on: ["STORY-001"]
created_at: "2026-05-14"
updated_at: "2026-05-14"
approved_by: "meta-po"
approved_at: "2026-05-14"
source_hld: "process/HLD.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
lld_handoff: "process/handoffs/META-DEV-LLD-W0-STORY-002-2026-05-14.md"
lld_path: "process/stories/STORY-002-data-prep-throttle-manifest-LLD.md"
implementation_handoff: "process/handoffs/META-DEV-IMPLEMENT-W0-STORY-002-2026-05-14.md"
verification_handoff: "process/handoffs/META-QA-VERIFY-W0-STORY-002-2026-05-14.md"
verification_report: "process/VERIFICATION-REPORT.md"
verified_by: "meta-qa"
verified_at: "2026-05-14"
verification_result: "PASS"
---

# STORY-002：数据准备节流重试与 manifest

## 目标

创建独立可联网的数据准备编排层，实现保守节流、有限重试、退避、断点续传、raw 缓存写入和 JSONL manifest 记录。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求 | REQ-016, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-055 |
| HLD | §8.1, §8.2, §8.4, §12.1, §16 M0 |
| ADR | ADR-001, ADR-005 |

## 开发上下文（dev_context）

**背景说明**：联网能力只能存在于显式数据准备流程，且必须通过节流/重试/断点续传治理。回测主路径不得调用本 Story 产物。

**输入文件**：`config/data_prep.yaml`、`engine/contracts.py`、历史 `data/manifests/data_prep_manifest.jsonl`（若存在）、AKShare 接口参数。

**输出文件**：`engine/data_prep.py`、`engine/akshare_adapter.py`、`engine/manifest.py`、`data/raw/<source>/<interface>/<YYYYMMDD>/<batch_id>.<ext>`、`data/manifests/data_prep_manifest.jsonl`。

**接口约定**：Data Prep 接收 source、interface、params、symbol/date 范围和节流配置；AKShare Adapter 返回原始表格或结构化错误；Manifest Writer 追加 JSONL 事件或最终批次记录。

**错误约定**：重试耗尽后批次状态为 `failed` 或 `partial_success`；禁止无限循环；每次失败必须记录 `error_type`、`error_message`、等待秒数和 attempt 序号。

**设计约束**：默认 `request_interval_seconds=2`、`batch_size=50`、`max_concurrency=1`、`max_retries=3`、`backoff_policy=exponential_jitter`；raw 缓存第一版长期保留，不自动清理。

**命名规范**：`batch_id` 使用稳定可复现摘要；manifest 路径固定为 `data/manifests/data_prep_manifest.jsonl`。

**平台目标**：本地 Python 研究工具；仅数据准备入口允许联网。

### 文件布局边界

```text
engine/
├── data_prep.py
├── akshare_adapter.py
└── manifest.py
data/
├── raw/<source>/<interface>/<YYYYMMDD>/<batch_id>.<ext>
└── manifests/data_prep_manifest.jsonl
```

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| S002-T1 | 创建 | `engine/manifest.py` | 实现 manifest 读写、批次状态枚举和断点续传查询 |
| S002-T2 | 创建 | `engine/akshare_adapter.py` | 封装 AKShare 调用边界和结构化错误 |
| S002-T3 | 创建 | `engine/data_prep.py` | 编排批次规划、节流、重试、退避和 raw 写入 |
| S002-T4 | 修改 | `engine/contracts.py` | 补充 manifest 字段常量和状态枚举（若 STORY-001 未覆盖完整） |

## 验证上下文（validation_context）

**验证入口**：单元测试中的 fake adapter；manifest 样例读取；raw 写入路径检查。

**验证方式**：人工检查 + 单元测试 + 限速时间戳断言。

**依赖环境**：Python 3.11+、uv；可使用 fake AKShare adapter，真实网络不是验收必需前提。

**关键验证场景**：成功批次、连续失败后重试耗尽、断点续传跳过已成功批次、`force_refresh=false` 不重复抓取、最近 N 交易日回补允许重抓。

## 量化验收标准（acceptance_criteria）

- [x] 默认配置下相邻远程请求时间间隔 `>= 2` 秒。
- [x] 单批规模 `<= 50`，最大并发请求数 `<= 1`。
- [x] 同一批次最多执行 1 次初始请求加 3 次重试。
- [x] manifest 每个批次至少包含 HLD §8.4 的 18 类字段或条件字段。
- [x] 批次状态只使用 `pending`、`running`、`success`、`partial_success`、`failed`、`skipped`。
- [x] 数据准备模块不被 `engine/backtest.py`、`engine/scanner.py` 或 `engine/candidates.py` 导入为自动补数路径。

## 后续 LLD 输入约束

LLD 必须定义 batch planner 算法、manifest 追加一致性策略、raw 文件格式选择、重试退避伪代码、时间戳精度和 fake adapter 测试方式。

## 阻塞说明

STORY-001 已通过 meta-qa 正式 8 维度验收并由 meta-po 标记为 `verified`，本 Story 的前置依赖已满足。用户已明确回复 `确认通过`，meta-po 判定 STORY-002 LLD 人工确认通过。meta-dev 报告 STORY-002 实现完成，且声明只修改 `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`、`engine/contracts.py`；未实现 STORY-003；未创建 normalizer/parquet/quality report；未写真实 `data/raw/**` 或 `data/manifests/**`；未调用真实 AKShare；未写 delivery；验证使用 fake adapter 和临时目录。

meta-qa 已完成 STORY-002 正式验证，`process/VERIFICATION-REPORT.md` 中 STORY-002 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项。meta-po 已将本 Story 从 `ready-for-verification` 收敛为 `verified`。后续 W0 串行推进至 STORY-003 的 LLD 起草门控；STORY-002 不再阻塞下游依赖。
