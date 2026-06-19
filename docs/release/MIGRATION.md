---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-092
---

# CR092 Migration

## 1. 迁移结论

| 项目 | 内容 |
|---|---|
| 是否需要迁移 | no |
| 是否自动迁移 | N/A |
| 是否保留兼容路径 | N/A |
| 是否可逆 | yes，文件级回滚即可 |

## 2. 兼容性判断表

| 对象 | 是否变化 | 兼容性 | 需要迁移 | 验证方式 | 回滚方式 |
|---|---|---|---|---|---|
| `STATE.md` schema | no | compatible | no | workspace check / manual review | 回退 CR092 状态条目 |
| 模板字段 | yes | compatible | no | checker self-check / tests | 回滚 evidence template |
| 配置格式 | no | N/A | no | 文件范围审查 | N/A |
| 安装路径 | no | N/A | no | deploy checklist | N/A |
| Agent frontmatter | no | N/A | no | 文件范围审查 | N/A |
| Skill 输出格式 | no | N/A | no | 文件范围审查 | N/A |
| 命令参数 | yes | compatible | no | `--evidence <file>` required by checker tests | 回滚 checker |
| 数据存储结构 | no | N/A | no | 文件范围审查 | N/A |

## 3. 迁移步骤

| Step | 操作 | 前置条件 | 验证 | 回退 |
|---|---|---|---|---|
| 1 | N/A | 本轮无状态 schema、配置、安装路径或数据迁移 | N/A | N/A |

## 4. N/A 说明

| 项目 | 原因 | 后续触发条件 |
|---|---|---|
| runtime migration | 未启用 QMT / MiniQMT / XtQuant / gateway / runner runtime | 用户批准真实 runtime smoke |
| NAS migration | 当前 CR092 不需要 NAS | 用户启动 CR091-FU-02 |
| credential / account migration | 未读取或存储凭据 / 真实账户 | 用户启动安全 / runtime evidence gate |
| data lake / publish migration | 未执行 provider fetch / lake write / catalog publish | 用户启动数据发布 gate |
