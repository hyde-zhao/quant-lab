---
handoff_id: "META-DEV-LLD-W0-STORY-002-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-002"
story_slug: "data-prep-throttle-manifest"
status: "dispatched"
created_at: "2026-05-14"
---

# Handoff: meta-dev 起草 STORY-002 LLD

## 1. 分派结论

`STORY-001` 已通过 `meta-qa` 正式 8 维度验收，`process/VERIFICATION-REPORT.md` 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项。`meta-po` 已将 `STORY-001` 标记为 `verified`。

`STORY-002` 依赖 `STORY-001`，当前前置依赖已满足。`meta-po` 将 `STORY-002` 从 `draft` 推进为 `approved`，分派 `meta-dev` 起草 `STORY-002` LLD。此分派只允许输出 LLD，LLD 未经人工确认前不得实现代码。

`STORY-003` 仍依赖 `STORY-001` 与 `STORY-002`。由于 `STORY-002` 尚未完成 LLD、实现和验证，不得推进 `STORY-003`，不得生成 STORY-003 LLD 或代码。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、W0 依赖和 LLD 门控 |
| Story 状态 | `process/STORY-STATUS.md` | 确认 STORY-001 verified、STORY-002 approved、STORY-003 draft |
| Story 卡片 | `process/stories/STORY-002-data-prep-throttle-manifest.md` | 获取目标、任务清单、验收标准和边界 |
| 上游 Story 卡片 | `process/stories/STORY-001-engine-baseline-data-contracts.md` | 确认工程基线与契约骨架已 verified |
| 上游 LLD | `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md` | 读取已确认的契约对象形态和文件布局 |
| 验证报告 | `process/VERIFICATION-REPORT.md` | 确认 STORY-001 验收结论和禁止范围未越界 |
| HLD | `process/HLD.md` | 读取 §8.1、§8.2、§8.4、§12.1、§16 M0 |
| ADR | `process/ARCHITECTURE-DECISION.md` | 读取 ADR-001 与 ADR-005 |
| Story Backlog | `process/STORY-BACKLOG.md` | 确认 STORY-002 与相邻 Story 边界 |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` | 确认 W0 串行依赖与 output_files |

按需读取当前实现文件：

- `config/data_prep.yaml`
- `engine/contracts.py`
- `pyproject.toml`
- `uv.lock`

## 3. 允许输出

本轮只允许创建或更新：

- `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md`
- `process/stories/STORY-002-data-prep-throttle-manifest.md`
- `process/STORY-STATUS.md`
- `process/STATE.md`

LLD 完成后，`meta-dev` 应将 STORY-002 状态推进到 `ready-for-lld-review`，并回传给 `meta-po` 发起 Story LLD 人工确认。

## 4. LLD 必须覆盖

`STORY-002` LLD 必须保持 14 个可见章节，并至少覆盖以下设计点：

1. batch planner 算法：输入 source、interface、params、symbol/date 范围和 batch_size，输出稳定批次集合。
2. manifest 追加一致性策略：JSONL 字段、写入顺序、运行标识、批次状态和断点续传查询。
3. raw 文件格式选择：第一版 raw 缓存扩展名、路径模板和可复现 `batch_id` 生成规则。
4. 重试退避伪代码：默认 1 次初始请求加 3 次重试、`exponential_jitter`、等待秒数记录和禁止无限循环。
5. 时间戳精度：请求开始、请求结束、失败事件、manifest 写入时间的字段口径。
6. fake adapter 测试方式：不依赖真实网络完成成功批次、失败重试、断点续传和 `force_refresh=false` 验证。
7. 与 `engine/contracts.py` 的最小修改策略：仅在 STORY-001 常量不足时补充 manifest 字段常量和状态枚举。
8. 与后续 STORY-003 的边界：本 Story 不派生标准 parquet，不输出质量报告。

## 5. 允许修改范围

LLD 可设计但不得实现以下未来文件：

- `engine/data_prep.py`
- `engine/akshare_adapter.py`
- `engine/manifest.py`
- `engine/contracts.py` 中与 manifest 字段或状态枚举相关的最小补充
- `data/raw/<source>/<interface>/<YYYYMMDD>/<batch_id>.<ext>`
- `data/manifests/data_prep_manifest.jsonl`

## 6. 禁止范围

本轮明确禁止：

- 不得实现 `engine/data_prep.py`、`engine/akshare_adapter.py`、`engine/manifest.py`
- 不得修改 `engine/contracts.py` 或其他源代码文件
- 不得写入 `data/raw/**`、`data/manifests/**` 或任何真实数据样本
- 不得生成 `engine/normalizer.py`、`engine/quality.py`、`reports/data_quality_report.*`
- 不得推进、设计或实现 `STORY-003`
- 不得写入 `delivery/**`
- 不得生成安装脚本
- 不得调用真实 AKShare 网络接口
- 不得跳过 Story LLD 人工确认门控

## 7. 回传要求

LLD 完成后，`meta-dev` 需要回传：

- LLD 文件路径
- Story 状态变更为 `ready-for-lld-review` 的证据
- `STORY-002` LLD 是否满足 14 章节契约
- 未实现代码、未写 data、未写 delivery、未推进 STORY-003 的越界复核结论
