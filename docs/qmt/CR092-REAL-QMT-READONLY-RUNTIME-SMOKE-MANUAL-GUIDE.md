---
status: "implemented"
version: "1.0"
source_cr: "CR-092"
owner: "host-orchestrator"
created_at: "2026-06-18T16:55:00+08:00"
runtime_authorized: false
nas_authorized: false
credential_read_authorized: false
real_account_read_authorized: false
trade_write_authorized: false
---

# CR092 Real QMT Readonly Runtime Smoke Manual Guide

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-18 | host-orchestrator | 初始 manual guide，只定义模拟账户 evidence 准备和静态校验，不授权运行。 |

## 1. 使用边界

本 guide 只用于 CR092 的 CP6 静态实现切片。它不授权任何真实运行。

允许：

- 用户明确提供模拟账户测试 evidence 文件路径或粘贴内容。
- Codex 读取该明确提供的单个 evidence 文件或内容。
- 运行本地静态 checker 校验 evidence 结构和敏感字段边界。

禁止：

- 启动、连接、安装或运行 QMT / MiniQMT / XtQuant / gateway / runner。
- 访问、列取、读取、复制、拉取、写入、发布或删除 NAS。
- 读取 `.env`、凭据、token、真实账号、真实账户、真实资金 / 持仓 / 委托 / 成交或未指定日志原文。
- submit / cancel、buy / sell。
- simulation / live。
- provider fetch、lake write、catalog publish。
- 自动启动 CR089 或恢复 CR020 gateway 路线。

## 2. Evidence 准备

使用模板：

- `docs/qmt/CR092-REAL-QMT-READONLY-RUNTIME-SMOKE-EVIDENCE-TEMPLATE.yaml`

必要条件：

- `account_mode` 必须为 `simulated`。
- `scope` 只能包含 `health`、`capabilities`、`query_positions_readonly`。
- `forbidden_counters` 中所有计数必须为 `0`。
- 不得包含凭据、真实账户、NAS 路径、submit/cancel、simulation/live 或 provider/lake/publish 信号。

## 3. 静态校验

命令格式：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/check_cr092_simulated_evidence.py --evidence <明确提供的模拟账户 evidence 文件> --json
```

该命令只读取 `--evidence` 指定的单个文件。不要把目录、NAS 路径、`.env`、真实账户日志或未脱敏日志传给该命令。

## 4. 结果处理

| checker 结果 | 处理 |
|---|---|
| `passed=true` | 可作为后续 CP7 evidence review 的输入。 |
| `passed=false` 且错误为结构缺失 | 修正 evidence 字段后重试。 |
| `passed=false` 且错误涉及凭据 / 真实账户 / NAS / live / order-write | 停止读取，重新脱敏或转入对应安全 / follow-up gate。 |

## 5. 不构成授权

本 guide、模板和 checker 的存在不代表：

- QMT / MiniQMT / XtQuant / gateway / runner 可运行。
- 当前机器可连接交易环境。
- 可以读取真实账户。
- 可以访问 NAS。
- 可以发单、撤单、simulation 或 live。
