---
handoff_id: "META-QA-VERIFY-W0-STORY-001-2026-05-14"
from_agent: "meta-po"
to_agent: "meta-qa"
phase: "story-execution"
wave: "W0"
story_id: "STORY-001"
story_slug: "engine-baseline-data-contracts"
status: "completed"
created_at: "2026-05-14"
redispatched_at: "2026-05-14"
completed_at: "2026-05-14"
verification_report: "process/VERIFICATION-REPORT.md"
---

# Handoff: meta-qa 验证 STORY-001

## 1. 分派结论

`meta-dev` 已报告 STORY-001 实现完成。`meta-po` 已按 Story / LLD 复核实现源文件范围，并将 `STORY-001` 状态推进到 `ready-for-verification`。用户已确认 `process/VALIDATION-ENV.yaml` 中的验证环境，当前 `approval.confirmed=true`。

本轮重新分派 `meta-qa` 执行 STORY-001 正式 8 维度验收。不得推进 STORY-002，不得生成 `delivery/**`、安装脚本、data fetcher、manifest writer、quality report、回测引擎或策略逻辑。

## 2. 必须读取的最小上下文

| 类型 | 路径 | 用途 |
|---|---|---|
| 当前状态 | `process/STATE.md` | 确认阶段、active_story、当前门控和禁止范围 |
| Story 状态 | `process/STORY-STATUS.md` | 确认 STORY-001 已进入 `ready-for-verification` |
| 验证环境 | `process/VALIDATION-ENV.yaml` | 确认当前验证环境已由用户确认，`approval.confirmed=true` |
| Story 卡片 | `process/stories/STORY-001-engine-baseline-data-contracts.md` | 获取目标、验收标准和输出文件 |
| 已确认 LLD | `process/stories/STORY-001-engine-baseline-data-contracts-LLD.md` | 作为验证依据 |
| LLD 检查点 | `checkpoints/STORY-001-LLD-CHECKPOINT.md` | 确认 LLD 人工门控已通过 |
| 实现分派单 | `process/handoffs/META-DEV-IMPLEMENT-W0-STORY-001-2026-05-14.md` | 复核实现允许范围和禁止范围 |

按需读取：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `pyproject.toml`
- `uv.lock`
- `config/data_prep.yaml`
- `engine/__init__.py`
- `engine/contracts.py`
- `strategies/__init__.py`
- `data/.gitkeep`
- `reports/.gitkeep`

## 3. 验证范围

meta-qa 需要验证以下事实：

1. 8 个 STORY-001 允许路径均存在：`pyproject.toml`、`uv.lock`、`config/data_prep.yaml`、`engine/__init__.py`、`engine/contracts.py`、`strategies/__init__.py`、`data/.gitkeep`、`reports/.gitkeep`。
2. `.gitkeep` 允许为空；其余 6 个文件必须非空。
3. `pyproject.toml` 使用 Python `>=3.11,<3.13`，包含 `pandas`、`pyarrow`、`akshare`、`PyYAML`、`pytest`，未声明 RQAlpha、Backtrader、vectorbt、bt。
4. `uv.lock` 与 `pyproject.toml` 当前依赖声明一致。
5. `config/data_prep.yaml` 包含节流、批量、并发、重试、退避、回补、raw 缓存保留和 raw 路径模板默认值。
6. `engine/contracts.py` 可导入，且不导入 pandas、pyarrow、akshare，不执行 I/O，不访问网络。
7. `engine/contracts.py` 覆盖三类 parquet 字段、manifest 字段、manifest 状态、`pass/warn/fail` 质量状态、数据准备配置键和至少 2 个报告字段列表。
8. 未出现 STORY-002+ 的源实现文件或逻辑，包括 data fetcher、AKShare 调用入口、manifest writer、quality report、parquet normalizer、Data Loader、portfolio engine、backtest、metrics、scanner、candidate report、策略逻辑。
9. 未写入 `delivery/**`，未生成安装脚本。
10. 导入验证产生的 `engine/__pycache__/` 属于缓存文件；需要在验证报告中标记为清理 / 禁入库关注项，不得视为 STORY-001 源实现范围。

## 4. 建议命令

可执行只读或验证型命令：

```bash
find config engine strategies data reports delivery -maxdepth 3 -type f | sort
uv run --python 3.11 python -c "import engine.contracts"
uv run --python 3.11 python -c "from engine import contracts as c; assert c.QUALITY_STATUS_VALUES == ('pass', 'warn', 'fail')"
```

如需验证锁文件，可使用 uv 的检查能力或只读解析；不得运行会扩展依赖或修改实现范围的命令。

## 5. 允许输出

meta-qa 可在流程区输出验证产物：

- `process/TEST-STRATEGY.md`：如当前阶段首次验证需要测试策略前置，可创建或更新。
- `process/VERIFICATION-REPORT.md` 或 Story 级验证报告：记录 STORY-001 验证结果、命令、通过项、失败项和 QA 建议。

meta-qa 不得输出：

- `delivery/**`
- `delivery/scripts/**`
- 安装脚本
- STORY-002+ 实现文件
- data fetcher、manifest writer、quality report、回测或策略逻辑

## 6. 验证结论回传

验证通过时，meta-qa 应报告 `STORY-001 verified` 建议，并列出验证命令与结果；由 meta-po 继续收敛状态并判断是否允许进入 W0 下一个 Story。

验证不通过时，meta-qa 应报告失败项、严重级别、复现命令和建议路由；不得自行推进 STORY-002。

## 7. 完成记录

`meta-qa` 已完成 STORY-001 正式 8 维度验收，`process/VERIFICATION-REPORT.md` 结论为 PASS，无 BLOCKING 或 REQUIRED 失败项。`meta-po` 已据此将 STORY-001 收敛为 `verified`，并按 W0 依赖分派 STORY-002 进入 LLD 起草。
