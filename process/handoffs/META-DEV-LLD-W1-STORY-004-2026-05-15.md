---
handoff_id: "META-DEV-LLD-W1-STORY-004-2026-05-15"
from_agent: "meta-po"
to_agent: "meta-dev"
created_at: "2026-05-15"
phase: "story-execution"
wave: "W1"
hld_phase: "M1 - 本地动量最小回测器"
story_id: "STORY-004"
task_type: "lld-draft"
status: "dispatched"
governance: "LLD 门控；不得实现"
---

# meta-dev 交接：STORY-004 LLD 起草

## 任务边界

请仅为 `STORY-004：离线 Data Loader 与合同校验` 起草 Story 级 LLD，输出目标为 `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`，并将 Story 状态推进到 `ready-for-lld-review` 后交回 meta-po 发起 Story LLD 人工确认。

本交接不授权实现代码、生成数据、写入 `delivery/**` 或生成安装脚本。LLD 未经人工确认前，不得创建或修改 `engine/data_loader.py`，不得修改 `engine/contracts.py`，不得推进 `STORY-005+`。

## 入口事实

| 项 | 状态 | 证据 |
|---|---|---|
| 当前阶段 | `story-execution` | `process/STATE.md` |
| 当前 Wave | W1/M1，串行 | `process/DEVELOPMENT-PLAN.yaml` 中 W1 `parallel=false` |
| W0 | completed | `STORY-001`、`STORY-002`、`STORY-003` 均为 `verified` |
| STORY-003 | `verified` | `process/VERIFICATION-REPORT.md` 中 bugfix regression 结论 PASS；`BUG-STORY-003-001` 为 `CLOSED / REGRESSION_PASS` |
| STORY-004 | `approved` | `process/stories/STORY-004-offline-data-loader-contract-validator.md` |

## 必须读取的最小上下文

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前阶段、active story、W1 门控与非阻断观察项 |
| `process/STORY-STATUS.md` | W0 完成证据、W1 当前 Story 状态 |
| `process/DEVELOPMENT-PLAN.yaml` | W1 串行计划、STORY-004 依赖、输出边界和完成准则 |
| `process/STORY-BACKLOG.md` | STORY-004 范围、验收目标、依赖图 |
| `process/stories/STORY-004-offline-data-loader-contract-validator.md` | Story 卡、任务清单、验收标准和 LLD 输入约束 |
| `process/HLD.md` | §8.3、§9.1、§9.3、§11、§12.2、§16 M1 设计依据 |
| `process/ARCHITECTURE-DECISION.md` | ADR-001、ADR-003、ADR-006 的离线、复权和质量降级决策 |
| `process/stories/STORY-003-parquet-quality-report.md` | 上游 parquet 与质量报告 Story 范围、验收和已验证状态 |
| `process/stories/STORY-003-parquet-quality-report-LLD.md` | 上游标准化 parquet、质量报告、manifest 关联和异常路径契约 |
| `process/VERIFICATION-REPORT.md` | STORY-003 PASS、`BUG-STORY-003-001` CLOSED / REGRESSION_PASS、非阻断观察项 |
| `process/TEST-STRATEGY.md` | 当前 QA 观察项与后续验证边界参考 |
| `engine/contracts.py`、`engine/normalizer.py`、`engine/quality.py`、`engine/manifest.py` | 只读理解上游实现契约，不得在 LLD 阶段修改 |

## LLD 输出要求

- 保持 `STORY-*-LLD.md` 的 14 个可见章节契约。
- frontmatter 必须包含 `story_id=STORY-004`、`tier`、`confirmed=false`、`shared_fragments`、`open_items`。
- 必须定义 Data Loader 函数签名、返回对象、metadata schema、异常类型、质量报告定位方式、无网络测试策略和与 STORY-005 的接口。
- 必须显式继承离线主路径约束：Data Loader 不触发 AKShare、requests、httpx、urllib 或任何远程补数。
- 必须覆盖复权一致性、`available_at <= decision_time`、质量状态 `pass/warn/fail` 启动策略、schema 缺失、交易日历排序和股票池字段校验。
- 必须把 `scripts/check_delivery_guardrails.py` 缺失与 `process/VALIDATION-ENV.yaml story_id` 元数据滞后作为非阻断流程观察项处理，不得在本 Story LLD 中创建脚本或改写验证环境确认事实。

## 不应加载或修改

- 不加载无关历史草稿、旧失败轮次或 STORY-005+ 的 LLD。
- 不修改实现代码。
- 不写真实 `data/*.parquet`、`data/raw/**`、`data/manifests/**` 或 `reports/**`。
- 不修改 `delivery/**`。
- 不生成安装脚本。
- 不创建 `scripts/check_delivery_guardrails.py`。
- 不推进 `STORY-005+`。

## 交回条件

完成 LLD 起草后，请回写：

- `process/stories/STORY-004-offline-data-loader-contract-validator-LLD.md`
- `process/stories/STORY-004-offline-data-loader-contract-validator.md` 的状态为 `ready-for-lld-review`
- `process/STORY-STATUS.md`
- `process/STATE.md`

交回时说明：未实现代码、未生成数据文件、未写 `delivery/**`、未生成安装脚本、未创建 guardrail 脚本。
