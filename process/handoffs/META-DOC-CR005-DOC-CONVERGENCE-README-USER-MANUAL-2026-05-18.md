---
handoff_id: "META-DOC-CR005-DOC-CONVERGENCE-README-USER-MANUAL-2026-05-18"
project_id: "local_backtest"
workflow_id: "local_backtest"
change_id: "CR-005"
created_at: "2026-05-18T06:45:33+08:00"
created_by: "meta-po"
from_agent: "meta-po"
to_agent: "meta-doc"
scope: "CR-005 documentation convergence for Tushare .env, external lake root, NAS SMB mount boundary, and postponed real-data test gate"
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
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-doc"
  agent_path: ""
  tool_name: "spawn_agent"
  agent_id: "019e3821-8a84-70e1-bd91-02d645525d11"
  agent_name: "doc-yan"
  thread_id: "019e3821-8a84-70e1-bd91-02d645525d11"
  spawned_at: "2026-05-18T06:51:44+08:00"
  resumed_at: ""
  completed_at: "2026-05-18T06:51:44+08:00"
  evidence: "主线程真实 spawn_agent 调度 meta-doc/doc-yan；agent_id/thread_id=019e3821-8a84-70e1-bd91-02d645525d11；完成后已关闭。spawn output 未提供精确 spawned_at，使用 completed_at 作为追溯记录时间。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
  note: "meta-doc 已通过 Codex 子 agent 完成文档收敛；未修改代码、测试、Story、检查点或 delivery。"
completion:
  completed_at: "2026-05-18T06:51:44+08:00"
  completed_by: "meta-doc"
  modified_files:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "process/handoffs/META-DOC-CR005-DOC-CONVERGENCE-README-USER-MANUAL-2026-05-18.md"
  documentation_sections:
    - "README.md#Tushare 真实回补与本地 comparison"
    - "docs/USER-MANUAL.md#4.4 Tushare hs300_index 显式回补 runbook"
  confirmations:
    credentials_written: false
    real_data_written: false
    code_modified: false
    tests_modified: false
    delivery_modified: false
    story_status_reopened: false
---

# Meta-doc Handoff: CR-005 文档收敛

## 1. 任务目标

请 `meta-doc` 只更新正式用户文档：

- `README.md`
- `docs/USER-MANUAL.md`

本轮文档收敛只吸收用户新增运维决策，不修改业务代码、测试、Story、LLD、检查点或 `delivery/**`。

用户已决定：

- 使用本地 `.env` 配置 `TUSHARE_TOKEN`。
- 使用本地 `.env` 配置 `MARKET_DATA_LAKE_ROOT=/mnt/nas/local_backtest_lake`。
- NAS SMB 共享路径为 `\\192.168.101.83\data_lake`。
- NAS 需要用户名和密码登录。
- 用户明确说：`data_lake` 挂载完成后再通知进入下一步实测。

## 2. 当前文档缺口

meta-po 已读取 `README.md`、`docs/USER-MANUAL.md`、`process/STATE.md`、`process/STORY-STATUS.md` 和 `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`。当前缺口如下：

| 缺口 | 当前事实 | 需要收敛 |
|---|---|---|
| `.env` 配置入口 | README / USER-MANUAL 只说明 `TUSHARE_TOKEN` 与 `MARKET_DATA_LAKE_ROOT` 来自环境变量；`.gitignore` 已忽略 `.env` / `.env.*`。 | 文档应新增本地 `.env` 示例，但只能写变量名和占位符，不写真实 token。 |
| 固定 lake root | 当前示例仍使用 `/abs/path/to/external/market_data_lake`。 | 改为或补充用户确认的 `/mnt/nas/local_backtest_lake`。 |
| NAS SMB 挂载边界 | 当前文档未写 `\\192.168.101.83\data_lake` 与本地挂载目标关系。 | 说明 SMB 共享需先由用户在系统层挂载到 `/mnt/nas/local_backtest_lake`，再进入 dry-run / 实测。 |
| 凭据安全 | 当前文档强调 token 不入库，但没有覆盖 NAS 用户名/密码。 | 明确不得把 NAS 用户名、密码、token 写入 README、手册、`.env.example`、日志、manifest、quality、catalog、测试 fixture 或对话。 |
| 暂停门控 | 当前 runbook 给出了 dry-run 和真实执行示例。 | 在文档中标注：本轮不执行真实 Tushare fetch、不真实写 lake；必须等用户确认 NAS 挂载完成后，下一轮再从 dry-run 开始。 |
| `.env` 加载方式 | 当前实现读取 shell 环境变量；未发现应用自动加载 `.env` 的依赖或说明。 | 文档应说明 `.env` 是本地 shell 配置源，运行命令前需显式加载到环境变量，例如 `set -a; . ./.env; set +a`；不要声称程序自动读取 `.env`，除非后续代码另行实现并验证。 |

