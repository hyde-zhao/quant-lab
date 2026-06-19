---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-099
---

# CR099 Migration

## 1. 迁移结论

| 项目 | 内容 |
|---|---|
| 是否需要迁移 | no |
| 是否自动迁移 | N/A |
| 是否保留兼容路径 | yes，CR098 offline runner integration 仍保留 |
| 是否可逆 | yes，文件级回滚即可 |

## 2. 兼容性判断表

| 对象 | 是否变化 | 兼容性 | 需要迁移 | 验证方式 | 回滚方式 |
|---|---|---|---|---|---|
| `STATE.md` schema | no | compatible | no | workspace check / cr-tracking | 回退 CR099 状态条目 |
| 模板字段 | yes | compatible | no | CR099 checker / tests | 回滚 checker / collector |
| 配置格式 | no | N/A | no | 文件范围审查 | N/A |
| 安装路径 | no | N/A | no | deploy checklist | N/A |
| Agent frontmatter | no | N/A | no | 文件范围审查 | N/A |
| Skill 输出格式 | no | N/A | no | 文件范围审查 | N/A |
| 命令参数 | yes | compatible | no | collector requires explicit parameters | 回滚 collector |
| 数据存储结构 | no | N/A | no | 文件范围审查 | N/A |

## 3. 迁移步骤

| Step | 操作 | 前置条件 | 验证 | 回退 |
|---|---|---|---|---|
| 1 | N/A | 本轮无状态 schema、配置、安装路径或数据迁移 | N/A | N/A |

## 4. N/A 说明

| 项目 | 原因 | 后续触发条件 |
|---|---|---|
| runtime migration | CR099 不安装 / 修改 Windows gateway；只消费用户已启动 gateway | 用户要求 gateway deployment / service install |
| NAS migration | 当前 CR099 不需要 NAS | 用户启动 NAS package exchange gate |
| credential / account migration | 未存储 Windows `.env`、账号或原始持仓 | 用户启动安全 / runtime evidence gate |
| data lake / publish migration | 未执行 provider fetch / lake write / catalog publish | 用户启动数据发布 gate |

## CR100 Addendum - Migration

| 对象 | 是否变化 | 兼容性 | 需要迁移 | 验证方式 | 回滚方式 |
|---|---|---|---|---|---|
| `STATE.md` schema | no | compatible | no | cr-tracking check | 回退 CR100 状态条目 |
| package manifest schema | yes，新建 `cr100-strategy-package-manifest-v1` | additive | no | CR100 pytest | 删除 CR100 新增 schema/代码 |
| 命令参数 | yes，新 CLI | additive | no | CLI/AST/pytest | 删除 `scripts/cr100_package_exchange.py` |
| 数据存储 | local fake exchange/cache only | compatible | no | tmp_path fixture | 删除本地 fake fixture |
| 真实 NAS | no | N/A | no | 未授权未执行 | N/A |
