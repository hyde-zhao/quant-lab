---
handoff_id: "META-QA-VERIFY-W0-STORY-002-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-qa"
phase: "story-execution"
wave: "W0"
story_id: "STORY-002"
story_slug: "data-prep-throttle-manifest"
status: "dispatched"
created_at: "2026-05-14"
---

# Handoff: meta-qa 验证 STORY-002

## 1. 分派结论

meta-dev 报告 `STORY-002` 实现完成。meta-po 已完成实现范围静态复核，并将 Story 推进到 `ready-for-verification`。本次分派只允许 meta-qa 验证 `STORY-002`，不得推进或验证 `STORY-003`。

## 2. meta-po 复核事实

| 复核项 | 结论 | 证据 |
|---|---|---|
| Story / LLD 允许实现文件 | 通过 | `STORY-002` Story 与 LLD 允许 `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`，以及必要时最小补充 `engine/contracts.py` |
| 实际实现文件范围 | 通过 | 当前文件系统存在并需验证的 STORY-002 源文件为 `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`、`engine/contracts.py` |
| STORY-003 越界 | 通过 | 未发现 `engine/normalizer.py`、`engine/quality.py`、parquet writer、quality report 或 `reports/data_quality_report.*` |
| 真实数据写入 | 通过 | `data/` 下仅有 `data/.gitkeep`，未发现真实 `data/raw/**` 或 `data/manifests/**` 文件 |
| delivery 边界 | 通过 | 未发现 `delivery/**` 文件；不得生成安装脚本 |
| 网络边界 | 待 QA 验证 | meta-dev 声明未真实调用 AKShare；meta-qa 需通过测试/静态检查确认默认验证路径使用 fake adapter 和临时目录 |

## 3. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、门控和禁止范围 |
| Story 状态汇总 | `process/STORY-STATUS.md` | 确认 `STORY-002=ready-for-verification`，`STORY-003=draft` |
| Story 卡片 | `process/stories/STORY-002-data-prep-throttle-manifest.md` | 验收标准、任务清单、边界和依赖 |
| 已确认 LLD | `process/stories/STORY-002-data-prep-throttle-manifest-LLD.md` | 验证接口设计、流程、异常路径、测试设计和回滚策略 |
| LLD 检查点 | `checkpoints/STORY-002-LLD-CHECKPOINT.md` | 确认人工门控已通过 |
| 实现 handoff | `process/handoffs/META-DEV-IMPLEMENT-W0-STORY-002-2026-05-14.md` | 复核 meta-dev 实现边界和禁止范围 |
| 验证环境 | `process/VALIDATION-ENV.yaml` | 确认正式验收环境仍为 `approval.confirmed=true` |
| 默认配置 | `config/data_prep.yaml` | 验证配置键、默认节流、批次、重试和路径约束 |
| 实现文件 | `engine/manifest.py`、`engine/akshare_adapter.py`、`engine/data_prep.py`、`engine/contracts.py` | STORY-002 验证对象 |

可按需读取 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/DEVELOPMENT-PLAN.yaml`。不得加载无关历史草稿或其他 Story 的 LLD。

## 4. 验证要求

meta-qa 必须先刷新 `process/TEST-STRATEGY.md` 使其目标指向 `STORY-002`，再执行并刷新 `process/VERIFICATION-REPORT.md`。验证至少覆盖：

- `engine/manifest.py` 支持 append-only JSONL、latest 查询、resume 查询和损坏行结构化错误。
- `engine/akshare_adapter.py` 支持 fake adapter 协议兼容；真实 AKShare 网络调用不得出现在默认测试路径。
- `engine/data_prep.py` 支持安全配置读取、稳定 batch planning、`batch_id` 可复现、resume filter、节流重试、raw `.jsonl` 写入和运行摘要。
- 默认相邻请求开始时间间隔 `>=2` 秒，单批 item 数 `<=50`，最大并发 `<=1`，同一批次最多 1 次初始请求加 3 次重试。
- manifest 终态覆盖 STORY-002 LLD §5.3 字段和 HLD §8.4 字段，状态只使用 `pending`、`running`、`success`、`partial_success`、`failed`、`skipped`。
- raw/manifest 验证必须使用临时目录，不写真实 `data/raw/**` 或 `data/manifests/**`。
- 静态检查确认不存在从回测、扫描、候选模块到 `engine.data_prep` / `engine.akshare_adapter` 的自动补数导入。
- 确认未创建或修改 STORY-003 范围文件，未写入 `delivery/**`、未生成安装脚本。
- 按项目规则清理或避免 `.venv`、`__pycache__`、`*.pyc` 等验证过程缓存入库。

## 5. 禁止范围

- 禁止推进 `STORY-003`，禁止起草其 LLD、实现其代码或生成其验证报告。
- 禁止创建 `engine/normalizer.py`、`engine/quality.py`、parquet writer、quality reporter 或 `reports/data_quality_report.*`。
- 禁止生成或标准化 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet`。
- 禁止真实调用 AKShare 网络接口；验证必须使用 fake adapter 和临时目录。
- 禁止写入真实 `data/raw/**` 或 `data/manifests/**`。
- 禁止写入 `delivery/**`、安装脚本、README、USER-MANUAL。

## 6. 期望回写

若验证通过，meta-qa 应刷新：

- `process/TEST-STRATEGY.md`
- `process/VERIFICATION-REPORT.md`

meta-qa 不直接将 Story 推进为 `verified`。验证结论为 PASS 且无 BLOCKING/REQUIRED 失败项后，由 meta-po 回收并判断 W0 下一步。
