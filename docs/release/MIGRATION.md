---
status: ready
version: "1.0"
release_artifact_profile: compact
release_decision: READY_WITH_RISK
cr_id: CR-044
---

# CR044 Migration

## 1. 迁移结论

| 项目 | 内容 |
|---|---|
| 是否需要迁移 | no |
| 是否自动迁移 | N/A |
| 是否保留兼容路径 | yes |
| 是否可逆 | yes |

## 2. 兼容性判断表

| 对象 | 是否变化 | 兼容性 | 需要迁移 | 验证方式 | 回滚方式 |
|---|---|---|---|---|---|
| `STATE.md` schema | no | compatible | no | CR tracking consistency PASS | 回退 CR044 状态记录 |
| 模板字段 | no | N/A | no | 未修改模板 | N/A |
| 配置格式 | yes | compatible | no | `.gitignore` 反忽略 `docs/quality/*.md` | 删除新增反忽略规则 |
| 安装路径 | no | N/A | no | 未修改安装器 | N/A |
| Agent frontmatter | no | N/A | no | 未修改 Agent | N/A |
| Skill 输出格式 | no | N/A | no | 未修改 Skill | N/A |
| 命令参数 | no | N/A | no | pytest 命令保持 uv / Python 3.11 | N/A |
| 数据存储结构 | no | N/A | no | 未写 lake / data / catalog | N/A |

## 3. 迁移步骤

| Step | 操作 | 前置条件 | 验证 | 回退 |
|---|---|---|---|---|
| 1 | N/A：无状态、数据或安装迁移 | CP8 approved | `uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` | N/A |

## 4. N/A 说明

| 项目 | 原因 | 后续触发条件 |
|---|---|---|
| 数据迁移 | CR044 不写数据湖、不写 catalog、不接真实 broker | 若未来 L4/L5 真实运行产生 artifact/schema，再新增迁移设计 |
| 安装迁移 | 未修改安装脚本或平台安装路径 | 若后续把 Goldminer admission guard 打包到交付安装器，再进入 release full profile |
| Runtime 配置迁移 | 未读取或写入 `.env`、凭据、账户配置 | L3+ 凭据准入 CR 启动时重新设计 |
