---
handoff_id: "META-DEV-CR007-S03-IMPLEMENT-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-yang"
status: "completed"
created_at: "2026-05-22T01:08:18+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-DEV-W3-CR008-UNLOCK"
story_id: "CR007-S03-index-members-stock-basic-datasets"
reuse_key: "meta-dev|local_backtest|CR-007|CR007-S03-index-members-stock-basic-datasets|CR007-DEV-W3-CR008-UNLOCK"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b8d-2218-76a1-85f7-ae32f58ff9c0"
  agent_name: "dev-yang the 2nd"
  thread_id: "019e4b8d-2218-76a1-85f7-ae32f58ff9c0"
  spawned_at: "2026-05-22T01:19:45+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T01:28:12+08:00"
  evidence: "前一复用线程 dev-you 无输出后，主线程通过 spawn_agent 真实调度 meta-dev/dev-yang the 2nd 接手同一 CR007-S03 离线实现；CP6 已写入并 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
previous_dispatches:
  - status: "stalled-closed-no-output"
    mode: "resume_agent/send_input"
    platform: "codex"
    tool_name: "resume_agent/send_input"
    agent_role: "meta-dev"
    agent_id: "019e45c2-6da2-7de1-b918-edd973b5676b"
    agent_name: "dev-you"
    thread_id: "019e45c2-6da2-7de1-b918-edd973b5676b"
    resumed_at: "2026-05-22T01:12:26+08:00"
    status_requested_at: "2026-05-22T01:18:00+08:00"
    closed_at: "2026-05-22T01:19:45+08:00"
    evidence: "主线程等待两轮并发送状态请求后，未发现 CP6 文件、目标范围 diff 或完成信号；关闭无输出线程并重新调度。"
---

# META-DEV Handoff: CR007-S03 Implementation For CR008-S05 Unlock

## 目标

按已确认的 `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md` 离线实现 `index_members`、`index_weights`、`stock_basic` readiness / PIT 合同，并写入 CP6。该 Story 本轮作为 `CR008-S05-pit-universe-consumption-contract` 的必要解锁项调度；不得启动 CR007-S04/S05。

## Entry Gate

- `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md` status=`approved`。
- `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md` confirmed=`true`、implementation_allowed=`true`。
- CR007-S01 / S02 已 verified。
- CR008-S03 已 verified，CR008-S04 已 verified。
- 当前仅允许离线实现；真实数据抓取、真实 lake read/write、旧数据和凭据操作均未授权。

## 写入范围

- `market_data/contracts.py`
- `market_data/source_registry.py`
- `market_data/connectors/tushare.py`
- `market_data/normalization.py`
- `market_data/validation.py`
- `market_data/readers.py`
- `tests/test_cr007_index_members_stock_basic_datasets.py`
- `process/checks/CP6-CR007-S03-index-members-stock-basic-datasets-CODING-DONE.md`

## 禁止范围

- 不修改 `engine/**`、`experiments/**`、README/docs、`reports/**`、`delivery/**` 或其他 Story LLD / CP5。
- 不联网，不真实 Tushare fetch。
- 不真实 lake read/write，不执行 normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开或覆盖旧 `reports/data_quality_report.csv`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 凭据或真实私有路径。

## 测试与 CP6 要求

- 必跑：`uv run --python 3.11 pytest -q tests/test_cr007_index_members_stock_basic_datasets.py`
- 视触及范围追加 `market_data` readers / validation 相关离线回归。
- CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、测试命令与结果、安全边界确认。

## 完成标准

- `index_members`、`index_weights`、`stock_basic` readiness / PIT status 结构化输出。
- `index_weights` 自动替代 `index_members` 的次数为 0。
- PIT 不完整时不得声明 PIT available。
- reader 不导入 connector/runtime/storage，不触发 fetch/backfill。
- 完成后由 meta-po 创建 CR007-S03 CP7 handoff；CR008-S05 仍需等待 CR007-S03 CP7 PASS 后再进入实现。
