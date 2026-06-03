---
story_id: "CR019-S09-deferred-capability-register"
title: "Backtrader / Qlib / minute / Level2 后置能力 register"
story_slug: "deferred-capability-register"
lld_version: "1.0"
tier: "S"
status: "approved"
confirmed: true
created_by: "meta-dev"
created_at: "2026-05-30T18:29:40+08:00"
confirmed_by: "user"
confirmed_at: "2026-05-30T18:56:50+08:00"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
shared_fragments: []
open_items: 0
---

# LLD: CR019-S09 — Backtrader / Qlib / minute / Level2 后置能力 register

本文档只定义 CR019-S09 的低层设计。`confirmed=true` 且 CP5 已通过；实现仍需 Story 卡片 `implementation_allowed=true`、依赖和文件所有权门控满足；不得新增依赖、连接 Qlib provider、抓 minute / Level2 数据、读取凭据或扩大阶段六 P0 admission 范围。

## 1. Goal

创建 `docs/CR019-DEFERRED-CAPABILITIES.md` 的后置能力 register、`tests/test_cr019_deferred_capabilities.py` 的静态验证入口，并在后续实现阶段增量更新 `README.md`，固化 Backtrader W6、Qlib W7、minute Spike、Level2 Spike 的触发条件、blocked reason 和后续 CR / CP 入口，确保它们不进入阶段六 P0 admission 与 QMT C/S bridge 默认实现范围。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 为 Backtrader、Qlib、minute、Level2 四类能力各定义 1 条 register entry。
- 每条 entry 必须包含：能力 ID、当前状态、非 P0 原因、触发条件、blocked reason、所需证据、后续 CR / CP 入口、禁止项和重访条件。
- README 增量只说明这些能力为 deferred / later-gated，不写成当前已启用能力。
- 测试必须验证四类能力均具备触发条件、blocked reason、后续 CR / CP 入口和禁止声明。

### 2.2 Non-Functional

- 范围控制：阶段六 P0 admission / QMT C/S bridge 依赖新增次数为 0。
- 依赖安全：`pyproject.toml` / `uv.lock` 修改次数为 0；不新增 Backtrader / Qlib / minute / Level2 运行依赖。
- 数据安全：不写 Qlib `provider_uri`、不声明 Level2 entitlement、不得发起 minute data fetch。
- 可维护：register 作为 roadmap / scope boundary，不作为运行时 feature flag 或自动启用开关。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| Deferred capability document | 以表格固定四类能力的后置状态、触发条件、blocked reason 和 CR / CP 入口 | `docs/CR019-DEFERRED-CAPABILITIES.md`；文档即 register |
| README boundary note | 面向用户说明 CR019 P0 不包含 Backtrader/Qlib/minute/Level2 默认启用 | `README.md` 增量；不得写成能力已可运行 |
| Static register tests | 解析文档和 README，检查 4 条 entry、禁止项、依赖边界和真实配置缺失 | `tests/test_cr019_deferred_capabilities.py` |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `docs/CR019-DEFERRED-CAPABILITIES.md` | 新建四类后置能力 register，包含触发条件、blocked reason、证据和后续 CR / CP 入口 |
| 创建 | `tests/test_cr019_deferred_capabilities.py` | 新建静态文档 / register 测试，验证完整性和禁止项 |
| 修改 | `README.md` | 增量加入 deferred capability 非 P0、非默认授权边界 |

## 5. 数据模型与持久化设计

