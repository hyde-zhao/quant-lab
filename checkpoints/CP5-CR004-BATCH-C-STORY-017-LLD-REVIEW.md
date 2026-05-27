---
checkpoint_id: "CP5"
checkpoint_name: "CR-004 批次 C STORY-017 LLD 确认门"
type: "rolling_auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-17T14:21:50+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-17T14:25:58+08:00"
auto_check_result: "process/checks/CP5-CR004-BATCH-C-STORY-017-LLD-PRECHECK.md"
target:
  phase: "story-execution"
  story_id: "STORY-017"
  artifacts:
    - "process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md"
    - "process/stories/STORY-017-cr004-cli-offline-comparison.md"
---

# CP5 CR-004 批次 C STORY-017 LLD 确认门 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP5-CR004-BATCH-C-STORY-017-LLD-PRECHECK.md` | PASS | 0 | STORY-017 LLD 已通过自动预检，仍保持 `confirmed=false`、`implementation_allowed=false`。 |

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 已确认 | 待审查 | `checkpoints/CP3-CR004-HLD-REVIEW.md` |  |
| CP4 已确认 | 待审查 | `checkpoints/CP4-CR004-STORY-PLAN-REVIEW.md` |  |
| STORY-014/015 verified | 待审查 | `process/checks/CP7-STORY-014-cr004-market-data-package-lake-contracts-VERIFICATION-DONE.md`; `process/checks/CP7-STORY-015-cr004-connector-runtime-raw-manifest-VERIFICATION-DONE.md` |  |
| STORY-016 verified | 待审查 | `process/checks/CP7-STORY-016-cr004-canonical-validation-readers-VERIFICATION-DONE.md` |  |
| STORY-017 LLD 已完成 | 待审查 | `process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md` |  |
| 实现尚未开始 | 待审查 | STORY-017 LLD frontmatter；`market_data/cli.py` / `market_data/comparison.py` / `tests/test_market_data_cli_comparison.py` 尚未作为本 Story 实现提交 |  |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 STORY-017 只实现 `market_data` CLI offline 闭环和 fake/reference comparison 接口 | 待审查 | STORY-017 LLD §1、§2、§4 |  |
| 2 | 是否接受本 Story 不做真实联网抓取、真实沪深 300 gold、实验十/十二接入、Data Loader 或安装交付脚本 | 待审查 | STORY-017 LLD §1、§2、§12 |  |
| 3 | 是否接受首版 CLI 入口为 `python -m market_data.cli`，不新增 console script，不修改 `pyproject.toml` / `uv.lock` | 待审查 | STORY-017 LLD §2、§4、§8、§13 |  |
| 4 | 是否接受 CLI 默认 `source=fake`、`offline=true`，真实 source 未显式启用必须 fail fast | 待审查 | STORY-017 LLD §2、§6、§7、§8 |  |
| 5 | 是否接受默认测试路径网络调用次数为 0，且不需要凭据 | 待审查 | STORY-017 LLD §2、§9、§10 |  |
| 6 | 是否接受 `validate` 继续保留质量报告 CSV canonical、Markdown human-only | 待审查 | STORY-017 LLD §2、§5、§7、§10 |  |
| 7 | 是否接受 `validate` 输出保留 `fetch_status`、`dataset_status`、coverage、thresholds、denominator、可复现字段和 non-PIT 披露 | 待审查 | STORY-017 LLD §5、§8、§10、§14 |  |
| 8 | 是否接受 `read` 只调用 reader，不导入 connector/runtime、不写数据湖、不自动 fetch/normalize | 待审查 | STORY-017 LLD §6、§7、§10 |  |
| 9 | 是否接受 comparison 默认只比较本地 canonical/reference frame 或临时 fixture，不调用真实 source | 待审查 | STORY-017 LLD §1、§5、§6、§8 |  |
| 10 | 是否接受 comparison 输出字段至少包含 `dataset,key,field,left_source,right_source,left_value,right_value,diff,tolerance,status` | 待审查 | STORY-017 LLD §5、§6、§10、§13 |  |
| 11 | 是否接受测试只使用 `tmp_path`、fake/reference fixture 和临时 CSV/parquet，不写真实 `data/**`、`reports/**`、`delivery/**` | 待审查 | STORY-017 LLD §2、§9、§10、§13 |  |
| 12 | 是否授权 CP5 通过后由 `meta-dev` 实现 STORY-017 限定文件范围 | 待审查 | STORY-017 LLD §4、§11、§13 |  |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| STORY-017 LLD 可作为实现输入 | 待审查 | STORY-017 LLD |  |
| CP5 通过后实现范围清晰 | 待审查 | STORY-017 LLD §4、§11、§13 |  |
| 离线、安全、质量报告和 comparison 边界已明确消费 | 待审查 | STORY-017 LLD §2、§5、§7、§8、§9、§10 |  |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| STORY-017 LLD | `process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md` | 待审查 |  |
| CP5 自动预检 | `process/checks/CP5-CR004-BATCH-C-STORY-017-LLD-PRECHECK.md` | 待审查 |  |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-17T14:25:58+08:00
- 修改意见：无。按 `process/stories/STORY-017-cr004-cli-offline-comparison-LLD.md` 限定范围实现。
- 风险接受项：本轮仅覆盖 CLI offline 闭环和 fake/reference comparison 接口；不覆盖真实联网抓取、真实沪深 300 gold、实验十/十二接入、Data Loader 或安装交付脚本。

## 可直接回复

请回复以下任一格式：

- `1` / `approve` / `通过`：批准 CP5 批次 C STORY-017，允许 `meta-dev` 实现 STORY-017。
- `2 修改: <具体修改点>`：要求修改后重新提交 CP5。
- `3` / `reject` / `不通过`：拒绝本次 STORY-017 LLD。
