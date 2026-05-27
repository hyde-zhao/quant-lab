---
checkpoint: "CP6"
story_id: "CR006-S04-old-data-reference-only-guardrail"
story_title: "Old data reference-only guardrail"
status: "PASS"
checked_at: "2026-05-19T22:16:53+08:00"
agent: "meta-dev/dev-yang"
handoff: "process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md"
implementation_allowed_by: "checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md"
post_s03_aggregate_required: true
---

# CP6 - CR006-S04 编码完成检查

## Entry Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| CP5 已人工批准并允许进入实现 | PASS | `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` 状态为 approved；`process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md` 已 confirmed 且 `implementation_allowed=true`。 |
| W1/S01 前置已满足 | PASS | `process/checks/CP6-CR006-S01-tushare-first-data-acquisition-runbook-CODING-DONE.md` 为 PASS。 |
| W2/S02 前置已满足 | PASS | `process/checks/CP6-CR006-S02-canonical-gold-lightweight-engine-adapter-CODING-DONE.md` 为 PASS；S02 阶段全量 pytest 记录为 `115 passed`。 |
| W3/S04 写入边界明确 | PASS | 本次只写 handoff 允许的 README、用户手册、`.gitignore`、S04 guardrail 测试和本 CP6 文件。 |
| 并行协作边界明确 | PASS | S03 正在并行修改 Backtrader/reader 相关代码；本次未修改 S03 文件。 |

## Agent Dispatch Evidence

| 字段 | 记录 |
|---|---|
| dispatch source | 用户在当前 Codex 会话中明确指定“你是 meta-dev/dev-yang”，要求执行 `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md`。 |
| handoff file | `process/handoffs/META-DEV-CR006-BATCH-A-DEV-W3-S04-2026-05-19.md`，本次只读消费，不回写该文件。 |
| execution role | `meta-dev/dev-yang`。 |
| execution mode | 当前会话直接执行 handoff；不是 meta-po 代执行，不标记 inline fallback。 |
| completed_at | `2026-05-19T22:16:53+08:00`。 |
| dispatch limitation | 当前允许写入范围不包含 handoff 文件，因此未在 handoff frontmatter 中追加 completed_at；本 CP6 作为本次编码完成证据。 |

## Implementation Summary

| 文件 | 变更摘要 |
|---|---|
| `README.md` | 新增 CR-006 旧 data reference-only guardrail 小节，明确旧 repo `data/` 只作人工参考线索，不得作为 fallback、迁移源、覆盖证明、fixture、smoke 前置或运行时输入；补充缺口必须返回 `required_missing` / unavailable 并走 dry-run 优先的 Tushare-first runbook。 |
| `docs/USER-MANUAL.md` | 在准备材料和 Tushare runbook 中补充旧 repo `data/` reference-only 边界、授权门禁和缺口处理规则。 |
| `.gitignore` | 补充本地湖、legacy flat、parquet/feather/arrow/sqlite/db、credentials、key/secret 等忽略规则，保持真实数据、凭据和大型输出不入库。 |
| `tests/test_cr006_old_data_reference_guardrail.py` | 新增 S04 静态 guardrail 测试：使用精确 allowlist、字符串级 denylist、文档合同断言、`.gitignore` 断言和高风险旧数据/凭据措辞扫描。 |
| `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md` | 记录本次 CP6 编码完成检查、测试结果、限制和 CP7 输入。 |

## Checklist

