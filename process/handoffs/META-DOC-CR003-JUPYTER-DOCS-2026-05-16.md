---
handoff_id: "META-DOC-CR003-JUPYTER-DOCS-2026-05-16"
from_agent: "meta-po"
to_agent: "meta-doc"
agent_name: "doc-zheng"
workflow_id: "local_backtest"
change_id: "CR-003"
story_id: "documentation"
wave_id: "CR-003"
status: "completed"
created_at: "2026-05-16T19:19:17+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-doc"
  agent_path: ".agents/agents/meta-doc.md"
  tool_name: "spawn_agent"
  agent_id: "019e308b-5947-7611-bffc-15fc60d142b1"
  agent_name: "doc-zheng the 2nd"
  thread_id: "019e308b-5947-7611-bffc-15fc60d142b1"
  spawned_at: "reported-by-main-thread; exact spawn time not provided"
  resumed_at: ""
  completed_at: "2026-05-16T19:33:15+08:00"
  evidence: "主线程真实调度：meta-doc / doc-zheng the 2nd agent_id=019e308b-5947-7611-bffc-15fc60d142b1 tool_name=spawn_agent；完成文档同步：README 本地 Notebook 探索章节、USER-MANUAL 10.1 与故障排查，明确 exploration 依赖、%matplotlib inline、OHLCV/mplfinance 限制、Notebook 不替代正式 PNG 报告。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable_key: "meta-doc|local_backtest|CR-003|documentation|CR-003"
fork_context: false
---

# Handoff：CR-003 Jupyter 探索入口文档同步

## 任务

请以 `meta-doc` 身份在 CR-003 实施后同步 README 与 `docs/USER-MANUAL.md`。目标是让用户知道如何进入本地 Jupyter 探索，同时清楚区分探索 Notebook 与 CR-002 正式 PNG 报告。

## 最小上下文

请读取：

- `process/STATE.md`
- `process/changes/CR-003-JUPYTER-RESEARCH-NOTEBOOKS-2026-05-16.md`
- `process/handoffs/META-DEV-CR003-JUPYTER-IMPLEMENT-2026-05-16.md` 的执行回填
- `notebooks/` 下新增或修改文件
- `pyproject.toml`
- `README.md`
- `docs/USER-MANUAL.md`

不要加载：

- 真实私有数据
- 过程推理草稿
- 无关 Story LLD

## 文档要求

1. README 增加 Jupyter 探索入口：启动命令、Notebook 路径、默认读取 `reports/equity_curve.csv` 的说明。
2. `docs/USER-MANUAL.md` 增加操作细节：`%matplotlib inline`、净值 / 回撤展示、OHLCV + `mplfinance` K 线限制、缺数据时如何处理。
3. 明确 Notebook 只用于探索，不替代正式报告；正式报告仍使用 `generate_report_charts("reports")` 输出 PNG 和索引。
4. 文档示例命令使用 `uv`，不得使用裸 `pip install` 作为默认入口。
5. 不新增 `delivery/**`、安装脚本、真实数据或报告样本。

## 完成输出

请返回修改章节、关键说明和是否存在文档缺口。没有真实平台调度证据前，不得把本 handoff 标记为 completed。

## 执行回填

### 调度证据

| 字段 | 值 |
|---|---|
| 调度方 | 主线程代发 |
| Agent | `meta-doc / doc-zheng the 2nd` |
| agent_id / thread_id | `019e308b-5947-7611-bffc-15fc60d142b1` |
| tool_name | `spawn_agent` |
| completed_at | `2026-05-16T19:33:15+08:00` |

### 执行结论

文档同步完成。README 已补充本地 Notebook 探索章节；`docs/USER-MANUAL.md` 已补充 10.1 与故障排查；文档明确 exploration 依赖、`%matplotlib inline`、OHLCV / `mplfinance` 限制，以及 Notebook 不替代正式 PNG 报告。
