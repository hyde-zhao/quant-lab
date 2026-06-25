---
status: ready-for-review
cr_id: CR-095
---

# CR095 Migration

| 项目 | 结论 | 说明 |
|---|---|---|
| 数据迁移 | N/A | 不读写数据 |
| 配置迁移 | N/A | 不改配置、环境变量或凭据 |
| 命令参数 | N/A | standalone checker 参数不变 |
| 输出格式 | 兼容新增 | 新增 summary 前缀行；最终 PASS/FAIL 行和退出码不变 |
| 安装路径 | N/A | 不改安装器或平台路径 |

## 兼容性说明

调用方若只依赖退出码不受影响；若解析 stdout 第一行，需要适配新增的 `CR tracking summary` 多行摘要。
