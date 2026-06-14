---
discussion_id: "CP3-CR053-HLD-DISCUSSION"
change_id: "CR-053"
status: "ready-for-cp3-review"
owner: "host-orchestrator"
created_at: "2026-06-14T10:02:00+08:00"
---

# CP3 CR053 HLD Discussion Log

## 用户新增输入

用户要求：可以不扫描 NAS，但必须给出 NAS 目录使用方案、数据传输方案、目录映射、数据是否备份以及备份方案。

## Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| 逻辑 root + manifest-first transfer + cold backup | 不扫描 NAS 也能设计；权限最小；后续可验证 | 当前不能证明真实目录存在 | NAS / 传输 / 备份 / 安全 / CR058 | 推荐 | 后续 CR058/CR060 可绑定真实路径 |
| 立即 NAS read-only inventory | 真实度高 | 需要授权，可能触碰大文件和敏感目录 | NAS / 权限 / 时间 | 不推荐 | 用户明确授权具体路径白名单时切换 |
| Git-only migration | 最快 | 不满足 NAS 目录、传输、备份需求 | 迁移 / 备份 | 不推荐 | 用户取消 NAS 需求时切换 |

## 影响 HLD 的结论

| 输入 | 采纳章节 | 结论 |
|---|---|---|
| NAS 目录使用方案 | HLD §5 | 采用逻辑 root 映射到 512G hot、4T warm、14T cold |
| 数据传输方案 | HLD §6 | 采用 staging / checksum / promote / record |
| 数据备份方案 | HLD §7 | 4T RAID 为主 archive，14T HDD 为 cold backup，hot cache 不作唯一副本 |
| 不扫描 NAS | HLD §1 / §14 / §15 | CR053 不执行真实 NAS 操作，真实路径绑定后置 |

## 不授权项

- 不扫描 NAS。
- 不创建、复制、删除或移动 NAS 目录。
- 不执行真实目录重命名。
- 不读取凭据或 `.env`。
- 不 git push / tag publish / 重写历史。
- 不连接 QMT / MiniQMT，不执行交易动作。
