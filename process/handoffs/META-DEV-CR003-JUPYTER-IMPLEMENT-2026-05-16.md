---
handoff_id: "META-DEV-CR003-JUPYTER-IMPLEMENT-2026-05-16"
from_agent: "meta-po"
to_agent: "meta-dev"
agent_name: "dev-zhao"
workflow_id: "local_backtest"
change_id: "CR-003"
story_id: "STORY-006+STORY-007"
wave_id: "CR-003"
status: "completed"
created_at: "2026-05-16T19:19:17+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e3086-fb15-7142-b839-b72cade549e2"
  agent_name: "dev-qian the 2nd"
  thread_id: "019e3086-fb15-7142-b839-b72cade549e2"
  spawned_at: "reported-by-main-thread; exact spawn time not provided"
  resumed_at: ""
  completed_at: "2026-05-16T19:33:15+08:00"
  evidence: "主线程真实调度：meta-dev / dev-qian the 2nd agent_id=019e3086-fb15-7142-b839-b72cade549e2 tool_name=spawn_agent；完成实现：pyproject.toml/uv.lock 新增 exploration 组（jupyter/ipykernel/mplfinance）、.gitignore、notebooks/local_research_intro.ipynb、notebooks/README.md、README.md、docs/USER-MANUAL.md、process/checks/CP6-CR003-JUPYTER-NOTEBOOKS.md、DEV-LOG.md；验证 uv add/sync 成功，pytest 12 passed，Notebook JSON/import/code boundary ok，generate_report_charts artifact_count=4。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
reusable_key: "meta-dev|local_backtest|CR-003|STORY-006+STORY-007|CR-003"
fork_context: false
---

# Handoff：CR-003 Jupyter 探索入口实现

## 任务

请以 `meta-dev` 身份实现 CR-003 的最小范围：为本地探索型研究提供 Jupyter / Notebook 入口、依赖和必要轻量支持，同时保持 CR-002 的正式报告 PNG 脚本化保存能力不变。

## 最小上下文

请读取：

- `process/STATE.md`
- `process/changes/CR-003-JUPYTER-RESEARCH-NOTEBOOKS-2026-05-16.md`
- `process/handoffs/META-SE-CR003-JUPYTER-BOUNDARY-REVIEW-2026-05-16.md` 的执行回填（若主线程已完成代发）
- `process/changes/CR-002-REPORT-CHARTS-2026-05-16.md`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `docs/USER-MANUAL.md`
- `engine/charts.py`
- `tests/test_story_004_013.py`
- `reports/equity_curve.csv`

不要加载：

- 真实私有行情数据
- 全量 `process/stories/` 和历史失败轮次
- 无关外部知识库内容

## 实施边界

必须：

1. 使用 `uv` 管理依赖。若新增依赖，优先通过 `uv add` 或 `uv add --dev` 更新 `pyproject.toml` 和 `uv.lock`。
2. 新增 `notebooks/` 下的探索入口。可以是 `.ipynb` 示例，也可以同时提供 `notebooks/README.md` bootstrap。
3. Notebook 示例默认使用 `%matplotlib inline`，读取 `reports/equity_curve.csv` 展示净值和回撤。
4. 若加入 `mplfinance` 示例，必须只在 OHLCV 数据列存在时绘制 K 线；无 OHLCV 时给出清晰提示，不生成伪造 K 线。
5. Notebook 默认不调用 `savefig`，不向 `reports/charts/` 或其他目录保存探索图片。
6. 如需要，补充 `.gitignore` 对 `.ipynb_checkpoints/` 或 notebook 临时输出的忽略。
7. 保持 `engine.charts.generate_report_charts("reports")` 的 CR-002 行为不变。

禁止：

1. 不删除或降级 `engine/charts.py`、`reports/charts/index.md` 或 PNG 保存能力。
2. 不把 Notebook 当正式报告替代物。
3. 不引入联网下载、远程 Notebook 服务、真实私有数据、凭据或自动上传。
4. 不改回测、扫描、指标或数据准备计算口径。

## 建议验证

- `uv sync`
- `uv run --python 3.11 pytest -q`
- 如依赖允许，可用 `uv run --python 3.11 python - <<'PY'` 轻量检查 `import mplfinance`、`import matplotlib`。
- 可额外检查 notebook JSON 有效性，但不要执行真实私有数据。

## 完成输出

请返回：

1. 修改文件列表。
2. 依赖变更说明。
3. Notebook 使用说明摘要。
4. 已运行命令和结果。
5. 明确说明 CR-002 PNG 报告能力未破坏。

没有真实平台调度证据前，不得把本 handoff 标记为 completed。

## 执行回填

### 调度证据

| 字段 | 值 |
|---|---|
| 调度方 | 主线程代发 |
| Agent | `meta-dev / dev-qian the 2nd` |
| agent_id / thread_id | `019e3086-fb15-7142-b839-b72cade549e2` |
| tool_name | `spawn_agent` |
| completed_at | `2026-05-16T19:33:15+08:00` |

### 执行结论

实现完成。修改范围：

- `pyproject.toml` / `uv.lock`：新增 exploration 组，包含 Jupyter / ipykernel / mplfinance。
- `.gitignore`：覆盖 Notebook checkpoint / outputs / tmp。
- `notebooks/local_research_intro.ipynb`、`notebooks/README.md`：新增本地探索入口。
- `README.md`、`docs/USER-MANUAL.md`：新增 Jupyter 研究入口与正式 PNG 报告边界说明。
- `process/checks/CP6-CR003-JUPYTER-NOTEBOOKS.md`、`DEV-LOG.md`：记录编码与验证证据。

验证结果：`uv add/sync` 成功，`pytest` 12 passed，Notebook JSON / import / code boundary ok，`generate_report_charts("reports")` 回归 `artifact_count=4`。