## 3. 最小必要上下文

meta-doc 应读取：

- `README.md`
- `docs/USER-MANUAL.md`
- `process/STATE.md`
- `process/STORY-STATUS.md`
- `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
- `.gitignore`
- 必要时读取 `market_data/cli.py` 中 `TUSHARE_TOKEN` / `MARKET_DATA_LAKE_ROOT` 的环境变量解析事实。

不应默认加载：

- 完整历史会话 transcript。
- 全量 Story LLD。
- 与 CR-005 文档收敛无关的历史失败草稿。
- 任何真实 token、NAS 用户名、NAS 密码或真实 lake 数据。

## 4. 文档更新范围

### README.md

建议在 `Tushare 真实回补与本地 comparison` 附近增量补充：

1. 本地 `.env` 示例：

   ```bash
   TUSHARE_TOKEN=<由用户本机填写，不提交>
   MARKET_DATA_LAKE_ROOT=/mnt/nas/local_backtest_lake
   ```

2. `.env` 安全边界：
   - `.env` / `.env.*` 已由 `.gitignore` 忽略。
   - 不创建包含真实值的 `.env.example`。
   - 不把 token、NAS 用户名或 NAS 密码写入文档、日志、manifest、quality、catalog 或测试 fixture。

3. NAS 挂载边界：
   - SMB 共享：`\\192.168.101.83\data_lake`。
   - 本地挂载目标：`/mnt/nas/local_backtest_lake`。
   - NAS 凭据由用户在系统层或凭据管理器中处理；文档不要求用户提供给 agent。

4. 暂停门控：
   - 在用户确认 `data_lake` 已挂载前，不执行真实 Tushare fetch，不写真实 lake。
   - 下一步应先做 dry-run / path preflight，再由用户显式授权真实执行。

### docs/USER-MANUAL.md

建议在 `4.4 Tushare hs300_index 显式回补 runbook` 中增量补充：

1. “准备本地环境变量”小节。
2. “挂载 NAS 数据湖”小节，只说明共享路径、本地挂载目标和凭据不得入文档；不要写具体用户名、密码或可直接含密命令。
3. 将示例 lake root 从泛化占位补充为 `/mnt/nas/local_backtest_lake`。
4. 标明当前阶段只允许说明与静态检查；用户通知挂载完成后才进入下一轮 dry-run / 实测。
5. 保留现有 no-network / no-token / no-auto-backfill / Backtrader optional backend 边界。

## 5. 禁止事项

meta-doc 不得：

- 写入或要求用户提供真实 `TUSHARE_TOKEN`。
- 写入或要求用户提供 NAS 用户名、密码。
- 执行真实 Tushare fetch。
- 执行真实 lake 写入。
- 读取 `/mnt/nas/local_backtest_lake` 的真实数据内容。
- 新增、删除或修改 `delivery/**`。
- 修改业务代码、测试、依赖锁、Story 卡片、LLD、CP5/CP6/CP7 结论。
- 把 CR005-S01..S06 从 `verified` 改回其它状态。
- 声称 NAS 已挂载、真实数据已抓取或真实 lake 已验证，除非用户后续明确通知并由 QA 实测验证。

## 6. 输出要求

meta-doc 完成后应回报：

- 修改的文档路径。
- 新增或调整的章节标题。
- 是否只涉及 README / USER-MANUAL。
- 是否确认未写入 token、NAS 用户名、NAS 密码、真实数据或 `delivery/**`。

## 7. 复用键与关闭条件

复用键：

- role: `meta-doc`
- workflow_id: `local_backtest`
- change_id: `CR-005`
- story_id: `documentation-convergence`
- wave_id: `CR005-docs`

关闭条件：

- `README.md` 与 `docs/USER-MANUAL.md` 已按上述范围收敛。
- meta-doc 明确没有修改代码、测试、Story 状态、真实数据、凭据或 `delivery/**`。
- meta-po 可据此调度 meta-qa 做后置静态复核。
