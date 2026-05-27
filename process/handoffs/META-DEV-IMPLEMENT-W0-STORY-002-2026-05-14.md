---
handoff_id: "META-DEV-IMPLEMENT-W0-STORY-002-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-002"
story_slug: "data-prep-throttle-manifest"
status: "dispatched"
created_at: "2026-05-14"
---

# Handoff: meta-dev 实现 STORY-002

## 1. 分派结论

用户已明确回复 `确认通过`。meta-po 判定为 `STORY-002` LLD 人工确认通过，并已完成以下门控更新：

- `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md`：`status=confirmed`，`confirmed=true`。
- `checkpoints/STORY-002-LLD-CHECKPOINT.md`：`status=confirmed`，`confirmed=true`。
- `process/stories/STORY-002-data-prep-throttle-manifest.md`：`status=lld-approved`。
- `process/STORY-STATUS.md`：`current_gate=implementation`，`STORY-002=lld-approved`。
- `process/STATE.md`：当前 agent 切换为 `meta-dev`，下一步为 STORY-002 实现。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、门控和禁止范围 |
| Story 卡片 | `process/stories/STORY-002-data-prep-throttle-manifest.md` | 获取目标、验收标准、依赖和任务清单 |
| 已确认 LLD | `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md` | 作为唯一实现设计依据 |
| LLD 检查点 | `checkpoints/STORY-002-LLD-CHECKPOINT.md` | 确认人工门控已通过 |
| Story 状态 | `process/STORY-STATUS.md` | 回写实现状态时保持汇总一致 |
| 已验证契约 | `engine/contracts.py` | 仅判断 manifest 字段常量和状态枚举是否需要最小补充 |
| 默认配置 | `config/data_prep.yaml` | 读取 STORY-001 已落地的节流、批次、重试、回补和路径默认值 |

可按需读取：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/VERIFICATION-REPORT.md`

不得加载无关历史草稿或其他 Story 的 LLD；当前实现以 `STORY-002` 已确认 LLD 为准。

## 3. 允许实现范围

meta-dev 只允许创建或修改以下文件：

| 文件 | 任务 |
|---|---|
| `engine/manifest.py` | 实现 `ManifestStore`、append-only JSONL 写入、latest 查询、resume 所需状态聚合、manifest 记录构造和解析错误 |
| `engine/akshare_adapter.py` | 实现 `AkshareAdapter.fetch`、结构化 `AdapterResult` / `AdapterError`、接口名校验和 fake adapter 协议兼容；真实 AKShare 仅允许封装在本文件中 |
| `engine/data_prep.py` | 实现配置读取、Batch Planner、`batch_id`、resume filter、节流重试、指数抖动退避、raw `.jsonl` 写入和 `run_data_prep` 运行摘要 |
| `engine/contracts.py` | 仅在 STORY-001 字段不足时，最小补充 manifest 字段常量和状态枚举；必须保持纯常量、无 I/O、无 AKShare、无重型依赖导入 |

测试代码如确有必要新增，必须只服务于 STORY-002 的 fake adapter、临时 raw/manifest、节流重试、resume 和错误路径验证，不得覆盖 STORY-003 的 normalizer、parquet 或 quality report。

## 4. 严格禁止范围

- 禁止实现 `STORY-003` 任意范围。
- 禁止创建 `engine/normalizer.py`、`engine/quality.py`、parquet writer、quality reporter 或 `reports/data_quality_report.*`。
- 禁止生成或标准化 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`。
- 禁止修改回测、扫描、候选、策略或报告主路径以自动补数。
- 禁止把 `engine.data_prep` 或 `engine.akshare_adapter` 导入回测主路径作为自动联网入口。
- 禁止在测试或验收中真实调用 AKShare 网络接口；必须使用 fake adapter。
- 禁止向真实 `data/raw/**` 或 `data/manifests/**` 写入验证样例；测试必须使用临时目录。
- 禁止写入 `delivery/**`、安装脚本、README、USER-MANUAL。
- 禁止修改 `process/` 和 `checkpoints/` 中非状态回写所需文件。

## 5. 实现完成后的回写要求

实现完成后，meta-dev 应：

1. 将 `process/stories/STORY-002-data-prep-throttle-manifest.md` 状态从 `lld-approved` 更新为 `ready-for-verification`。
2. 更新 `process/STORY-STATUS.md` 中 STORY-002 状态与 W0 计数。
3. 更新 `process/STATE.md` 的 `last_action`、`next_action` 和 `history`，下一步指向 meta-po 复核后分派 meta-qa 验证。
4. 如记录开发日志，只记录 STORY-002 范围内的实现命令、文件和偏差。

## 6. 验收入口

至少执行或准备以下验证：

- `engine/manifest.py` 支持 append-only JSONL、latest 查询、resume 查询和损坏行结构化错误。
- `engine/akshare_adapter.py` 支持 fake adapter 协议兼容，真实 AKShare 网络调用不得出现在测试路径。
- `engine/data_prep.py` 支持配置读取、稳定 batch planning、`batch_id` 可复现、节流重试、raw `.jsonl` 写入和运行摘要。
- 默认相邻请求开始时间间隔 `>=2` 秒，单批 item 数 `<=50`，最大并发 `<=1`，同一批次最多 1 次初始请求加 3 次重试。
- manifest 终态覆盖 HLD §8.4 字段和 LLD 时间戳字段，状态只使用 `pending`、`running`、`success`、`partial_success`、`failed`、`skipped`。
- raw/manifest 测试使用临时目录，不写真实 `data/raw/**` 或 `data/manifests/**`。
- 静态检查确认不存在从回测、扫描、候选模块到 `engine.data_prep` / `engine.akshare_adapter` 的自动补数导入。
- 确认未创建或修改 STORY-003 范围文件，未写入 `delivery/**`。