本 Story 不新增运行时数据模型和持久化。`DeferredCapabilityEntry` 是文档表格合同，不写数据库、不写 lake、不读取 provider、不生成真实配置。

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `capability_id` | string | 固定 4 个 ID | `backtrader_w6`、`qlib_w7`、`minute_spike`、`level2_spike` |
| `current_status` | enum | `deferred` 或 `spike_candidate` | 默认不启用、不进入 P0 |
| `non_p0_reason` | string | 必填 | 说明为何不纳入阶段六 P0 admission / QMT bridge |
| `trigger_conditions` | list | 每条至少 2 个条件 | 触发后仍需新 CR / CP，不自动进入实现 |
| `blocked_reason` | string | 必填 | 面向 admission / docs 的阻断原因 |
| `required_evidence` | list | 必填 | clean feed、factor panel、PIT、权限或微观结构风险证据 |
| `next_cr_cp_entry` | string | 必填 | 后续 CR / CP / Spike 入口 |
| `forbidden_claims` | list | 必填 | 禁止新增依赖、provider_uri、entitlement claim、minute fetch 等 |
| `revisit_condition` | string | 必填 | 何时重新进入需求 / HLD / Story Plan |

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `docs/CR019-DEFERRED-CAPABILITIES.md#Deferred Capability Register` | 四类能力静态表 | 后置能力 register | README、CP5、后续 CR / Spike | 测试 T-S09-01 至 T-S09-04 覆盖 |
| `README.md#CR-019 deferred capabilities` | register 摘要 | 用户可读边界说明 | 用户 / meta-doc / QA | 测试 T-S09-05 覆盖 |
| `tests/test_cr019_deferred_capabilities.py` static parser | Markdown 文档 | PASS / FAIL | meta-qa / CI | 测试自身检查结构、禁止项和配置泄露 |

## 7. 核心处理流程

1. 实现阶段创建 `docs/CR019-DEFERRED-CAPABILITIES.md`。
2. 文档先写入 no-real-operation 声明，明确 register 不启用能力、不新增依赖、不触发 provider / data fetch。
3. 文档写入四条 capability entry，并为每条 entry 填写触发条件、blocked reason、required evidence、next CR / CP entry 和 forbidden claims。
4. README 增量只引用该 register 的非 P0 边界，不复制长表。
5. 静态测试解析文档，检查四类能力完整性、P0 依赖新增次数为 0、真实配置出现次数为 0。

## 8. 技术设计细节

