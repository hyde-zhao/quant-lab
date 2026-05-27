---
handoff_id: "META-QA-CR005-TUSHARE-BACKTRADER-QUALITY-2026-05-17"
from_agent: "meta-po"
to_agent: "meta-qa"
status: "completed"
created_at: "2026-05-17T16:56:29+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
story_id: "CR005-QUALITY-REVIEW"
wave_id: "CR005-SOLUTION-DESIGN"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e352c-45e1-7602-bce5-7fff71c1d1b0"
  agent_name: "qa-lv"
  thread_id: "019e352c-45e1-7602-bce5-7fff71c1d1b0"
  spawned_at: "2026-05-17T17:17:29+08:00"
  resumed_at: ""
  completed_at: "2026-05-17T17:17:29+08:00"
  evidence: "用户回报主线程已通过 spawn_agent 真实并行调度 meta-qa；agent_id=019e352c-45e1-7602-bce5-7fff71c1d1b0，nickname=qa-lv，状态 completed。meta-qa 已完成 CR-005 质量评审，更新 process/TEST-STRATEGY.md 并新增 process/checks/QA-CR005-QUALITY-REVIEW.md；验证命令 UV_CACHE_DIR=/tmp/uv-cache-local-backtest TUSHARE_TOKEN= uv run --python 3.11 pytest -q，结果 56 passed in 4.12s；review artifact 校验 OK。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Handoff：CR-005 质量门、离线默认与安全评审

## 任务

请以 `meta-qa` 身份并行评审 CR-005 的质量策略，不实现代码。

必须覆盖：

1. 默认离线：`uv run --python 3.11 pytest -q` 不需要 `TUSHARE_TOKEN`、不联网、不安装 Backtrader optional 依赖也能通过默认路径。
2. 凭据安全：Tushare token 只能来自环境变量引用，不得进入 manifest、quality、catalog、日志、错误消息、测试 fixture 或文档示例值。
3. 数据质量：Tushare fetch status 与本地 dataset status 必须分离；本地 canonical/gold 合规时不得因远端失败直接阻断只读回测。
4. Backtrader optional backend：未安装时必须结构化降级；启用时只读本地 canonical/gold，不直接联网、不读取 Tushare token、不绕过 quality gate。
5. 回归范围：列出 CP3/CP4 后进入 CP5 前应要求 meta-dev 覆盖的最小测试集、离线负向测试、凭据泄漏扫描和依赖组策略。

## 最小上下文

- `process/STATE.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- 代码事实：
  - `market_data/connectors/tushare.py`
  - `market_data/config.py`
  - `market_data/source_registry.py`
  - `market_data/readers.py`
  - `market_data/validation.py`
  - `engine/backtest.py`
  - `engine/data_loader.py`
  - `pyproject.toml`

## 禁止事项

- 不得执行真实联网测试。
- 不得要求提交 token 或真实行情数据。
- 不得将 Backtrader 变成默认必装依赖。
- 不得生成 CP7；当前仍处于方案 / 计划门控前。

## 完成后回填

主线程通过 `spawn_agent` 调度后，请回填本文件 frontmatter `dispatch.tool_name`、`agent_id`、`agent_name`、`spawned_at`、`completed_at` 和结果摘要，并同步 `process/STATE.md.agent_lifecycle.active_agents`。
