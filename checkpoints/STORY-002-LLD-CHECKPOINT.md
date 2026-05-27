---
checkpoint_id: "STORY-002-LLD"
checkpoint_type: "story-lld-confirmation"
story_id: "STORY-002"
story_title: "数据准备节流重试与 manifest"
story_slug: "data-prep-throttle-manifest"
status: "confirmed"
confirmed: true
created_by: "meta-po"
created_at: "2026-05-14"
updated_at: "2026-05-14"
lld_path: "process/stories/STORY-002-data-prep-throttle-manifest-LLD.md"
story_path: "process/stories/STORY-002-data-prep-throttle-manifest.md"
dev_log_path: "DEV-LOG.md"
---

# STORY-002 LLD 人工确认检查点

> 检查点 ④：Story LLD 确认。用户已确认通过，允许 STORY-002 按 LLD 限定范围进入实现。

## 1. 门控结论

`STORY-002` LLD 人工确认已通过。

用户明确回复 `确认通过`，语义记录为 `STORY-002` LLD 人工确认通过。meta-po 已将 LLD `confirmed=true`，并将 Story 推进到 `lld-approved`，分派 meta-dev 开始实现。

实现范围严格限定为：`engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`，以及仅在 STORY-001 常量不足时最小修改 `engine/contracts.py`。允许实现代码在测试中使用临时目录写入 raw/manifest 样例；禁止写入真实 `data/raw/**`、`data/manifests/**`，禁止实现 STORY-003 范围，禁止标准化 parquet、quality report、真实 AKShare 网络调用和 `delivery/**`。

## 2. 复核对象

| 对象 | 路径 | 复核结果 |
|---|---|---|
| Story 卡片 | `process/stories/STORY-002-data-prep-throttle-manifest.md` | 存在，frontmatter 已更新为 `status=lld-approved` |
| LLD 文档 | `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md` | 存在，frontmatter 已更新为 `status=confirmed`，`confirmed=true` |
| Story 状态汇总 | `process/STORY-STATUS.md` | 当前门控为 `implementation`，`STORY-002` 状态为 `lld-approved` |
| 运行态状态 | `process/STATE.md` | 保持 `current_phase=story-execution`，当前 agent 切换为 `meta-dev` |
| 开发过程日志 | `DEV-LOG.md` | 存在，记录 LLD 摘要、待确认点和越界复核；本检查点将其状态化为过程日志，不作为实现产物或交付物 |

## 3. Frontmatter 契约复核

| 字段 | 期望 | 实际 | 结论 |
|---|---|---|---|
| `story_id` | `STORY-002` | `STORY-002` | 通过 |
| `status` | `confirmed` | `confirmed` | 通过 |
| `confirmed` | `true` | `true` | 通过 |
| `tier` | `L` | `L` | 通过 |
| `shared_fragments` | `[]` | `[]` | 通过 |
| `open_items` | `0` | `0` | 通过 |
| `source_story` | Story 卡片路径 | `process/stories/STORY-002-data-prep-throttle-manifest.md` | 通过 |

## 4. 14 章节契约复核

LLD 文档包含 14 个编号可见章节，并保留独立人工确认区。

| # | 章节 |
|---:|---|
| 1 | Goal |
| 2 | Requirements（Functional / Non-Functional） |
| 3 | 模块拆分与职责 |
| 4 | 代码结构与文件影响范围 |
| 5 | 数据模型与持久化设计 |
| 6 | API / Interface 设计 |
| 7 | 核心处理流程 |
| 8 | 技术设计细节 |
| 9 | 安全与性能设计 |
| 10 | 测试设计 |
| 11 | 实施步骤 |
| 12 | 风险、难点与预研建议 |
| 13 | 回滚与发布策略 |
| 14 | Definition of Done |

## 5. DEV-LOG 状态化说明

`DEV-LOG.md` 当前内容只记录 STORY-002 LLD 摘要、待确认设计点、流程状态和越界复核。它未声明实现完成，未写入 `delivery/**`，也未改变 Story 生命周期。

由于 `DEV-LOG.md` 位于仓库根目录，不属于 `process/`、`checkpoints/`、`delivery/` 三类隔离输出区，本检查点将其明确状态化为“meta-dev 过程日志旁证”。本轮不把它作为交付物、不把它作为 LLD 批准依据、不把它作为实现范围扩展依据；后续若需要严格归档，应由 meta-po 单独组织迁移或改写为 `process/` 下运行态日志。

## 6. 实现范围门控

| 项 | 当前结论 | 说明 |
|---|---|---|
| 允许文件 | 仅允许 STORY-002 LLD 文件影响范围 | `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`；`engine/contracts.py` 仅限 manifest 字段常量和状态枚举最小补充 |
| 允许测试写入 | 仅允许临时目录 | raw/manifest 测试必须使用 pytest 临时目录或等价隔离目录，不得污染真实 `data/raw/**`、`data/manifests/**` |
| 禁止范围 | STORY-003 范围全部禁止 | 禁止标准化 parquet、quality reporter、`reports/data_quality_report.*`、normalizer、回测、扫描、候选、策略逻辑 |
| 真实网络 | 禁止作为实现或验证入口 | 测试必须使用 fake adapter，不得真实调用 AKShare 网络接口 |
| 交付目录 | 禁止写入 `delivery/**` | STORY-002 不生成安装脚本或交付文档 |

说明：本轮 meta-po 只更新流程状态、检查点与 handoff，不实现代码。

## 7. 本轮需确认的设计点

- 是否接受 raw 缓存第一版统一使用 `.jsonl`，并以第一行 metadata、后续 data/payload 行表达原始响应。
- 是否接受 `batch_id` 采用 canonical JSON + SHA-256 前 16 位摘要，格式为 `<source>.<interface>.<range_key>.<digest16>`。
- 是否接受 manifest append 顺序为 `skipped` 或 `running` 先行，成功 / 部分成功 / 失败终态后写；resume 只读取每个 `batch_id` 的最新记录。
- 是否接受 `partial_success` 不视为整批完成，后续运行仍可针对失败项或原批次重试。
- 是否接受 STORY-002 中 `standardized_output_path` 可为空字符串或 `null`，由 STORY-003 标准化 parquet 产物再补充关联。

## 8. 用户确认选项

1. 确认通过 - 当前 Story LLD 可进入实现；meta-po 后续才可将 Story 状态推进到 `lld-approved`。
2. 需要修改 - 请说明需要调整的实现设计；meta-po 将交由 meta-dev 修订 LLD 后重新确认。
3. 确认不通过 - 当前 Story 回退至 `approved`，重新组织 LLD 设计。

## 9. 确认记录

| 日期 | 用户回复 | meta-po 判定 | 状态更新 |
|---|---|---|---|
| 2026-05-14 | 确认通过 | STORY-002 LLD 人工确认通过 | LLD `confirmed=true`；Story `status=lld-approved`；已创建 meta-dev 实现交接 |
