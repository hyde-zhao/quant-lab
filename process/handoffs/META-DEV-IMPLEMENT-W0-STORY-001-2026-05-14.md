---
handoff_id: "META-DEV-IMPLEMENT-W0-STORY-001-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-001"
story_slug: "engine-baseline-data-contracts"
status: "dispatched"
created_at: "2026-05-14"
---

# Handoff: meta-dev 实现 STORY-001

## 1. 分派结论

用户已明确回复“确认通过，继续推进”。meta-po 判定为 `STORY-001` LLD 人工确认通过，并已完成以下门控更新：

- `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md`：`status=confirmed`，`confirmed=true`。
- `checkpoints/STORY-001-LLD-CHECKPOINT.md`：`status=confirmed`，`confirmed=true`。
- `process/stories/STORY-001-engine-baseline-data-contracts.md`：`status=lld-approved`。
- `process/STORY-STATUS.md`：`current_gate=implementation`，`STORY-001=lld-approved`。
- `process/STATE.md`：当前 agent 切换为 `meta-dev`，下一步为 STORY-001 实现。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、门控和禁止范围 |
| Story 卡片 | `process/stories/STORY-001-engine-baseline-data-contracts.md` | 获取目标、验收标准和输出文件 |
| 已确认 LLD | `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md` | 作为唯一实现设计依据 |
| LLD 检查点 | `checkpoints/STORY-001-LLD-CHECKPOINT.md` | 确认人工门控已通过 |
| Story 状态 | `process/STORY-STATUS.md` | 回写实现状态时保持汇总一致 |

可按需读取：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/DEVELOPMENT-PLAN.yaml`

不得加载无关历史草稿或其他 Story 的 LLD；当前实现以 `STORY-001` 已确认 LLD 为准。

## 3. 允许实现范围

meta-dev 只允许创建或修改以下 8 个文件：

| 文件 | 任务 |
|---|---|
| `pyproject.toml` | 声明项目元数据、Python `>=3.11,<3.13`、最小运行依赖和 pytest 开发依赖 |
| `uv.lock` | 通过 `uv lock` 生成锁文件 |
| `config/data_prep.yaml` | 写入节流、批大小、并发、重试、退避、回补、raw 缓存保留和路径模板默认值 |
| `engine/__init__.py` | 建立 `engine` 包，不执行副作用导入 |
| `engine/contracts.py` | 定义 parquet 字段、manifest 字段、质量状态、配置键、报告字段列表和 `__all__` |
| `strategies/__init__.py` | 建立 `strategies` 包，不导入策略实现 |
| `data/.gitkeep` | 保留数据目录 |
| `reports/.gitkeep` | 保留报告目录 |

可运行必要的依赖管理命令：

```bash
uv lock
uv sync
uv run --python 3.11 python -c "import engine.contracts"
```

命令只能服务于 STORY-001 依赖入口、锁文件和导入验证，不得扩展实现范围。

## 4. 严格禁止范围

- 禁止实现 `STORY-002+` 任意范围。
- 禁止 data fetcher、AKShare 调用入口、节流执行器、断点续传、raw cache 写入逻辑。
- 禁止 manifest writer 或 manifest JSONL 生成逻辑。
- 禁止 parquet normalizer、quality report 或质量统计生成逻辑。
- 禁止回测引擎、Data Loader、portfolio engine、metrics、parameter sweep、candidate report。
- 禁止策略逻辑、RSI/MACD 示例或任何 `strategies/*.py` 策略文件。
- 禁止写入 `delivery/**`、安装脚本、README、USER-MANUAL。
- 禁止修改 `process/` 和 `checkpoints/` 中非状态回写所需文件。

## 5. 实现完成后的回写要求

实现完成后，meta-dev 应：

1. 将 `process/stories/STORY-001-engine-baseline-data-contracts.md` 状态从 `lld-approved` 更新为 `ready-for-verification`。
2. 更新 `process/STORY-STATUS.md` 中 STORY-001 状态与 W0 计数。
3. 更新 `process/STATE.md` 的 `last_action`、`next_action` 和 `history`，下一步指向 meta-qa 验证。
4. 如创建开发日志，仅记录 STORY-001 范围内的实现命令、文件和偏差。

## 6. 验收入口

至少执行或准备以下验证：

- 8 个允许路径存在，其中 `.gitkeep` 可为空，其余文件非空。
- `pyproject.toml` 未声明 RQAlpha、Backtrader、vectorbt、bt。
- `config/data_prep.yaml` 包含 `request_interval_seconds`、`batch_size`、`max_concurrency`、`max_retries`、`backoff_policy`、`recent_trade_days_backfill`。
- `engine/contracts.py` 可通过 `uv run --python 3.11 python -c "import engine.contracts"` 导入。
- `engine/contracts.py` 不导入 pandas、pyarrow、akshare，不执行 I/O 或网络调用。
