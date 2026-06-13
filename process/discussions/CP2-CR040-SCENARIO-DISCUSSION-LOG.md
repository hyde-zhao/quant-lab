---
cr_id: CR-040
discussion_id: CP2-CR040-SCENARIO-DISCUSSION
status: ready-for-review
owner: meta-po
created_at: 2026-06-10T22:45:00+08:00
---

# CP2 CR040 场景讨论日志

## 背景

用户确认无法获取 MiniQMT 权限，并要求删除 QMT 相关 CR，不再推进 QMT / MiniQMT / XtQuant 路线。CR040 承接该决策，目标是关闭旧路线、保留审计证据，并规划本地 paper simulation 与后续掘金量化 adapter 候选路线。

## Scenario Gray Areas

| 问题 ID | 问题 | 推荐方案 | 备选方案 | 当前分类 | 影响 |
|---|---|---|---|---|---|
| SGQ-CR040-01 | 删除 QMT 路线后，是否物理删除历史文件？ | 不物理删除，只标记 deleted / cancelled 并保留证据 | 物理删除历史文件；或只在 README 标记废弃 | resolved-by-user | 推荐方案保留审计链，避免丢失历史 CP 证据。 |
| SGQ-CR040-02 | 本地模拟盘是否应直接作为 CR040 实现？ | 否；CR040 只做路线变更，代码实现拆为 CR041 | 在 CR040 中直接实现 paper simulation | decision-item | 拆分后门禁清晰，避免一边删 QMT 一边新增执行引擎。 |
| SGQ-CR040-03 | 掘金量化接口是否现在接入？ | 否；仅作为 CR043 Spike 候选 | 立即安装 SDK 并验证 | decision-item | 当前不具备账号、终端、凭据与运行授权边界。 |

## 用户可见确认口径

用户回复 `approve` 表示接受：

1. CR040 只确认 QMT 路线删除与新路线规划，不授权真实运行。
2. 后续代码实现优先另起 CR041 API-less Paper Simulation Runner。
3. 掘金量化只进入后续 Spike 候选，不安装、不登录、不连接、不查询账户、不下单。

## 不授权项

| 不授权项 | 状态 |
|---|---|
| QMT / MiniQMT / XtQuant 连接 | not-authorized |
| Backtrader 安装或运行 | not-authorized |
| 掘金量化 SDK 安装、登录或连接 | not-authorized |
| 账户、持仓、委托、成交查询 | not-authorized |
| 下单、撤单、simulation/live 运行 | not-authorized |
| 凭据、token、cookie、session 读取 | not-authorized |
