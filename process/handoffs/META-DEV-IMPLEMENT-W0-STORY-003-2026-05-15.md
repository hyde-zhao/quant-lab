---
handoff_id: "META-DEV-IMPLEMENT-W0-STORY-003-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-dev"
phase: "story-execution"
wave: "W0"
story_id: "STORY-003"
story_slug: "parquet-quality-report"
status: "dispatched"
created_at: "2026-05-15"
---

# Handoff: meta-dev 实现 STORY-003

## 1. 分派结论

用户已明确回复 `确认通过`。meta-po 判定为 `STORY-003` LLD 人工确认通过，并已完成以下门控更新：

- `process/stories/STORY-003-parquet-quality-report-LLD.md`：`status=confirmed`，`confirmed=true`。
- `checkpoints/STORY-003-LLD-CHECKPOINT.md`：`status=confirmed`，`confirmed=true`。
- `process/stories/STORY-003-parquet-quality-report.md`：`status=lld-approved`。
- `process/STORY-STATUS.md`：`current_gate=implementation`，`STORY-003=lld-approved`。
- `process/STATE.md`：当前 agent 切换为 `meta-dev`，下一步为 STORY-003 实现。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认当前阶段、active_story、门控和禁止范围 |
| Story 卡片 | `process/stories/STORY-003-parquet-quality-report.md` | 获取目标、验收标准、依赖和任务清单 |
| 已确认 LLD | `process/stories/STORY-003-parquet-quality-report-LLD.md` | 作为唯一实现设计依据 |
| LLD 检查点 | `checkpoints/STORY-003-LLD-CHECKPOINT.md` | 确认人工门控已通过 |
| Story 状态 | `process/STORY-STATUS.md` | 回写实现状态时保持汇总一致 |
| 已验证契约 | `engine/contracts.py` | 仅追加 STORY-003 所需 schema、dataset、质量报告字段和格式常量 |
| 已验证数据准备模块 | `engine/manifest.py`, `engine/data_prep.py`, `engine/akshare_adapter.py` | 只读理解 raw/manifest 语义；不得改变 STORY-002 已验证行为 |
| 默认配置 | `config/data_prep.yaml` | 只读理解 raw/manifest 默认路径 |

可按需读取：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/VERIFICATION-REPORT.md`

不得加载无关历史草稿或其他 Story 的 LLD；当前实现以 `STORY-003` 已确认 LLD 为准。

## 3. 允许实现范围

meta-dev 只允许创建或修改以下源文件：

| 文件 | 任务 |
|---|---|
| `engine/normalizer.py` | 实现 raw JSONL 读取、exact interface/dataset 映射、字段别名转换、三类 dataset 标准化、schema 校验、重复键和异常价格处理、parquet 原子写入和标准化运行摘要 |
| `engine/quality.py` | 实现 parquet/manifest 质量计算、缺失率分母、新鲜度算法、数据源失败降级、未来函数/幸存者偏差披露、`pass/warn/fail` 判定、CSV/Markdown 报告渲染和结构化错误 |
| `engine/contracts.py` | 仅追加 `PARQUET_SCHEMA_VERSION`、`QUALITY_REPORT_SCHEMA_VERSION`、`DATASET_NAMES`、`QUALITY_REPORT_FIELDS`、`QUALITY_REPORT_FORMATS` 等常量；必须保持纯常量模块 |

测试代码如确有必要新增，必须只服务于 STORY-003 的 raw fixture、manifest fixture、parquet schema、质量阈值、异常路径和报告渲染验证。测试可使用临时目录生成 parquet 与 report 样例，不得污染真实运行目录。

## 4. 严格禁止范围

- 禁止实现 `STORY-004+` 任意范围。
- 禁止创建或修改 `engine/data_loader.py`、`engine/backtest.py`、`engine/scanner.py`、`engine/candidates.py`、`strategies/**`。
- 禁止修改 `engine/manifest.py`、`engine/data_prep.py`、`engine/akshare_adapter.py` 的 STORY-002 已验证行为，除非发现编译级阻塞并先状态化回报 meta-po。
- 禁止真实调用 AKShare、聚宽或其他远程数据源；测试必须使用 fixture、fake 或临时目录。
- 禁止向真实 `data/raw/**`、`data/manifests/**` 写入验证样例。
- 禁止向真实 `data/prices.parquet`、`data/index_members.parquet`、`data/trade_calendar.parquet` 写入测试样例；真实产物生成必须等实现入口被用户显式执行。
- 禁止向真实 `reports/data_quality_report.csv` 或 `reports/data_quality_report.md` 写入测试样例；报告测试必须使用临时目录。
- 禁止写入 `delivery/**`、安装脚本、README、USER-MANUAL。
- 禁止修改 `process/` 和 `checkpoints/` 中非状态回写所需文件。

## 5. 实现完成后的回写要求

实现完成后，meta-dev 应：

1. 将 `process/stories/STORY-003-parquet-quality-report.md` 状态从 `lld-approved` 更新为 `ready-for-verification`。
2. 更新 `process/STORY-STATUS.md` 中 STORY-003 状态与 W0 计数。
3. 更新 `process/STATE.md` 的 `last_action`、`next_action` 和 `history`，下一步指向 meta-po 复核后分派 meta-qa 验证。
4. 如记录开发日志，只记录 STORY-003 范围内的实现命令、文件和偏差。

## 6. 验收入口

至少执行或准备以下验证：

- raw `.jsonl` metadata/data/payload 解析、manifest 关联和损坏行结构化错误。
- exact interface 或显式 `target_dataset` 到 `prices`、`index_members`、`trade_calendar` 的映射，不做模糊匹配。
- 三类 parquet schema 覆盖 LLD 必需字段，写入使用同目录临时文件后原子替换。
- `close <= 0`、未解决重复键、必需字段缺失、覆盖缺口、缺失率 `> 5%` 均导致 `quality_status=fail`。
- `0 < missing_rate <= 5%` 导致 `quality_status=warn`。
- 数据源失败但本地 parquet 覆盖请求区间且 schema 合规时，报告披露失败批次，并可按 LLD 输出 `warn/pass`。
- 交易日新鲜度与自然日新鲜度使用固定 `as_of_date` 可测。
- CSV/Markdown 报告字段覆盖 Story 验收标准中至少 14 类字段，并包含 `manifest_run_id`、`available_at_rule`、`adjustment_policy`、`is_pit_universe`、`survivorship_bias_note`。
- 静态检查确认 `engine/normalizer.py`、`engine/quality.py` 不导入 AKShare、不触发联网、不写 `delivery/**`。
