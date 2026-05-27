---
handoff_id: "NEXT-SESSION-CR005-TUSHARE-5000-DATA-LAYER-2026-05-17"
from_agent: "codex"
to_agent: "meta-po"
status: "handoff-created"
created_at: "2026-05-17T16:25:00+08:00"
workflow_id: "local_backtest"
change_id: "CR-005"
dispatch:
  required: true
  mode: "handoff-only"
  platform: "codex"
  agent_role: "meta-po"
  agent_path: ".codex/agents/meta-po.toml"
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: "当前仅为重启会话交接文件；未拉起子 agent，未执行实现。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# 下一会话交接：CR-005 Tushare 5000 数据层整改

## 恢复入口

重启会话后请先读取：

1. `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`
2. `process/STATE.md`
3. `process/changes/CR-004-MARKET-DATA-COMPONENT-2026-05-17.md`
4. `checkpoints/CP5-CR004-BATCH-D-DATALOADER-EXPERIMENT-READONLY-LLD-REVIEW.md`
5. `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`
6. `process/stories/STORY-018-cr004-experiment-readonly-benchmark-LLD.md`

## 当前事实

1. CR-004 Batch D CP5 已通过。
2. STORY-004 Data Loader LLD 已确认，但尚未实现本轮 Batch D。
3. STORY-018 实验十/十二只读接入 LLD 已确认，但尚未实现。
4. 用户准备购买 Tushare 5000 积分档，并询问数据层是否需要整改。
5. 已形成 CR-005 文档，当前仅为 draft / next-session 状态。

## 当前结论

数据层需要整改，但不需要推倒重来：

1. 保留 `market_data/` 独立可迁移包。
2. 保留 Parquet 数据湖。
3. 保留 raw + manifest + canonical + quality + catalog。
4. 保留 Data Loader / 实验只读本地数据边界。
5. 需要将 Tushare 从 fail-fast adapter 升级为可控真实 connector。
6. 需要新增或扩展 `hs300_index`、`index_weights`、`trade_calendar`、`prices` 等 dataset。

## 下一会话建议动作

1. 使用 `change-impact-analysis` 受理 CR-005，确认是否激活该 CR。
2. 唤醒或复用 `meta-po` 组织：
   - `meta-se`：评审 HLD/ADR/Story Plan 如何增量更新。
   - `meta-qa`：评审凭据、联网、默认离线测试、真实数据写入风险。
3. 生成 CR-005 的 HLD/ADR/Story Plan 修订稿。
4. 形成 CR-005 Story LLD 批次，进入 CP5 人工确认。
5. CP5 通过前不得实现 Tushare 真实调用，不得修改真实数据目录，不得写 token。

## 建议子 agent 复用键

- `role=meta-po, workflow_id=local_backtest, change_id=CR-005`
- `role=meta-se, workflow_id=local_backtest, change_id=CR-005`
- `role=meta-qa, workflow_id=local_backtest, change_id=CR-005`
- `role=meta-dev, workflow_id=local_backtest, change_id=CR-005`，仅在 LLD 批次通过后使用

## 禁止事项

1. 不要在下一会话一开始直接改代码。
2. 不要把 Tushare token 写进文件、日志、manifest、测试或对话。
3. 不要让 `engine/data_loader.py` 或实验脚本直接调用 Tushare。
4. 不要真实抓取全量数据，除非后续有明确 CP5/CP6 范围和用户确认。
5. 不要删除 CR-004 fake/offline 默认路径。

