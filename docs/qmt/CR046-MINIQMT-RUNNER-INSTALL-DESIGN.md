---
status: "implemented-cp6"
version: "1.1"
change_id: "CR-046"
owner: "host-orchestrator"
real_install_authorized: false
connection_authorized: false
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
cp6_implemented_at: "2026-06-14T00:16:26+08:00"
---

# CR046 MiniQMT Runner 安装设计与运行边界

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | host-orchestrator | 初版 MiniQMT runner 安装设计，冻结 Windows 目录、uv、依赖隔离、配置、日志、kill switch、升级卸载回滚和不授权边界 |
| 1.1 | 2026-06-14 | host-orchestrator | CP6 状态收敛：确认本文作为 MiniQMT runner install design 契约资产实现；真实安装、连接、订阅、查询和交易仍不授权 |

## 目标

本设计冻结 MiniQMT runner 的未来安装与运行边界。CR046 不真实安装、不连接 XtQuant / MiniQMT、不订阅行情、不查询账户、不 submit/cancel。

## 安装目录候选

| 路径对象 | 默认候选 | 说明 |
|---|---|---|
| install_root | `C:\local_backtest\miniqmt_runner\<package_id>` | 后续 CR049 可由用户覆盖 |
| package_root | `<install_root>\packages\<package_id>` | 解压策略包 artifact |
| config_root | `<install_root>\config` | 只放 redacted template 或用户本地私有配置引用 |
| log_root | `<install_root>\logs` | 脱敏日志 |
| evidence_root | `<install_root>\evidence` | 后续 dry-run / readonly 证据 |
| rollback_root | `<install_root>\rollback` | 升级回滚备份 |

## uv 与依赖隔离

| 项目 | 设计 |
|---|---|
| Python 管理 | 使用 uv 管理解释器、虚拟环境和命令入口 |
| 依赖声明 | MiniQMT / XtQuant 依赖只进入 runner target，不进入 Linux 主项目依赖 |
| 禁止事项 | 不使用裸 pip 作为默认入口，不把 xtquant 写入本仓库主依赖，不读取真实 `.env` |
| 后续验证 | CR049 再验证 Windows 端 uv、Python、MiniQMT 权限和只读连接 |

## 配置模板

配置模板只允许出现占位符：

```yaml
package_id: "<package_id>"
target: "miniqmt_runner"
runtime_authorized: false
connection_authorized: false
account_query_authorized: false
submit_cancel_authorized: false
userdata_mini_path: "<USER_LOCAL_PATH_PLACEHOLDER>"
log_root: "<INSTALL_ROOT>\\logs"
kill_switch:
  default_state: "hard_off"
  require_per_run_authorization: true
```

禁止在模板中出现真实账号、token、session、交易密码、cookie、私钥或 broker payload。

## 进程与 kill switch

| 合同 | CR046 设计 |
|---|---|
| start | 只定义未来命令形态，不执行 |
| stop | 只定义未来命令形态，不执行 |
| status | 只定义状态枚举，不查询真实 runtime |
| health | 只定义健康检查字段，不连接 MiniQMT |
| kill_switch | 默认 hard-off；无逐 run 授权时 fail closed |

## 日志与证据

日志只能包含：

- package_id
- run_id
- target
- action
- status
- redacted relative path
- error code

日志不得包含：

- 真实账号
- token / session
- 持仓、资金、委托、成交明细
- 原始 broker payload
- 未脱敏路径中的用户名或敏感目录

## 升级、卸载与回滚

| 动作 | 设计要求 | CR046 状态 |
|---|---|---|
| install dry-run | 检查目录、配置模板、依赖声明、日志目录 | 只定义 |
| upgrade | 先备份旧 package，再替换 artifact | 只定义 |
| uninstall | 删除 package_root，保留审计日志策略 | 只定义 |
| rollback | 从 rollback_root 恢复上一版本 | 只定义 |

## 失败路径

| 触发条件 | 行为 |
|---|---|
| MiniQMT 权限不存在 | fail closed，等待 CR049 |
| 需要真实安装 | 转 runtime_authorization |
| 需要连接 XtQuant | 转 CR049 / runtime_authorization |
| 配置包含真实凭据 | BLOCKED，必须脱敏 |
| kill_switch 非 hard-off | FAIL，回到设计修正 |

## 不授权边界

CR046 不授权真实安装、真实卸载、真实升级、真实回滚、启动 runner、连接 MiniQMT / XtQuant、订阅行情、查询账户、submit/cancel、simulation/live、读取凭据或 `.env`。