| 检查项 | 结果 | 说明 |
|---|---|---|
| 保持 S04 单 Story 范围 | PASS | 未修改 `engine/**`、`experiments/**`、`market_data/**`、`config/**`、Backtrader 测试或其他 Story 产物。 |
| 文档明确旧 data reference-only | PASS | README 和用户手册均声明旧 repo `data/` 只作人工参考，不可 fallback、迁移、覆盖证明、fixture、smoke 前置或运行时输入。 |
| 授权门禁明确 | PASS | 文档要求读取、列出、复制、迁移、比对或删除旧 `data/**` 前必须有具体、显式、当次授权；默认次数为 0。 |
| Tushare-first 缺口处理明确 | PASS | 缺少真实 Tushare、canonical/gold、benchmark 或 quality/catalog 时返回结构化缺口，不静默回退旧数据。 |
| `.gitignore` 覆盖本地湖与凭据 | PASS | 增加 lake/output/legacy/credential/secret 相关忽略规则。 |
| Guardrail allowlist 精确 | PASS | 测试只对固定文档/源码/测试路径建模，不做仓库全量遍历。 |
| Guardrail denylist 精确 | PASS | 阻断 `data/**`、`.env*`、凭据、大型数据/二进制、缓存和本地湖路径；denylist 判定为字符串级规则。 |
| 禁止真实数据/凭据访问 | PASS | 本次未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取 `.env`；未触发 Tushare、lake read/write、normalize、validate、read 或 replay/backfill。 |
| 最低验证命令 | PASS | `uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py` 通过。 |

## Test Results

| 命令 | 结果 |
|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py` | PASS，最近一次复跑为 `5 passed in 0.01s`。 |

说明：开发中曾有一次测试自身 monkeypatch `Path.exists` 导致 pytest internal error，已移除该写法并改为纯字符串规则测试；最终最低验证命令已通过。

## Exit Criteria

| 条目 | 结果 | 证据 |
|---|---|---|
| S04 文档合同已落地 | PASS | README 与用户手册均包含 CR-006 reference-only guardrail。 |
| S04 静态 guardrail 测试已落地 | PASS | `tests/test_cr006_old_data_reference_guardrail.py` 存在并通过最低验证。 |
| 写入范围未越界 | PASS | 仅写入 handoff 允许的 5 个路径。 |
| 可交给 CP7 验证 | PASS_WITH_LIMITATION | S04 自身可进入 CP7；由于 S03 并行中，主线程需在 S03 CP6 后补跑聚合验证。 |

## Deliverables

| 交付物 | 状态 |
|---|---|
| `README.md` | DONE |
| `docs/USER-MANUAL.md` | DONE |
| `.gitignore` | DONE |
| `tests/test_cr006_old_data_reference_guardrail.py` | DONE |
| `process/checks/CP6-CR006-S04-old-data-reference-only-guardrail-CODING-DONE.md` | DONE |

## Limitations And CP7 Input

- S03 与 S04 并行执行；本次 S04 guardrail 测试建模了 `POST_S03_STATIC_SCAN_TARGETS`，但不把 S03 正在编辑的 Backtrader 新产物作为本次 CP6 的完成前置。
- CP7 或主线程聚合验证需要在 S03 CP6 完成后补跑 S04 guardrail，并视需要纳入 `engine/backtrader_adapter.py`、`engine/backtest.py`、`market_data/readers.py` 和 `tests/test_cr006_backtrader_clean_feed.py` 的最终版本。
- 本次没有执行全量 pytest；S02 阶段已有全量 `115 passed`，本次只执行 handoff 要求的 S04 最低验证命令。

## Safety Confirmation

- 未读取、列出、迁移、复制、比对或删除真实 `data/**`。
- 未读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或真实私有路径。
- 未执行真实 Tushare 抓取、真实 lake read/write、normalize、validate、read、replay 或 backfill job。
- 未修改 S03 并行负责的 `engine/backtrader_adapter.py`、`engine/backtest.py`、`market_data/readers.py` 或 Backtrader 测试。
- 未回滚、覆盖或整理其他 agent 的改动。

## Conclusion

CP6 结论：PASS。

S04 编码范围已完成，最低验证通过。剩余非阻塞项为 W3 聚合层面的 post-S03 补跑：待 S03 CP6 完成后，主线程应重新执行 S04 guardrail 或全量聚合验证，确认 S03 最终代码也符合旧 data reference-only 合同。
