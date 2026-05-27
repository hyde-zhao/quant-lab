---
handoff_id: "META-DOC-CR005-POST-REAL-DATA-DOC-SYNC-2026-05-18"
project_id: "local_backtest"
workflow_id: "local_backtest"
change_id: "CR-005"
created_at: "2026-05-18T20:15:21+08:00"
created_by: "meta-po"
from_agent: "meta-po"
to_agent: "meta-doc"
scope: "CR-005 post-real-data documentation sync for README.md and docs/USER-MANUAL.md"
status: "completed"
priority: "REQUIRED"
delivery_write_allowed: false
documentation_write_allowed: true
authorized_output_paths:
  - "README.md"
  - "docs/USER-MANUAL.md"
implementation_allowed: false
story_reopen_allowed: false
real_fetch_allowed: false
real_lake_write_allowed: false
credential_collection_allowed: false
data_generation_allowed: false
install_script_generation_allowed: false
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-doc"
  agent_path: ""
  tool_name: "spawn_agent"
  agent_id: "019e3b08-b8cc-7532-8fae-8f5d8fef2162"
  agent_name: "doc-cao"
  thread_id: "019e3b08-b8cc-7532-8fae-8f5d8fef2162"
  spawned_at: "2026-05-18T20:15:21+08:00"
  resumed_at: ""
  completed_at: "2026-05-18T20:22:31+08:00"
  evidence: "主线程通过 Codex spawn_agent 启动 meta-doc；用户在对话中补充真实调度证据 agent_id/thread_id=019e3b08-b8cc-7532-8fae-8f5d8fef2162，nickname=doc-cao。本轮只更新 README.md、docs/USER-MANUAL.md、handoff dispatch/completion 证据和 process/STATE.md 对应文档同步状态；未执行 dry-run、真实 fetch、normalize、validate、read，未读取或写入 lake 数据。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
completion:
  result: "PASS"
  completed_by: "meta-doc"
  nickname: "doc-cao"
  completed_at: "2026-05-18T20:22:31+08:00"
  modified_files:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "process/handoffs/META-DOC-CR005-POST-REAL-DATA-DOC-SYNC-2026-05-18.md"
    - "process/STATE.md"
  confirmations:
    dry_run_executed: false
    real_fetch_executed: false
    normalize_validate_read_executed: false
    lake_read_or_write_executed: false
    env_file_echoed_or_copied: false
    token_or_nas_credentials_written: false
    full_backfill_authorized: false
---

# Meta-doc Handoff: CR-005 真实小窗口通过后的文档同步

## 1. 任务目标

请 `meta-doc` 只同步正式用户文档：

- `README.md`
- `docs/USER-MANUAL.md`

本轮只吸收 `2026-05-18T20:01:26+08:00` 之后已确认的 CR-005 最新事实，不修改业务代码、测试、依赖锁、Story、LLD、检查点、真实 lake 数据或 `delivery/**`。

## 2. 必须同步的当前事实

| 事实 | 文档要求 |
|---|---|
| CR-005 小窗口真实 Tushare 链路已 PASS。 | 将“挂载完成前暂停实测 / 下一步才 dry-run”的旧口径更新为：已按小窗口完成 preflight、dry-run、真实 fetch/write、normalize、quality、catalog、reader 最小链路。 |
| 正式依赖入口已落地。 | 写明 `pyproject.toml` / `uv.lock` 已包含正式 dependency group：`tushare==1.4.29`；正式入口使用 `uv run --env-file .env --group tushare --python 3.11 ...`。 |
| `hs300_index` CLI 已补齐。 | 写明 `python -m market_data.cli normalize --dataset hs300_index`、`validate --dataset hs300_index`、`read --dataset hs300_index` 已支持。 |
| 未显式传 `--lake-root` 时的路径口径已改变。 | 写明 `normalize` / `validate` / `read` 未显式传 `--lake-root` 时优先使用 `.env` 中的 `MARKET_DATA_LAKE_ROOT`，与 `hs300-backfill` 保持一致。 |
| 仓库内误写产物已清理且未重新生成。 | 写明复验后 `data/market_data` 不存在；真实 lake root 仍应是外置路径，不应把真实数据写回仓库默认目录。 |
| 更大窗口或全量回补仍未授权。 | 保留强门控：超过本次 `2024-01-02` 至 `2024-01-05` 小窗口的更大窗口、2015-2025 长区间或全量回补，必须用户显式授权；不得把本次 PASS 扩大解释为全量回补已完成或已授权。 |