- 关键规则：register 是范围管理合同，不是运行时开关；任何能力从 `deferred` 转为实现都必须另起 CR / Story / CP5。
- Backtrader 触发条件：clean feed、候选策略稳定、执行语义对照需求明确，且不抢占阶段六 admission 主线。
- Qlib 触发条件：factor panel、report catalog、PIT / available_at 和 isolated runner I/O 合同稳定；不得在本 Story 写 `provider_uri`。
- minute 触发条件：交易现实性实验证明日频执行假设不足，且已有数据源、存储和质量审计方案。
- Level2 触发条件：订单簿深度、排队、冲击成本或微观结构成为主要风险，且 L1 / minute 证据不足；不得声明已拥有 Level2 权限。
- 图示类型选择：本 Story 是静态 register，无跨模块复杂流程，不需要 Mermaid 图。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 文档禁止真实 provider URI、Level2 entitlement、minute fetch、credential 示例 | 静态测试关键字和结构断言 |
| 安全 | README 不写“已启用 / 默认可用 / 授权使用”语义 | 静态测试匹配禁止语义 |
| 范围 | register 不修改 P0 admission / QMT bridge 依赖 | 测试检查 `pyproject.toml`、`uv.lock` 不在文件影响范围 |
| 性能 | 无运行时路径；测试只读 Markdown | pytest 静态解析，无网络、无 lake、无服务 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| T-S09-01 四类能力齐全 | 文档存在 | 解析 register | Backtrader、Qlib、minute、Level2 各 1 条 entry | pytest |
| T-S09-02 触发条件完整 | 文档存在 | 检查每条 entry | 每条包含 trigger conditions、required evidence、revisit condition | pytest |
| T-S09-03 blocked reason 与 CR / CP 入口 | 文档存在 | 检查字段 | 每条包含 blocked reason 和 next CR / CP entry | pytest |
| T-S09-04 禁止项 | 文档存在 | 搜索 forbidden claims | 无 Qlib provider_uri、Level2 entitlement claim、minute fetch 真实配置 | pytest |
| T-S09-05 README 边界 | README 增量存在 | 静态匹配 | README 说明 deferred / non-P0，不声明当前授权 | pytest |
| T-S09-06 依赖不变 | 仓库文件列表 | 检查影响范围 | `pyproject.toml` / `uv.lock` 修改次数为 0 | pytest 或 git diff 证据 |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR019-S09-T1 | 创建 | `docs/CR019-DEFERRED-CAPABILITIES.md` | 定义 Backtrader、Qlib、minute、Level2 四类后置能力 register | T-S09-01 至 T-S09-04 |
| CR019-S09-T2 | 创建 | `tests/test_cr019_deferred_capabilities.py` | 验证四类能力均有触发条件、blocked reason、后续 CR / CP 入口和禁止项 | T-S09-01 至 T-S09-06 |
| CR019-S09-T3 | 修改 | `README.md` | 增量记录后置能力非 P0、非默认授权边界 | T-S09-05 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| CP3-CR019-DQ-06 | Backtrader、Qlib、minute、Level2 是否进入阶段六 P0 | 推荐：全部后置触发；备选：提前 Backtrader / Qlib / minute / Level2 | 已由 CP3 approve 接受推荐；S09 只做 deferred register | 范围 / 依赖 / 测试 / 文档 / 后续 CR | `checkpoints/CP3-CR019-HLD-REVIEW.md`、ADR-073、HLD §33.14 | 任一能力满足触发条件后，另起 CR / Spike / CP5 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| register 被误读为实现授权 | 用户可能认为能力已可运行 | README 和 register 同时写 non-P0 / deferred / later-gated；测试禁止授权语义 |
| Qlib provider_uri 泄露或被写入示例 | 凭据 / 私有路径风险 | 文档只写字段名禁区，不给真实 URI；测试匹配 `provider_uri` 真实配置模式 |
| Level2 权限声明过度 | 可能造成权限和成本承诺 | entry 明确 entitlement claim 为 0，触发后必须新 CR |
| minute 数据提前抓取 | 扩大数据工程范围 | register 将 minute 作为 Spike，禁止 fetch 和依赖变更 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| 无 | N/A | 无阻断 OPEN / Spike | N/A | N/A |

## 13. 回滚与发布策略

- 发布方式：CP5 全量人工确认后，按 TASK-ID 创建 register、测试和 README 增量；不修改依赖。
- 回滚触发条件：文档出现当前启用语义、新依赖要求、真实 provider_uri、Level2 entitlement claim、minute fetch 配置或阶段六 P0 范围扩张。
- 回滚动作：删除 `docs/CR019-DEFERRED-CAPABILITIES.md` 和对应 README 增量，保留测试失败证据；不得回滚 HLD / ADR。

## 14. Definition of Done

- [ ] `docs/CR019-DEFERRED-CAPABILITIES.md` 包含 Backtrader、Qlib、minute、Level2 四类 entry。
- [ ] 每类 entry 包含触发条件、blocked reason、required evidence、next CR / CP entry 和 forbidden claims。
- [ ] `tests/test_cr019_deferred_capabilities.py` 通过静态检查。
- [ ] README 增量只说明 deferred / non-P0 / later-gated，不声明能力已启用。
- [ ] `pyproject.toml` / `uv.lock` 修改次数为 0。
- [ ] Qlib provider_uri、Level2 entitlement claim、minute fetch 真实配置出现次数为 0。
- [ ] 第 6 节接口均有第 10 节测试覆盖。
- [ ] `confirmed=true` 后仍需 Story 卡片、依赖和文件所有权门控满足后进入实现。

## 人工确认区

> CP5 自动预检文件：`process/checks/CP5-CR019-S09-deferred-capability-register-LLD-IMPLEMENTABILITY.md`
>
> 本 LLD 已纳入 `CR019-STAGE6-QMT-BRIDGE-BATCH-A` 并通过 CP5 全量 LLD 统一确认。用户已回复 `approve`；实现仍需 Story 卡片、依赖和文件所有权门控满足。
