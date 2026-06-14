---
discussion_id: "CP3-CR053-HLD-DISCUSSION"
change_id: "CR-053"
status: "approved"
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

## CP3 补充问答与确认

| 时间 | 用户问题 / 决策 | 处理结论 | 写入位置 |
|---|---|---|---|
| 2026-06-14T10:59:13+08:00 | NAS root 映射是否可以把 NAS 三个分区一起映射？ | 可以在 Linux 研究机统一暴露 `/mnt/quant-lab/*` 逻辑视图，但底层保持 512G hot、4T archive、14T cold-backup 三个独立分区。 | HLD §5、ADR-CR053-001/007 |
| 2026-06-14T10:59:13+08:00 | 当前数据湖已有映射方案，是否需要调整？ | 不调整。继续使用 `MARKET_DATA_LAKE_ROOT` / 显式 `--lake-root`；`QUANT_LAB_MARKET_DATA_LAKE_ROOT` 只作文档 alias / pointer。 | HLD §5/§7、ADR-CR053-006 |
| 2026-06-14T10:59:13+08:00 | Windows 交易机是否需要映射？ | 只映射 package exchange，默认 read-only；不映射 research archive、cold backup 或完整 lake。 | HLD §5/§6、ADR-CR053-005/007 |
| 2026-06-14T10:59:13+08:00 | Linux 研究机是否都可以映射？ | Linux 研究机是主要挂载端，可同时挂载 hot / archive / cold-backup 三层；真实挂载仍需后续用户配置或授权。 | HLD §5、ADR-CR053-007 |
| 2026-06-14T10:59:13+08:00 | 用户回复“同意，继续推进”。 | 按 CP3 approved 处理，进入 CP4 story-planning。 | CP3 checkpoint / STATE |

## 不授权项

- 不扫描 NAS。
- 不创建、复制、删除或移动 NAS 目录。
- 不执行真实目录重命名。
- 不读取凭据或 `.env`。
- 不 git push / tag publish / 重写历史。
- 不连接 QMT / MiniQMT，不执行交易动作。