## 3. 最小必要上下文

`meta-doc` 应读取：

- `README.md`
- `docs/USER-MANUAL.md`
- `process/STATE.md`
- `process/checks/CR005-REAL-DATA-ACQUISITION-VALIDATION-2026-05-18.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `pyproject.toml`
- 必要时读取 `market_data/cli.py` 中 `MARKET_DATA_LAKE_ROOT` / `--lake-root` 的解析事实。

不应加载：

- 完整历史会话 transcript。
- 全量 Story LLD。
- 真实 `.env` 内容、真实 token、NAS 用户名、NAS 密码。
- `/mnt/nas/local_backtest_lake` 或其他 lake root 下的真实数据内容。

## 4. 建议文档调整点

### README.md

在 `Tushare 真实回补与本地 comparison` 附近：

1. 将旧的“挂载完成前不实测 / 下一步 dry-run”改为“CR-005 已完成小窗口真实链路验证”。
2. 将示例命令统一改为正式依赖入口：

   ```bash
   uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli hs300-backfill ...
   uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli normalize --dataset hs300_index ...
   uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli validate --dataset hs300_index ...
   uv run --env-file .env --group tushare --python 3.11 python -m market_data.cli read --dataset hs300_index ...
   ```

3. 保留 `.env` 和凭据禁写边界，但不要再声称当前尚未进入真实小窗口验证。
4. 写明 `data/market_data` 未重新生成。
5. 写明更大窗口和全量回补必须单独获得用户显式授权。

### docs/USER-MANUAL.md

在 `4.4 Tushare hs300_index 显式回补 runbook` 中：

1. 增加或更新“当前验证状态”小节，记录小窗口 PASS 和 CLI REQUIRED 已关闭。
2. 将 dry-run / 真实执行 / normalize / validate / read 示例统一补上 `--group tushare`。
3. 写明 CLI 的 `normalize` / `validate` / `read` 可使用 `dataset=hs300_index`。
4. 写明未传 `--lake-root` 时优先取 `.env` 的 `MARKET_DATA_LAKE_ROOT`。
5. 保留全量回补禁令：只允许在用户显式授权后扩大窗口，不允许自动执行 2015-2025 或全量数据回补。

## 5. 禁止事项

`meta-doc` 不得：

- 执行真实 Tushare fetch。
- 执行 dry-run、normalize、validate、read 或任何 lake 读写命令。
- 读取或输出真实 `.env`、`TUSHARE_TOKEN`、NAS 用户名、NAS 密码。
- 读取、列出或写入真实 lake 数据。
- 修改业务代码、测试、依赖锁、Story、LLD、检查点或 `delivery/**`。
- 声称更大窗口、2015-2025 长区间或全量回补已完成或已授权。

## 6. 输出要求

完成后请回报：

- 修改的文件路径。
- 更新的章节标题。
- 是否确认未执行真实 fetch / lake 读写。
- 是否确认未写入 token、NAS 凭据、真实 lake 路径值或真实数据。
- 是否确认没有扩大授权到更大窗口或全量回补。

## 7. 复用键与关闭条件

复用键：

- role: `meta-doc`
- workflow_id: `local_backtest`
- change_id: `CR-005`
- story_id: `documentation-post-real-data`
- wave_id: `CR005-post-real-data-docs`

关闭条件：

- `README.md` 与 `docs/USER-MANUAL.md` 已按上述范围收敛。
- handoff frontmatter 已回填真实 Codex `spawn_agent` / `resume_agent` / `send_input` 证据。
- meta-po 随后调度 `meta-qa` 做最终静态复核。
