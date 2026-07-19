---
status: confirmed
version: "2.9"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-07-17T16:54:09+08:00"
ready_for_design: true
---

# Product Requirements

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级需求基线草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充 frontmatter，并把成功标准改为可量化字段集和计数。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation 需求；保留 CR157 adapter backlog boundary 为历史基线。 |
| v0.4 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review workflow 需求，并补齐 `DF-CR157-003` / `BL-CR157-003` promotion 追溯。 |
| v0.5 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 七对象 evidence availability、typed_unavailable fail-closed、CR155 negative regression 和 deferred producer 需求追溯。 |
| v0.6 | 2026-07-11 | meta-pm | CR163 增量追加 experiment-family lifecycle、append-only lineage、count、seal、inventory、integration、integrity 和 authorization 需求。 |
| v0.7 | 2026-07-11 | meta-pm | 根据 SGQ 全部确认 A 归一化 inventory 为 2 条去重 producer chains / 4 个 instrumentation mappings，并明确 present/typed_unavailable/blocked 与 C1 raw-input-only ceiling。 |
| v0.8 | 2026-07-12 | meta-pm | CR164 增量追加方法集、lineage/input binding、输入充分性、确定性、方法冲突、consumer integration、effective-count ceiling 与授权边界需求；回填 SGQ-CR164-001..004 全部确认 A。 |
| v0.9 | 2026-07-13 | host-orchestrator-inline | CR166 增量追加 C2 producer 输入、泄漏边界、确定性 envelope、consumer projection、兼容与授权需求，以及 12 项量化成功标准。 |
| v1.0 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 批准，冻结 9 项需求、12 项 QAC、fixture/static 与 Stage 3 claim ceiling；解锁 CP3 设计但不授权实现。 |
| v1.1 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 批准；9 项需求与 12 项 QAC 映射到五个正式 Story 和 CP5 全量设计证据，继续不授权实现。 |
| v1.2 | 2026-07-13 | host-orchestrator-inline | CR168 增量追加 9 项 C3 需求、15 项精确 QAC、Gate 4 C3+C4 联合边界、两类 fixture 与 5 个 CP2 开放决策；保留既有需求基线。 |
| v1.3 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见为 REQ-CR168-006 增加 projection-side absent-no-na-reason guard，新增 `SC-CR168-B02`；9 项需求、15 项 QAC、10 类 C3 fail-closed 与范围边界均不变，并补齐 CP3 前向设计义务。 |
| v1.4 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准；依据 canonical Gate 4 代码评审，把 reason 逃逸整改精确为 CR168 adapter 的 8-key denylist、strict allowlist、调用前拒绝、调用后非 PASS 断言与 adapter-only 调用面，canonical 全局硬化仍不在本 CR。 |
| v1.5 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 的 9 项 C4 fixture/static requirements、15 项 QAC、strict C3+C4 joint adapter 边界、alpha-decay CP3 disposition 与五项 CP2 DQ；不改写 CR168、canonical Gate 4 或 CR155 基线。 |
| v1.6 | 2026-07-14 | host-orchestrator-inline | 根据 CR169 CP2 评审整改，明确 `stage3_entry_ready=false`，将 Stage 2 exit 的 7/7 事实核验固化为 CP8 / formal exit 义务，并把 FU-007 的 007a/007b 仅登记为后续提案。 |
| v1.7 | 2026-07-15 | host-orchestrator-inline-meta-pm | 增量追加 CR170 的 9 项 canonical Gate 1-5 N/A semantics / Gate 6 admission hardening 需求、21 项 inventory、15 项 QAC 与 tier 不变量；保留现有底层 worst-state merge，单独审查 `resolve_admission_policy`。 |
| v1.8 | 2026-07-15 | host-orchestrator-inline | 回填 CR170 CP2 批准；明确“独立验证者”仅为 FU-006 future consumer，本 CR 以可靠性 Gate 维护者自验证代行且不声明 verifier independence；9 项需求、21/21 inventory、15 项 QAC 和 20 个场景计数不变，解锁 CP3 设计。 |
| v1.9 | 2026-07-15 | meta-pm | CR171 增量追加 Stage 3 entry-route、event-bounded verifier waiver、deny-default read scope、historical legacy/revalidation 与 no-overclaim 需求；CP8 关闭不改变 Stage 3 未启动的事实。 |
| v2.0 | 2026-07-16 | meta-pm（pm-wu） | CR172 增量追加 8 项 P0 activation 需求：PATH-C 默认、PATH-B 恢复链、C2/C3 独立 CR、五字段、C1 降级、双 owner ledger、E1/OI-005 与授权 claim ceiling；待 CP2 统一批准。 |
| v2.1 | 2026-07-16 | meta-pm（pm-zheng） | CR173 增量追加 8 项 P0 offline effective-trial methodology 需求、七字段证据、六类 golden-vector、8 个 CP2 DQ 与 CR172 恢复边界；具体算法留 CP3。 |
| v2.2 | 2026-07-16 | host-orchestrator | 回填 CR173 CP2 批准；八项 DQ 冻结为推荐值，并把 estimator 可识别性不足转 Spike、公共 C1 contract 跨域修改时拆分 projection 固化为 CP3 强制设计义务。 |
| v2.3 | 2026-07-16 | meta-pm（pm-zheng） | 依据 CP3 `DO-001=PASS` / `DO-002=PASS_BY_SPLIT` 解析已批准条件分支：冻结 participation-ratio 二阶 effective-dimensionality 语义，将 REQ-007 收缩为 standalone evidence + public-boundary stop，保持 8 REQ / 8 SC 追溯不变。 |
| v2.4 | 2026-07-16 | host-orchestrator | 修正 CR173 门禁与关联 CR 状态：CP2 已批准、CP3 待人工审查；补入 CR172/CR173 追溯，不改变 8 项 P0 requirement、8 个场景或 estimator-only 边界。 |
| v2.5 | 2026-07-17 | meta-pm（pm-wu） | CR172 scope-delta 前轮草案：保留并标记 DQ/REQ-001~008 为历史已决 PATH-B 基线并加入后续待决集合；其部署、授权和待决集合已由 v2.7 correction R1 全量替换，`ready_for_design=false` 直至本轮 CP2 批准。 |
| v2.6 | 2026-07-17 | host-orchestrator | CP2 发起前状态一致性修正：CR173 已 closed/cp8_closed，不再保留“CP3 人工批准前”旧措辞；其前轮 CR172 待决集合已由 v2.7 correction R1 替换。 |
| v2.7 | 2026-07-17 | meta-pm（pm-wu） | correction R1 将 REQ/DQ-010~012 改为 research-local active canonical → NAS verified replica → execution-local immutable cache，并新增 REQ/DQ-015 的信号本地生成、低频 immutable mailbox 与 intraday 独立 CR 边界。 |
| v2.8 | 2026-07-17 | meta-pm（pm-wu） | correction R2 收缩 REQ/DQ-015 为默认本地生成、可选低频 8 字段 contract 与 intraday split；将详细 exchange/ack/idempotency/path 实现转 deferred；强化 REQ/DQ-014 的 `FU-CR173-001` 硬前置条件和 PATH-C/A 三选一；新增 CP2/3/5/7/8 精确守卫。 |
| v2.9 | 2026-07-17 | meta-pm（pm-wu） | 回填 CR172 PATH-I scope-delta CP2 用户批准：REQ/DQ-009~015 从 awaiting/open 转 confirmed/approved-CP2，`ready_for_design=true`；批准只解锁 CP3，不改变范围、三个强制边界或真实动作授权。 |

## 状态

- 文档状态：confirmed-CP2（CR172 PATH-I scope delta；CR173 CP2/方法学历史不被改写）
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168` / `CR-169` / `CR-170` / `CR-171` / `CR-172` / `CR-173`
- 当前门禁：CR172 PATH-I scope-delta CP2 已于 `2026-07-17T16:54:09+08:00` 获用户批准；`ready_for_design=true`，当前只解锁 CP3 design-only，不授权实现或任何真实 data lake/NAS/runtime/signal/migration/Git remote 操作。
- 旧基线保留：当前仓库未发现既有 `docs/product/REQUIREMENTS.md`；既有组件文档和检查证据作为输入，不被替换。

## Requirement Summary

| REQ ID | 标题 | 优先级 | 状态 | 验收要点 |
|---|---|---|---|---|
| REQ-CR157-001 | Mature admission package builder scope | P0 | draft | 能定义从 mature research package、validation report、offline preflight、observation plan 到准入包的字段与校验边界。 |
| REQ-CR157-002 | Stage 2/Stage 3 handoff hardening | P0 | draft | Handoff 必须显式区分 Stage 2 no-lake 支撑、Stage 3 真实研究输入和 Stage 4 观察候选。 |
| REQ-CR157-003 | Research evidence index traceability | P0 | draft | 每个 package 必须追溯 data release、run manifest、metric refs、lineage refs 和 typed unavailable / blocked reason。 |
| REQ-CR157-004 | Fail-closed no-runtime guard | P0 | draft | provider、lake write、catalog publish、credential、QMT、gateway、simulation、live 和 trading 计数非 0 时阻断。 |
| REQ-CR157-005 | Portfolio risk policy compatibility | P1 | draft | 准入包必须携带 top_n、max_weight、turnover、行业/风格/容量/费用/停止条件等风险策略引用。 |
| REQ-CR157-006 | Backlog strategy adapter boundary | P1 | draft | event/ML adapters 不进入 CR157 first slice；仅保留 adapter 合同兼容性和后续 CR 入口。 |
| REQ-CR157-007 | CP2-before-design gate | P0 | draft | CP2 未 approved 前不得启动 HLD、Story 拆分、LLD 或实现。 |
| REQ-CR158-001 | Unified adapter scope | P0 | draft | CR158 必须同时覆盖 event adapter 与 ML adapter，并明确共享 core 与 type-specific extension 边界。 |
| REQ-CR158-002 | Event strategy adapter contract | P0 | draft | Event adapter 必须能表达事件输入 refs、event-time alignment、signal output refs 和 blocked reasons，且不读取真实 event feed。 |
| REQ-CR158-003 | ML strategy adapter contract | P0 | draft | ML adapter 必须能表达 training snapshot refs、model artifact refs、prediction signal refs、validation refs 和 blocked reasons，且不训练真实模型或写 registry。 |
| REQ-CR158-004 | Evidence index typed extensions | P0 | draft | Event/ML adapter evidence 必须保持 refs-only，并为 event-specific 与 ML-specific refs 提供 typed extension。 |
| REQ-CR158-005 | No-runtime authorization guard | P0 | draft | CR158 不授权真实 feed、training、provider/lake/NAS/credential、runtime、trading、publish 或 registry/store/catalog write；禁用计数非 0 必须 blocked。 |
| REQ-CR158-006 | CP2/CP5 gate enforcement | P0 | draft | CP2 前不得 HLD/Story/LLD/实现；CP5 前不得实现；CP7 必须验证 no-runtime。 |
| REQ-CR158-007 | Release wording boundary | P1 | draft | CP8 release wording 必须区分 fixture/static adapter readiness 与 production/runtime/trading readiness。 |
| REQ-CR160-001 | Stage 4 observation review workflow contract | P0 | draft | 定义 6 个 Stage 4 design objects 的输入、输出、失败路径和后续路由。 |
| REQ-CR160-002 | Observation plan template and instance boundary | P0 | draft | `observation_plan_ref` 必须指向可审查实例；CR160 必须定义 template，Stage 3 产物必须声明 instance 合规性。 |
| REQ-CR160-003 | Layered observation review checklist | P0 | draft | Checklist 必须覆盖 Stage 1、Stage 2、Stage 3 和横切授权/no-overclaim 4 层，每层至少 5 项。 |
| REQ-CR160-004 | Fail-closed evidence lane decision table | P0 | draft | Decision table 必须覆盖 4 条 evidence lane；`contract_only` lane 不得输出 `paper_candidate=true` 或 `simulation_ready`。 |
| REQ-CR160-005 | CR155 blocked seed classification | P0 | draft | 既有 CR155 evidence 必须分类为 `blocked_admission_failed`，且 `paper_candidate=false` 不得被提升。 |
| REQ-CR160-006 | Design-only authorization boundary | P0 | draft | CR160 CP8 approval 不授权代码实现、新数据访问、runtime、simulation、paper、live、trading、publish 或 CR155 晋级。 |
| REQ-CR160-007 | Product baseline traceability refresh | P0 | draft | CP8 关闭前必须更新 6 个产品基线文档，记录 `DF-CR157-003` / `BL-CR157-003` promoted to CR160。 |
| REQ-CR161-001 | Seven-object admission evidence contract | P0 | baseline-refreshed | 当前产品基线必须可发现 C1-C4 对应的七个 evidence objects、用途、availability 和 follow-up producer。 |
| REQ-CR161-002 | Typed-unavailable fail-closed ceiling | P0 | baseline-refreshed | mandatory evidence 缺失或不可计算时必须 `typed_unavailable` 且阻断；不得静默 PASS。 |
| REQ-CR161-003 | Existing-gate integration and CR155 regression | P0 | baseline-refreshed | 复用 CR151/CR154 gate；CR155 仍 blocked，不能由新 contract 或既有 rerun 证据提升。 |
| REQ-CR161-004 | No computed-proof or runtime overclaim | P0 | baseline-refreshed | contract-only baseline 不得声称已计算 FDR/PBO/DSR、OOS folds、TCA、market impact 或容量 sizing，也不得输出 runtime readiness。 |
| REQ-CR161-005 | Deferred evidence-producer traceability | P1 | baseline-refreshed | FU-CR161-001..006 与 FU-CR162-001 必须被记录为 candidate；实现和通用 checker 均需独立授权。 |
| REQ-CR163-001 | Pre-search family lifecycle | P0 | draft | 首个 trial 前必须存在 family declaration；生命周期可校验且不可事后缩小。 |
| REQ-CR163-002 | Append-only trial / attempt / selection lineage | P0 | draft | trial、retry attempt、失败/取消/排除和 selection 事件全部保留且可追溯。 |
| REQ-CR163-003 | Raw trial count semantics | P0 | draft | 参数或 seed 不同形成不同 trial；retry 只增加 attempt；计数与稳定 identity 去重结果一致。 |
| REQ-CR163-004 | Deterministic seal and supersession | P0 | draft | seal 内容确定、hash 可复算；纠错只新增 superseding version，不修改旧版本。 |
| REQ-CR163-005 | Frozen candidate-producer inventory | P0 | confirmed-CP2-input | 2 条去重 producer chains 的 `CPI-CR163-001..004` 4/4 instrumentation mappings 共享 producer contract；excluded paths 不进入分母。 |
| REQ-CR163-006 | Existing-gate availability integration | P0 | confirmed-CP2-input | 只向 CR151/CR154/admission consumer 暴露 lineage availability/ref/raw count；effective count 仍 unavailable，C1 仍不可计算。 |
| REQ-CR163-007 | Completeness, tamper and recovery validation | P0 | draft | missing、duplicate、count mismatch、post-seal mutation 100% fail-closed，并可沿 supersession 恢复。 |
| REQ-CR163-008 | Authorization and CR155 regression boundary | P0 | draft | 禁止真实数据/runtime/外部写入/统计计算/历史回填；CR155 始终 blocked。 |
| REQ-CR164-001 | MVP statistical method set | P0 | confirmed-CP2-input | BH、WRC/SPA、PBO/CSCV、DSR 均为 MVP mandatory methods，claim-relevant 聚合无 OR-pass。 |
| REQ-CR164-002 | Validation-bound family/input identity | P0 | draft | 所有计算绑定同一 sealed family ref/hash/raw count 与完整 candidate membership。 |
| REQ-CR164-003 | Method-specific computable evidence | P0 | draft | 每个批准方法都有输入、输出、参数、provenance、availability 与 blocked reason。 |
| REQ-CR164-004 | Quantitative input sufficiency | P0 | confirmed-CP2-input | 候选、split/fold、sample、finite-value 与退化输入阈值按 SGQ A 可机器判定。 |
| REQ-CR164-005 | Determinism and numerical boundary | P0 | draft | 相同规范化 fixture 可复跑，NaN/Inf/退化输入 fail-closed。 |
| REQ-CR164-006 | Method disagreement projection | P0 | draft | mandatory FAIL/BLOCKED 不得被其他方法 PASS 覆盖；冲突最保守投影。 |
| REQ-CR164-007 | Existing-consumer integration | P0 | draft | 复用 CR151/CR154/admission package，不建立竞争 gate。 |
| REQ-CR164-008 | Effective-trial claim ceiling | P0 | confirmed-CP2-input | raw count 不得冒充 effective count；effective 保持 typed_unavailable。 |
| REQ-CR164-009 | Compatibility, authorization and regression | P0 | confirmed-CP2-input | UC-58 实现、UC-59/60 compatibility-only，禁用操作为 0，CR155 保持 blocked。 |
| REQ-CR168-001 | Versioned typed C3 component | P0 | awaiting-CP2 | 复用 CR166 envelope，把 `economic_cost@reserved` 演进为 1 个 active typed component / 1 个 schema version，不新建平行 gate/envelope/registry。 |
| REQ-CR168-002 | Nine-family explicit input contract | P0 | awaiting-CP2 | 9/9 字段族均有 required/optional/N/A/authorization 规则，含 cost-underestimation assumptions/limitations。 |
| REQ-CR168-003 | Transparent cost and impact approximation | P0 | awaiting-CP2 | 透明输出 fee/tax/spread/slippage/impact approximation、total、gross-to-net、availability、reason、lineage 和 `cost_underestimation_status`。 |
| REQ-CR168-004 | Ten-class fail-closed validation | P0 | awaiting-CP2 | 10/10 指定缺失、数值、basis、算术、lineage/auth 和 hash tamper 类别均不得产生 present/PASS。 |
| REQ-CR168-005 | Deterministic canonical identity | P0 | awaiting-CP2 | 同一规范化输入 10 次只产生 1 个 canonical hash，tamper 必须 blocked。 |
| REQ-CR168-006 | Joint Gate 4 C3 projection | P0 | awaiting-CP2 | 只投影 C3 四字段；C4 unavailable 映射为三个 refs absent-no-na-reason；字段级/通用 na-reason 逃逸由 projection 阻断；capacity/aggregate PASS=0。 |
| REQ-CR168-007 | Multi-strategy-type fixtures | P0 | awaiting-CP2 | daily multifactor synthetic 与 daily/ML compatibility 两族 2/2；event-specific producer=0。 |
| REQ-CR168-008 | Authorization and claim ceiling | P0 | awaiting-CP2 | 禁止真实数据/TCA/calibration/runtime/trading/remote write；Stage2=true、Stage3=false，其余真实/运行时 claim=false/0。 |
| REQ-CR168-009 | C4/FU-007/CR155 boundary | P0 | awaiting-CP2 | C4 calculator=0；aggregate integration 留给 FU-007；CR155 admission promotion=0。 |
| REQ-CR169-001 | Versioned typed C4 component | P0 | awaiting-CP2 | `capacity_liquidity@v1` component/schema=1/1；平行 envelope/registry/gate=0。 |
| REQ-CR169-002 | Independent C4 input and correlation header | P0 | awaiting-CP2 | C4 calculation body 独立，最小 correlation header 待 CP3 冻结且不默认进入 semantic hash。 |
| REQ-CR169-003 | Transparent static C4 proxy | P0 | awaiting-CP2 | 仅 synthetic/static ADV/reference、participation、capacity/liquidity sizing 与 auditable refs。 |
| REQ-CR169-004 | Twelve-class fail-closed validation | P0 | awaiting-CP2 | 12/12 输入、完整性、reason escape 与越权类别不得产生 present/PASS。 |
| REQ-CR169-005 | Deterministic C4 identity | P0 | awaiting-CP2 | 规范化输入 10 次→1 hash；tamper blocked。 |
| REQ-CR169-006 | Strict C3+C4 Gate 4 fixture compatibility | P0 | awaiting-CP2 | 新 adapter 精确组合 verified C3/C4；fixture contract PASS 仅为 1，aggregate/capacity admission PASS=0。 |
| REQ-CR169-007 | C3-only regression and fixtures | P0 | awaiting-CP2 | 2/2 fixture；CR168 C3-only absent-C4 fail-closed 不变。 |
| REQ-CR169-008 | Authorization and claim ceiling | P0 | awaiting-CP2 | 真实数据/calibration/runtime/trading/remote write=0；Stage3=false。 |
| REQ-CR169-009 | Alpha/verifier/FU-007/CR155 boundary | P0 | awaiting-CP2 | alpha CP3 disposition；canonical/global/aggregate 留 FU-007；CR155 BLOCKED。 |
| REQ-CR171-001 | Stage 3 evidence-route decision | P0 | confirmed-delivered | CP2 已选择 C1-C4 real-producer；computation 必须由独立 activation CR 授权。 |
| REQ-CR171-002 | Event-bounded FU-006 verifier waiver | P0 | confirmed-delivered | waiver 在 real-evidence admission PASS/PASS_WITH_RISK 前或 Stage 3 exit gate 启动前自动失效。 |
| REQ-CR171-003 | Deny-default frozen read contract | P0 | confirmed-delivered | 后续 read scope 固定 release/dataset/date/read identity/output directory，并明确拒绝 credentials、provider、write、catalog/current pointer、runtime 与 trading；本 CR 不授权读取。 |
| REQ-CR171-004 | Historical evidence legacy/revalidation ceiling | P0 | confirmed-delivered | 历史 Stage 3 运行只能是 legacy / require-revalidation；revalidation 只分类、标注、报告，三个合法 current-entry verdict 外不得提升任何 readiness claim。 |
| REQ-CR171-005 | Claim ceiling and adjacent-debt isolation | P0 | confirmed-delivered | CP8 成功不等于 entry-ready；CR010/018/032 只披露、不修复，新的风险消费者使用 `R-CR170-RUNNER-GAP`。 |
| REQ-CR172-001 | Finite five-field authorization contract | P0 | confirmed-prior-CP2 | 五字段不能冻结的历史事实保留；通配符/隐式继承/历史目录推断=0，PATH-B 保持已批准历史。 |
| REQ-CR172-002 | Conditional PATH-B/C/A routing | P0 | confirmed-prior-CP2 | 已批准 PATH-B 方法学前置；未来 PATH-C/A 必须重新门禁，不自动恢复。 |
| REQ-CR172-003 | PATH-B activation recovery chain | P0 | confirmed-prior-CP2 | PATH-B 只完成 CR173 方法学前置，不关闭 OI-001..005；恢复仍须 fresh precheck 与人工门禁。 |
| REQ-CR172-004 | C1 typed-unavailable degradation | P0 | confirmed-prior-CP2 | effective count/ref/method unavailable 时 raw alias 与 computable/admission claim=0。 |
| REQ-CR172-005 | Producer isolation and C2/C3 governance | P0 | confirmed-prior-CP2 | 共享 blocker 阻断全部；局部失败只阻断本 producer；C2/C3 独立治理。 |
| REQ-CR172-006 | Effective-trial owner and joint approval | P0 | confirmed-prior-CP2 | 方法学由 CR173 独立承接；未来合并仍要求同 revision/hash 双 ledger 与权限交集。 |
| REQ-CR172-007 | E1, OI-005 and adjacent-scope ceiling | P0 | confirmed-prior-CP2 | CR172/CR173 交付不触发 E1；OI-005、C4、FU-006、aggregate 独立。 |
| REQ-CR172-008 | Runtime-high-risk gate and claim ceiling | P0 | confirmed-prior-CP2 | 产品批准不授权真实行为，Stage3/admission/aggregate claims=false。 |
| REQ-CR172-009 | Trial-return source and object contract | P0 | confirmed-approved-CP2 | PATH-I 必须定义每个 trial 的 portfolio return series；错误 returns 对象与 source 缺失 `100%` fail-closed。 |
| REQ-CR172-010 | Research-local canonical, NAS verified replica and stable URI | P0 | confirmed-approved-CP2 | research-local active canonical；NAS replica/backup/distribution；execution pull+verify+immutable cache；runtime 直读 NAS=`0`。 |
| REQ-CR172-011 | Multi-trial/sync/materialization per-action authorization | P0 | confirmed-approved-CP2 | lake read、runtime/workspace、generation、R compute、NAS sync、execution pull/materialize 六类动作 `6/6` 独立授权。 |
| REQ-CR172-012 | Four-component data ownership and GitHub ceiling | P0 | confirmed-approved-CP2 | 研究机 active canonical、NAS verified replica、执行机 verified local cache、GitHub metadata-only；职责 `4/4`。 |
| REQ-CR172-013 | New-run semantic path and legacy read-only compatibility | P0 | confirmed-approved-CP2 | 新 run 使用 `multifactor-strategy-research/{run_id}`；历史 stage3 目录 move/rename/rewrite=`0`。 |
| REQ-CR172-014 | Declared-exact versus empirical-R fail-closed | P0 | confirmed-approved-CP2 | typed-unavailable 降级不阻断 PATH-C/A 设计；available effective count 或 `c1_computable=true` 必须以 `FU-CR173-001` v2 sampling-error validation 为硬前置。 |
| REQ-CR172-015 | Execution-local signal generation and optional batch-contract boundary | P0 | confirmed-approved-CP2 | 默认执行机本地生成；低频/EOD 只冻结精确 `8/8` 最小字段；详细 exchange/ack/replay/path 与 intraday transport 均 deferred。 |
| REQ-CR173-001 | Effective-dimensionality estimand and non-alias boundary | P0 | confirmed-CP2 | v1 表示 sealed-trial 相关矩阵的 participation-ratio 二阶有效维度；raw alias 与 Li–Ji/BH/FWER/DSR calibration claim=0。 |
| REQ-CR173-002 | CP3 method and input-contract freeze | P0 | confirmed-CP2 | CP2 冻结可观察行为，CP3 对输入类别、有效域、方法/版本/hash 与估计假设覆盖 100%。 |
| REQ-CR173-003 | Typed-unavailable fail-closed semantics | P0 | confirmed-CP2 | 缺方法、无效输入、非有限值、lineage/provenance 缺失或 method/hash/evidence mismatch 均不得产生 available standalone evidence。 |
| REQ-CR173-004 | Seven-field standalone typed evidence and provenance | P0 | confirmed-CP2 | 独立七字段 7/7，任一缺失时 present/available=0，orphan provenance=0。 |
| REQ-CR173-005 | Strategy-agnostic offline boundary | P0 | confirmed-CP2 | `strategy_id/strategy_name` 必填/推断数=0；只用 synthetic/fixture/golden-vector。 |
| REQ-CR173-006 | Deterministic golden-vector acceptance | P0 | confirmed-CP2 | 六类 vectors 6/6，每类重复 3/3，同一输入/方法版本只产生 1 个 canonical result。 |
| REQ-CR173-007 | Standalone evidence and public-boundary stop | P0 | confirmed-CP2 | standalone evidence=1；public C1 projection/write=0；C1/Gate1/admission 保持 typed_unavailable；各类 overclaim=0。 |
| REQ-CR173-008 | Gate, authorization and CR172 prerequisite ownership | P0 | confirmed-CP2 | CR173 只关闭 methodology prerequisite；五字段/data owner/fresh precheck/strategy identity/runtime binding 均不由本 CR 解决。 |

## Functional Requirements

### REQ-CR157-001 Mature Admission Package Builder Scope

CR157 应定义 mature admission package builder 的产品范围。Builder 后续实现应只消费研究产物引用和验证证据引用，不读取真实数据湖、不触发 provider、不导入 QMT、不调用 gateway，也不发布 registry/store/catalog。

成功标准：

- 字段清单固定为 11 类：strategy id、run id、data release ref、factor model validation report ref、mature research package ref、runner offline preflight ref、observation plan ref、risk policy ref、evidence index ref、blocked reasons、authorization flags；11/11 缺一即 blocked。
- 缺失 P0 evidence、`typed_unavailable:*`、placeholder 或 runtime flags 冲突时 fail-closed。
- 输出不能声明 simulation-ready、paper-ready、live-ready 或 trading-ready。

### REQ-CR157-002 Stage 2/Stage 3 Handoff Hardening

CR157 应把现有历史命名中的 `stage3` 兼容对象解释清楚：Stage 2 输出框架支撑和 handoff contract，Stage 3 研究机生产真实研究证据，Stage 4 才是观察候选审查。

成功标准：

- Handoff 文档或 schema 必须包含输入、输出、证据、边界、下一阶段消费方式和降级策略。
- 任一真实 runtime 或交易需求必须另开 authorization gate。

### REQ-CR157-003 Research Evidence Index Traceability

准入包必须能从轻量 package 引用追溯到完整研究证据，不复制大型证据正文。

成功标准：

- Evidence index 固定包含 7 类引用：data release ref、manifest ref、metric refs、lineage refs、risk policy ref、validation report ref、runner offline preflight ref；7/7 缺一即 blocked。
- blocked / unavailable 必须结构化表达，不能通过空字符串或自然语言隐藏。

### REQ-CR157-004 Fail-Closed No-Runtime Guard

CR157 必须延续 Stage 2 no-lake/no-runtime 防线。

成功标准：

- 禁用面包括 NAS access、provider fetch、credential/env read、lake write、catalog/store/registry write、QMT/MiniQMT/xtquant、gateway、simulation、paper/live trading、broker/order/account 操作、Git remote write、publish。
- 禁用计数非 0 时阻断，并给出 machine-readable reason。

### REQ-CR158-001 Unified Adapter Scope

CR158 必须把 CR157 延后的 event strategy adapter 与 ML strategy adapter 作为一个统一 adapter Change Package 推进。统一不等于强行相同：共享 core 只承载 strategy type、input refs、output signal refs、evidence refs、blocked reasons、authorization flags 和 handoff refs；event-only 与 ML-only 字段必须通过 type-specific extension 显式表达。

成功标准：

- CP2 Decision Brief 必须列出 3 个 scope 选项：统一 event+ML、只做 event、只做 ML；推荐方案为统一 event+ML。
- CP3 HLD 必须明确 shared core 字段不少于 7 类，type-specific extension 至少区分 event 与 ML 两类。
- 任何 Story 或 schema 不得把 event-only 字段设为 ML 必填，或把 ML-only 字段设为 event 必填。

### REQ-CR158-002 Event Strategy Adapter Contract

Event adapter 应将离散事件类策略输入转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static event refs，不允许接入真实 feed、live listener、provider 或 gateway。

成功标准：

- Event adapter contract 至少包含 6 类字段：event source ref、event time ref、event payload schema ref、alignment policy ref、signal output ref、blocked reason ref。
- 真实 event feed、live listener、provider fetch、gateway call 计数必须为 0。
- 缺少 event source ref、alignment policy ref 或 signal output ref 时必须 fail-closed。

### REQ-CR158-003 ML Strategy Adapter Contract

ML adapter 应将模型类策略的训练/验证/预测引用转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static model artifact refs，不允许训练真实模型、调用外部模型服务或写 model registry。

成功标准：

- ML adapter contract 至少包含 7 类字段：training snapshot ref、feature set ref、label policy ref、model artifact ref、validation report ref、prediction signal ref、blocked reason ref。
- real model training、external model service、model registry write/promotion 计数必须为 0。
- 缺少 training snapshot ref、validation report ref 或 prediction signal ref 时必须 fail-closed。

### REQ-CR158-004 Evidence Index Typed Extensions

CR158 必须延续 CR157 refs-only evidence index 基线，新增 event/ML typed extension 时只能记录引用和短元数据，不复制报告正文、模型文件、event payload 全文、diff、transcript 或大型矩阵正文。

成功标准：

- Event extension 至少能引用 event source、alignment policy 和 signal output refs。
- ML extension 至少能引用 training snapshot、model artifact、validation report 和 prediction signal refs。
- Evidence index 中大型正文复制计数必须为 0。

### REQ-CR158-005 No-Runtime Authorization Guard

CR158 的任何 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 approve 都不授权真实运行时或生产写入。

成功标准：

- 禁用面包括 real event feed、real model training、external model service、model registry write、provider fetch、NAS access、credential/env/session read、lake write、catalog/store/registry/prediction write、QMT/MiniQMT/xtquant/gateway、simulation/paper/live/trading/broker、external framework run、Git remote write、publish。
- CP7 evidence 必须报告禁用操作计数；每个禁用计数必须为 0。
- 任一禁用计数非 0 时，CP7 不得 PASS。

### REQ-CR158-006 CP2/CP5 Gate Enforcement

CR158 是 architecture-major product-scope CR，必须保留 CP2 / CP3 / CP5 / CP8 人工门禁。

成功标准：

- CP2 approved 前不得创建 dev-ready Story、LLD 或实现。
- CP5 approved 前不得修改 adapter source/test implementation。
- CP2 approve 只授权进入 solution-design；不授权 implementation、runtime 或 publish。

### REQ-CR158-007 Release Wording Boundary

CR158 的 release notes、verification report 和 component docs 必须明确区分 local/static/fixture adapter readiness 与 production/runtime readiness。

成功标准：

- CP8 release wording 必须包含 “not authorized” 清单，覆盖真实 feed、训练、registry、runtime、trading、publish。
- 不得出现 simulation-ready、paper-ready、live-ready、trading-ready、production-ready 或 registry-published 声明，除非后续独立授权 CR 明确批准。

### REQ-CR160-001 Stage 4 Observation Review Workflow Contract

CR160 必须补齐 CR157 预留但未定义的 Stage 4 observation review 语义，使 Stage 3 mature research package 到 Stage 5 paper/simulation admission 之间有可审查、可失败、可路由的 contract。

成功标准：

- HLD 必须定义 6 个 Stage 4 design objects：ObservationReviewInput、EvidenceProfile、AdmissionReadiness、ObservationDecision、EscalationRoute、AuthorizationBoundary。
- 每个 design object 必须列出输入、输出、失败路径和下一阶段消费方式。
- 缺少 observation plan instance、admission package ref、research evidence refs 或 authorization boundary 时必须 fail-closed。

### REQ-CR160-002 Observation Plan Template and Instance Boundary

CR160 必须区分 observation plan template 与 observation plan instance，避免把模板文档误当成已审查实例。

成功标准：

- Observation plan template 至少定义 5 类内容：观察周期、检查点频率、跟踪指标、退出条件、Stage 1/2/3 evidence refs 要求。
- Stage 3 产物必须提供 observation plan instance ref；仅有 template ref 时 Stage 4 review 不得通过。
- Review workflow 必须审查 instance 对 template 的合规性，并在不合规时输出 blocked 或 needs_review。

### REQ-CR160-003 Layered Observation Review Checklist

Observation review checklist 必须覆盖数据基础、研究生产、研究机 admission 和横切授权边界，不能只审 Stage 3 统计结果。

成功标准：

- Stage 1 层至少 5 项，覆盖 PIT、universe、lineage、dataset refs、leakage policy。
- Stage 2 层至少 5 项，覆盖 factor methodology、evaluation refs、typed_unavailable、blocked reasons、evidence index。
- Stage 3 层至少 5 项，覆盖 statistical gate、out-of-sample、economic significance、capacity/impact、rerun consistency。
- 横切层至少 5 项，覆盖 operation counters、authorization boundary、no-overclaim wording、follow-up route、human review outcome。
- 每个 checklist item 的结果枚举必须是 PASS、NEEDS_REVIEW、FAIL 或 N/A。

### REQ-CR160-004 Fail-Closed Evidence Lane Decision Table

CR160 必须用 evidence lane + admission readiness 的矩阵表达 Stage 4 结果，默认 fail-closed。

成功标准：

- Evidence lane 必须覆盖 4 类：`contract_only`、`real_data_validated`、`runtime_authorized`、`unknown`。
- `contract_only` lane 的 readiness=true 路径数量必须为 0。
- `unknown` lane 必须 blocked 或 needs_review，不能输出 paper/simulation readiness。
- `real_data_validated` lane 仍需 admission 非阻断；real-data evidence 不等于 runtime authorization。

### REQ-CR160-005 CR155 Blocked Seed Classification

CR155 daily baseline artifact 必须作为 fail-closed 反例样本被 CR160 workflow 正确分类。

成功标准：

- CR155 既有 evidence 必须显示 admission package `FAIL` 或 `BLOCKED`、`paper_candidate=false`、blocked gates 可追溯。
- CR160 classification 必须输出 `blocked_admission_failed`。
- Rerun consistency PASS 不得提升 CR155 evidence 等级，也不得绕过 admission FAIL。
- CR160 不得执行新的 real lake read/write；只消费既有 CR155 evidence ref。

### REQ-CR160-006 Design-Only Authorization Boundary

CR160 是 product-scope / requirement-change 的纯设计 CR，不是 runtime 或代码实现 CR。

成功标准：

- CP8 approve 不授权代码实现、schema/checker、strategy remediation、CR155 晋级、新 real lake read/write、NAS/provider/credential access、broker/order/trading、QMT/MiniQMT/xtquant/gateway、paper/simulation/live/runtime、catalog/store/registry/model/prediction write、Git remote write、deployment、release execution 或 publish。
- Release wording 必须明确 `READY_WITH_RISK` 只表示 Stage 4 design/gate contract 可用作后续基线。
- 所有 Stage 5 paper/simulation/live/runtime 动作必须另起 CR 和授权 gate。

### REQ-CR160-007 Product Baseline Traceability Refresh

CR160 CP0/CP2 已承诺刷新产品基线；CP8 关闭前必须补齐该追溯链。

成功标准：

- 6 个产品文档必须增量更新：`USE-CASES.md`、`REQUIREMENTS.md`、`SCENARIOS.yaml`、`TEST-MATRIX.md`、`MVP-SCOPE.md`、`BACKLOG.md`。
- `DF-CR157-003` 与 `BL-CR157-003` 必须标记为 promoted to CR160，且旧 CR157/CR158 基线不得被删除。
- 产品文档必须保留修订记录，并把 product baseline refresh 作为 CP8 关闭前置条件记录到 CP8 checkpoint。

### REQ-CR161-001 Seven-Object Admission Evidence Contract

- 当前产品基线必须枚举 `ExperimentFamilyManifest`、`MultipleTestingEvidence`、`DataSnoopingEvidence`、`OverfitRiskEvidence`、`WalkForwardEvidence`、`EconomicCostEvidence` 和 `CapacityLiquidityEvidence`。
- 每个对象必须能追溯其覆盖的 C1-C4 blocker、availability 语义、现有 gate 集成点和后续 evidence producer；不要求当前切片提供计算实现。

### REQ-CR161-002 Typed-Unavailable Fail-Closed Ceiling

- 缺 trial lineage、trial count、parameter-search lineage、raw p-values、fold metrics、成本输入或容量输入时，相关 mandatory evidence 必须是 `typed_unavailable` 并阻断 admission。
- `typed_unavailable` 不是 PASS、不是计算成功、不是风险接受，也不得降格为静默 warning。

### REQ-CR161-003 Existing-Gate Integration and CR155 Regression

- CR161 evidence availability 只补充 CR151 statistical gate 和 CR154 相关控制面；不得创建竞争性 admission gate。
- CR155 只能作为 negative regression：即使它缺少新 C1/C2 可计算输入，也必须保持 `blocked`，不得重建或推断缺失历史数据。

### REQ-CR161-004 No Computed-Proof or Runtime Overclaim

- 本基线只声明 evidence-computable 或 `typed_unavailable` fail-closed 的判别边界；当前已交付的是后者。
- FDR/PBO/DSR、walk-forward/OOS fold-level 指标、真实 market impact/TCA、capacity/liquidity sizing、真实数据访问和任何 runtime/trading 结论均不由本需求授权。

### REQ-CR161-005 Deferred Evidence-Producer Traceability

- `FU-CR161-001..006` 保持后续追溯链，分别覆盖 trial-lineage instrumentation、统计/数据偷窥/过拟合计算、walk-forward/OOS producer、economic/capacity producer、集成验证和 verifier-lane resilience。
- `FU-CR162-001` 只跟踪通用 CP8 product-baseline-refresh checker；它不改变 CR162 文档纠错的 design-only 边界。
- `FU-CR161-001` 由 CR163 承接为 active product-scope CR；`FU-CR161-002..006` 和 `FU-CR162-001` 继续保持 candidate。
- CR163 只解决 experiment-family raw lineage 事实来源，不隐式启动其余 producer。

### REQ-CR163-001 Pre-Search Family Lifecycle

- 首个 candidate-producing trial 开始前必须已有 family declaration；验证证据必须能证明 declaration timestamp / sequence 早于任何 trial start。
- family 生命周期至少区分 declared、recording、sealed、superseded 或 CP3 确认的等价状态；最终名称由 CP3 决定。
- sealed family 的 declared search space、trial membership 和 selection policy 不得原地缩小。

成功标准：P0 inventory 的 2/2 生产链均在 first trial 前声明 family；post-hoc declaration 验证 100% blocked。

### REQ-CR163-002 Append-Only Trial / Attempt / Selection Lineage

- 每个 trial 必须有稳定 trial identity；每次执行尝试必须有独立 attempt identity，并回链 family、trial、run、experiment 与 artifact refs。
- success、failed、cancelled、excluded 状态及 selection / rejection reason 均不得因最终候选选择而删除。
- 同一事件 identity 的完全相同重复写可幂等；同 identity 不同内容必须冲突并 blocked。

成功标准：声明的每个 trial 至少有 1 个 attempt 或明确的 never-started terminal reason；0 个未解释孤儿 trial；0 个无法回链的 selection。

### REQ-CR163-003 Raw Trial Count Semantics

- 不同参数组合或不同 seed 视为不同 trial，即使其余字段相同。
- 同一 trial 的 retry 产生新 attempt，不增加 `raw_trial_count`。
- failed、cancelled、excluded trial 仍属于 declared/search family 并计入 raw count；重复 delivery 不重复计数。

成功标准：`raw_trial_count = count(distinct stable_trial_id)`；seed A/B 产生 2 个 trial；同 trial 3 次 retry 仍为 1 个 raw trial、3 个 attempts；manifest count 与事件重算值不一致时 100% blocked。

### REQ-CR163-004 Deterministic Seal and Supersession

- seal 必须基于规范化内容与确定性排序，同一逻辑内容重复计算产生相同 content hash。
- sealed version immutable；任何纠错创建新 version，提供 `supersedes_ref` / reason，并保留旧 ref/hash。
- consumer 默认解析最新合法未撤销版本，但审计者仍能验证完整 version chain；最终对象名与 artifact 路径留给 CP3。

成功标准：相同 fixture 重复 seal 10 次得到 1 个 hash；原 sealed artifact 原地修改次数为 0；断链、循环或 hash mismatch 100% blocked。

### REQ-CR163-005 Frozen Candidate-Producer Inventory

- P0 分母固定为 **2 条去重 producer chains / 4 个 instrumentation mappings**：`CPI-CR163-001..004`；两个 public/legacy entrypoints 和两个 direct construction hooks 都有 mapping。
- wrapper 与 hook 属同一 producer chain，不得按调用层级重复增加 trial count。
- anomaly factor discovery、compatibility adapter、admission consumer、单次-run contract 和未存在的 real ML/event runner 均必须显式 excluded/N/A，而非静默漏测。

成功标准：2 条 producer chains 均被覆盖，P0 instrumentation mapping 4/4、coverage 100%；included path 未映射数 0；excluded path 均有理由和重访条件。

### REQ-CR163-006 Existing-Gate Availability Integration

- `ExperimentManifest` 保持单次-run object；family lineage 以独立 lifecycle 通过 `run_id`、`experiment_id` 和 artifact refs 连接。
- 对既有 admission consumer 只暴露 `present / typed_unavailable / not_applicable_with_reason / blocked` availability、lineage ref、raw count 与验证状态；不得新建竞争 gate family。
- 本 CR 中 `effective_trial_count` 必须保持 `typed_unavailable`，其 ref 与 method 为空；不得以 raw count 替代。
- 未来原生 instrumented run 仅在 seal、completeness、reference integrity、count 与 tamper checks 全 PASS 后，`ExperimentFamilyManifest` 才可 `present`；未 instrumented path 为 `typed_unavailable`；invalid/incomplete/tampered lineage 为 `blocked`。
- CR163 只使 C1 raw-lineage input-ready；缺少 raw p-values、effective-trial method 和 statistical producer 时，C1 multiple-testing/data-snooping/overfit evidence 仍不可计算。

成功标准：present 只在 seal、completeness、reference integrity、count 与 tamper checks 全 PASS 时出现；未 instrumented fixture 100% typed_unavailable；invalid/tampered fixture 100% blocked；effective count 的 available 声明数为 0；C1 computed-evidence 声明数为 0。

### REQ-CR163-007 Completeness, Tamper and Recovery Validation

- validator 必须覆盖 family declaration、trial/attempt/selection referential integrity、duplicate identity、raw count、seal hash、version chain 和 missing instrumentation。
- 失败后允许基于 append-only correction + superseding seal 恢复；不得删除失败事件或覆盖旧 sealed version。
- 所有 blocked reason 都必须 machine-readable 并指向 evidence ref 或缺失字段。

成功标准：正向、missing、duplicate-conflict、count-mismatch、tamper、broken-supersession 六类 fixture 均有确定结论；五类负向 fixture 5/5 blocked。

### REQ-CR163-008 Authorization and CR155 Regression Boundary

- 本 CR 不授权 real lake/NAS/provider/credential、runtime、simulation/paper/live、broker/trading、external framework、remote write、publish 或 catalog pointer mutation。
- 不授权 statistical correction、effective-trial computation、historical lineage reconstruction；不得用推断 backfill 生成 `present`。
- CR155 仅作为 negative regression，保持 blocked；新 lineage contract、rerun consistency 或 unavailable evidence 均不得提升它。

成功标准：所有 forbidden operation counters 为 0；CR155 regression 1/1 保持 blocked；runtime-ready / statistical-proof overclaim 数为 0。

### REQ-CR164-001 MVP Statistical Method Set

- SGQ-CR164-001 已确认 A：BH + WRC/SPA + PBO/CSCV + DSR；每种方法独立表达 `present / typed_unavailable / blocked`。
- positive statistical-significance、performance-robustness、Sharpe/IC reliability claim 只能消费其 claim-relevant mandatory methods；不得以任一方法 PASS 形成 OR-pass。
- Bonferroni/BH 现有 anomaly helper 只是可复用事实，不等于 strategy-family 方法或 schema 已获批准。

成功标准：CP2 method matrix 对 4/4 方法逐项记录 required/deferred、输入、claim、不可用语义与切换条件；未确认前 `ready_for_design=false`。

### REQ-CR164-002 Validation-Bound Family and Input Identity

- 所有 method evidence 必须绑定 CR163 trusted projection 的 family ref、target hash、raw trial count 与候选 membership；serialized/untrusted projection、hash mismatch 或 manual count mismatch 必须 blocked。
- candidate metric、p-value、return path 与 split 输入必须能回链同一 family/trial identity；不得混用不同 family 或选择后缩小分母。

成功标准：完整 fixture 的 lineage/input refs 100% 一致；missing lineage 为 typed_unavailable；family/hash/count/membership mismatch 5/5 负向 fixture blocked。

### REQ-CR164-003 Method-Specific Computable Evidence

- BH evidence 至少记录 raw/adjusted p-values、alpha、candidate count、rejected count、method/version 与 provenance。
- WRC/SPA evidence 至少记录候选集合、benchmark/null、对齐 return matrix、resampling policy、seed/config 与 corrected significance result。
- PBO/CSCV evidence 至少记录候选集合、组合 split 定义、train/test ranking或 loss、有效 split count 与 PBO。
- DSR evidence 至少记录 observed Sharpe、sample length、skew、kurtosis、trial-count provenance、approved trial-count mode 与 DSR。

成功标准：每个已批准方法 required fields 100% 存在且有限；缺字段不产生 present evidence。

### REQ-CR164-004 Quantitative Input Sufficiency

- SGQ-CR164-003 已确认 A：BH/WRC-SPA 至少 2 个完整候选；PBO/CSCV 至少 4 个完整候选和 4 个有效组合 splits，且每 split 的 train/test 观察均非空；DSR 至少 2 个 trials、sample_length >= 30、收益方差 > 0。
- 所有方法输入必须是有限值；空数组、NaN、Inf、零方差、无法对齐的 return path、缺失 split side 或低于阈值均不得计算正向证据。

成功标准：每个方法的下限、比较符号、required fields 和失败状态在 CP2 可度量；低阈值与退化 fixture 100% fail-closed。

### REQ-CR164-005 Determinism and Numerical Boundary

- 相同规范化 fixture、方法版本、参数、seed/config 必须生成相同 evidence summary；排序与 hash 输入必须确定。
- 浮点输出必须有限并满足方法定义域：p/q/PBO 在 [0,1]；count 为正整数；sample length、split count 与 candidate count 与输入一致。

成功标准：同一 fixture 10 次计算只产生 1 个摘要 hash；NaN、Inf、负 count、长度不一致、越界概率、零方差 6 类负向 fixture 6/6 blocked 或 typed_unavailable。

### REQ-CR164-006 Method Disagreement Projection

- 每个方法原始结论保留；聚合层不得改写或丢弃不利结果。
- claim-relevant mandatory 方法任一 BLOCKED/typed_unavailable 时相关 claim blocked；任一 FAIL 时不得由其他 PASS 提升；仅非 mandatory 方法差异可进入 needs_review 且必须有 reason/ref。

成功标准：BH PASS + WRC FAIL、PBO PASS + DSR unavailable、单一 method PASS + 另一 mandatory blocked 三类 fixture 均不输出 clean PASS。

### REQ-CR164-007 Existing-Consumer Integration

- method evidence 投影到既有 `strategy_admission_statistical_gate`、CR154 Gate 1 slots 与 `strategy_admission_package`；不得新建竞争 admission gate family。
- consumer 只能保持或恶化上游 admission status；evidence ref 不得改变 runtime authorization flags。

成功标准：3/3 consumer paths 可回链同一 method refs；blocked input 3/3 保持 blocked；新增 competing gate count 为 0。

### REQ-CR164-008 Effective-Trial Claim Ceiling

- SGQ-CR164-002 已确认 A：CR164 MVP 不定义 effective-trial estimator，`effective_trial_count`、ref、method 保持 typed_unavailable/空；raw count 不得代替它。
- CP3 schema 必须声明 `dsr_input_method=raw_trial_count`、lineage provenance 与 effective-count non-alias limitation。
- DSR 是否可在 raw-count mode 下形成独立 evidence，与现有 Gate-1 是否允许 deflated-performance claim 必须分开表达；现有 consumer 要求 effective count时保持 blocked。

成功标准：未获批 estimator 下 effective-count available 声明数为 0；raw-to-effective alias 数为 0；受影响 claim 的错误 PASS 数为 0。

### REQ-CR164-009 Compatibility, Authorization and Regression

- SGQ-CR164-004 已确认 A：UC-58 multifactor 是当前实现主体；UC-59 ML 与 UC-60 event 仅消费 compatibility contract，缺相同 sealed-family/statistical inputs 时 fail-closed。
- 不授权真实研究批次、production/lake/NAS/provider/credential、external framework、broker/trading、publish 或 remote write。
- CR155 只消费既有 evidence refs，始终保持 blocked；不得回填 p-values、returns、splits、effective counts 或统计结论。

成功标准：UC-58/59/60 compatibility cases 3/3 有确定结论；forbidden operation counters 全为 0；CR155 1/1 blocked；runtime-ready/statistical-proof overclaim 数为 0。

## CR164 Quantitative Acceptance Criteria

| AC ID | 指标 | 目标值 | 失败行为 | 来源 |
|---|---|---:|---|---|
| QAC-CR164-001 | selected-method required-input coverage | 100% | 任一 required input 缺失则该方法不得 present | SGQ-CR164-001/003 |
| QAC-CR164-002 | family/ref/hash/raw-count binding coverage | 100% | 缺失为 typed_unavailable；mismatch/tamper 为 blocked | REQ-CR164-002 |
| QAC-CR164-003 | candidate/raw-ledger/method-input count difference | 0 | 任一差异 blocked，不允许 post-selection shrink | REQ-CR164-002/004 |
| QAC-CR164-004 | enumerated negative-fixture fail-closed hit rate | 100% | 任一 false PASS 阻断 CP7 | REQ-CR164-004/005/006 |
| QAC-CR164-005 | same-fixture deterministic reruns | 10 runs -> 1 summary hash | hash 漂移 blocked | REQ-CR164-005 |
| QAC-CR164-006 | orphan method-evidence references | 0 | orphan ref blocked | REQ-CR164-003/007 |
| QAC-CR164-007 | consumer projection coverage | 3/3：UC-58 multifactor + UC-59 ML compatibility + UC-60 event compatibility | 缺 consumer projection 阻断对应 claim | REQ-CR164-007/009 |
| QAC-CR164-008 | CR155 negative-regression preservation | 1/1 blocked | 状态提升即 FAIL | REQ-CR164-009 |
| QAC-CR164-009 | forbidden-operation counters | 每项 0 | 任一非 0 blocked | REQ-CR164-009 |
| QAC-CR164-010 | runtime/statistical-proof overclaims | 0 | 任一 overclaim blocked | REQ-CR164-008/009 |

QAC-CR164-007 的 3/3 是产品 consumer coverage，不代表 UC-59/60 implementation scope。所有指标只由后续 fixture/static 验证证明；本阶段不执行统计计算。

## CR164 CP3 Design Obligations

| Obligation ID | 义务 | CP2 已冻结的不变量 | CP3 待决策内容 |
|---|---|---|---|
| DO-CR164-001 | DSR input semantics | effective count typed_unavailable；raw 不得别名 effective | schema 写入 `dsr_input_method=raw_trial_count`、lineage provenance、limitation/reason code |
| DO-CR164-002 | WRC/SPA bootstrap | WRC/SPA 属于 MVP；结果须确定性可复跑 | stationary bootstrap 的 block-length mode：`automatic_politis_romano_1994` vs `fixed_window`，参数/seed provenance、切换条件 |
| DO-CR164-003 | Method disagreement | claim-relevant mandatory methods 无 OR-pass；FAIL/BLOCKED 不得被 PASS 覆盖 | 完整 priority/final-status decision table 与 reason-code mapping |

## Non-Functional Requirements

| NFR ID | 维度 | 要求 | 度量 |
|---|---|---|---|
| NFR-CR157-001 | 可追溯性 | Package 不复制大证据正文，只引用 evidence index。 | P0 evidence refs 覆盖率 100%。 |
| NFR-CR157-002 | 安全性 | 禁用外部运行时和真实交易。 | 禁用计数必须为 0。 |
| NFR-CR157-003 | 可测试性 | 所有 P0 场景可用 fixture/static/no-lake 方式验证。 | P0 scenario 覆盖率 100%。 |
| NFR-CR157-004 | 可扩展性 | Adapter 合同不阻断 event/ML 后续扩展。 | `docs/product/BACKLOG.md` 必须保留 2 个 adapter follow-up：`BL-CR157-001` 和 `BL-CR157-002`。 |
| NFR-CR158-001 | 可追溯性 | Event/ML adapter evidence 只引用 refs，不复制大型正文。 | 大型正文复制计数为 0；P0 refs 覆盖率 100%。 |
| NFR-CR163-001 | 完整性 | 冻结 producer inventory、trial/attempt/selection 与 seal chain 全部可重算。 | P0 inventory mapping 4/4；未解释 orphan 与 count mismatch 均为 0。 |
| NFR-CR163-002 | 确定性 | 相同规范化 lineage 内容产生相同 seal。 | 同一 fixture 连续 seal 10 次仅产生 1 个 content hash。 |
| NFR-CR163-003 | 安全与权限 | fixture/static 验证不访问任何禁止 runtime/data/external write。 | 所有 forbidden operation counters 为 0；任一非 0 则 blocked。 |
| NFR-CR163-004 | 可维护性 | sealed 修正以 supersession 追加，保留旧版本审计。 | sealed artifact 原地修改数 0；有效 supersession chain 覆盖率 100%。 |
| NFR-CR158-002 | 安全性 | Event/ML adapter 实现必须保持 no-runtime/no-publish。 | 禁用操作计数全部为 0。 |
| NFR-CR158-003 | 可演进性 | Shared core 与 type-specific extension 分离。 | event-only 与 ML-only 字段互不成为对方必填项。 |
| NFR-CR158-004 | 可测试性 | 所有 P0 CR158 场景可用 fixture/static 方式验证。 | P0 scenario 覆盖率 100%。 |
| NFR-CR160-001 | 可追溯性 | Stage 4 review 必须可回链 Stage 1/2/3 refs、CR155 seed evidence 和产品基线 promotion。 | CR160 P0 requirement / scenario / matrix 覆盖率 100%；6/6 产品文档刷新。 |
| NFR-CR160-002 | 安全性 | Stage 4 design closure 不得被误读为 runtime、paper、simulation 或 live 授权。 | 禁用操作授权数量为 0；not-authorized 清单覆盖 12 类以上。 |
| NFR-CR160-003 | 可测试性 | Checklist、decision table 和 CR155 seed classification 必须可人工复核。 | Checklist item 数 >= 20；CR155 classification evidence ref 1 个以上。 |
| NFR-CR164-001 | 可追溯性 | 每个 method result 绑定 family、输入、参数、方法版本与 evidence ref。 | 已批准方法 provenance 字段覆盖率 100%；orphan ref 数为 0。 |
| NFR-CR164-002 | 确定性 | 相同规范化 fixture 的计算摘要稳定。 | 重复 10 次只产生 1 个摘要 hash。 |
| NFR-CR164-003 | 数值安全 | 非有限、退化、长度/计数不一致与越界值 fail-closed。 | 6 类负向 fixture 6/6 不产生 present/PASS。 |
| NFR-CR164-004 | 安全与权限 | 本地 fixture/static 验证不执行禁止操作。 | 所有 forbidden operation counters 为 0；任一非 0 则 blocked。 |

## Open Decisions

| 决策 ID | 类型 | 问题 | 推荐方案 | 状态 |
|---|---|---|---|---|
| DQ-CP2-CR157-FIRST-SLICE | scope | CR157 first slice 是否纳入 event/ML adapters？ | 不纳入；event/ML adapters 作为 backlog 或后续 CR。 | pending user review |
| DQ-CP2-CR158-UNIFIED-SCOPE | scope | CR158 是否把 event 与 ML adapter 合并为一个统一 adapter CR？ | 合并为一个 CR，shared core + type-specific extension。 | pending user review |
| DQ-CP2-CR158-NO-RUNTIME | security | CR158 CP2 approve 是否授权真实 feed、训练、registry、runtime、trading或 publish？ | 不授权；只允许 local/static/fixture 设计和后续验证。 | pending user review |
| DQ-CP2-CR158-GATE-SEQUENCE | implementation | CP2 approve 后是否允许直接实现？ | 不允许；CP2 后进入 CP3 HLD，CP5 批准后才实现。 | pending user review |
| DQ-CP2-CR160-EVIDENCE-PROFILE | scope | CR160 observation review 输入是 contract-level evidence 还是 real-data evidence？ | 双轨 fail-closed；contract lane 不能输出 paper/simulation readiness。 | approved |
| DQ-CP2-CR160-DELIVERABLE-SHAPE | implementation | CR160 是设计交付还是代码实现？ | 纯设计交付；CP4/CP5/CP6 N/A，CP7/CP8 做设计验证和发布就绪。 | approved |
| DQ-CP8-CR160-004 | scope / traceability | CP8 关闭前是否必须补齐产品基线刷新？ | 必须补齐 6 个产品文档，作为 CR160 关闭前置条件。 | resolved 2026-07-09 |
| DQ-CP2-CR164-METHOD-SET | scope | MVP 是否包含 BH + WRC/SPA + PBO/CSCV + DSR？ | 四类均纳入并逐方法 fail-closed。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-EFFECTIVE-TRIAL | scope / risk | 是否在本 CR 计算 effective trial count？ | 不计算；保持 typed_unavailable，防止未经批准的 estimator。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-SUFFICIENCY | risk_acceptance | 方法充分性下限采用推荐值还是更严格值？ | 采用方法特定推荐下限，后续 CP3 可在不降低下限的前提下收紧。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-COMPATIBILITY | scope | UC-59/60 是实现对象还是 compatibility-only？ | UC-58 实现，UC-59/60 compatibility-only。 | resolved-A 2026-07-12 |
| DQ-CP2-CR166-SCOPE | scope | 是否批准 fixture/static C2 foundation、8 类 P0 与 Stage 3 claim ceiling？ | 批准；真实 fold/OOS 数据与 Stage 3 启动另起 CR。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-EXTENSION | architecture-boundary | 是否只预留 C3/C4 versioned typed component 扩展点？ | 只冻结兼容约束，不实现或验证 C3/C4 计算。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-COMPATIBILITY | scope | event 是否与 daily/ML 同列 P0？ | daily + ML 为 P0；event 为 P1 applicability，语义未冻结时 N/A。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-AUTHZ | security | CP2 是否授权真实数据/runtime/外部系统或实现？ | 不授权；CP2 后只进入 CP3，CP5 后才可 fixture/static 实现。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR168-METHOD | scope / methodology | C3 是否包含透明 impact approximation？ | 包含 fee/tax/spread/slippage/impact 分解，但 impact 只使用显式静态参数；备选为延后 impact。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-C3-C4 | architecture-boundary | 是否冻结 C3/C4 最小共享 header？ | 冻结最小共享 header；C4 专属字段 reserved，C4 calculator=0。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-GATE4 | integration-boundary | existing-gate integration 做到何种粒度？ | 只做 1 条 C3-to-Gate-4 compatibility projection；C4 reserved/not-built/typed_unavailable 映射为三个 refs absent；CR168 adapter 用精确 8-key denylist、strict allowlist、调用前拒绝和调用后非 PASS 断言局部封堵 reason 逃逸；不修改或宣称全局修复 canonical Gate 4。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-FIXTURE | compatibility | fixture 适用面是什么？ | 2 族：daily multifactor synthetic + daily/ML multi-strategy-type compatibility；event N/A/deferred。 | resolved-approved 2026-07-14 |
| CP2-CR171-DQ-ROUTE | architecture | 哪条 Stage 3 evidence route 获准进入后续设计？ | C1-C4 real-producer；需单独 Real-Evidence Activation CR 才可 computation。 | OPEN，待 CP2 |
| CP2-CR171-DQ-VERIFIER | risk acceptance | FU-006 是 entry blocker 还是临时 event-bounded waiver？ | event-bounded waiver；在 real-evidence admission PASS/PASS_WITH_RISK 前或 Stage 3 exit gate 前失效。 | OPEN，待 CP2 |
| CP2-CR171-DQ-READ-SCOPE | runtime authorization | 哪个 release/dataset/date/read identity/output directory 可在后续受控读取中使用？ | scoped research-data-lake read-only，且 deny credentials/provider/write/catalog/runtime/trading。 | resolved-approved 2026-07-15; no read authorization |

## CR166 Walk-forward / OOS Producer Requirements

| REQ ID | 标题 | 优先级 | 可验证要求 |
|---|---|---|---|
| REQ-CR166-001 | Typed fold input contract | P0 | fold manifest、split policy、train/validation/OOS bounds、purge/embargo、metrics、lineage refs 7/7 字段族有 schema 与 validation result。 |
| REQ-CR166-002 | Temporal and leakage boundary | P0 | 时间逆序、purge 缺失、embargo 不足 3/3 fail-closed，reason code 不为空。 |
| REQ-CR166-003 | Fold/metric sufficiency | P0 | 缺 fold、metric 缺失、NaN/Inf 3/3 不产生 present/PASS；valid fold 分母与 pass-rate 可重算。 |
| REQ-CR166-004 | Lineage integrity | P0 | lineage 缺失、ref/hash/membership 不一致 100% typed_unavailable 或 blocked；orphan refs=0。 |
| REQ-CR166-005 | Deterministic C2 envelope | P0 | 相同规范化 fixture 10 次只产生 1 个 canonical hash；header + versioned typed component 保持稳定。 |
| REQ-CR166-006 | Future C3/C4 compatibility | P0 design constraint | 支持注册式 versioned C3/C4 component 扩展；未知/未注册 component 不能满足 mandatory evidence 或产生 PASS；当前 C3/C4 calculators=0。 |
| REQ-CR166-007 | Existing-consumer projection | P0 | statistical gate、cross-strategy reliability gate、StrategyAdmissionPackage 3/3 使用同一 C2 refs/availability/reasons；不新建 gate。 |
| REQ-CR166-008 | Strategy compatibility | P0/P1 | daily multifactor 与 ML purged-embargo compatibility 2/2；event 在 CP3 完成 applicability decision，未冻结语义时为 N/A 而非假覆盖。 |
| REQ-CR166-009 | Deny-default authorization and Stage claim | P0 | external/real-data ref 解引用=0，forbidden counters=0；Stage 2 保持 complete，Stage 3 started/runtime-authorized/real-evidence-available 均为 false。 |

## CR166 Quantitative Acceptance Criteria

| QAC | 指标 | 目标 |
|---|---|---:|
| QAC-CR166-01 | P0 fail-closed 类别覆盖 | 8/8 |
| QAC-CR166-02 | daily + ML P0 fixture 族 | 2/2 |
| QAC-CR166-03 | event applicability 决策 | 1/1；实现可为 N/A |
| QAC-CR166-04 | typed input 字段族 | 7/7 |
| QAC-CR166-05 | temporal/leakage 负向类 | 3/3 blocked |
| QAC-CR166-06 | lineage negative coverage | 100% fail-closed，orphan=0 |
| QAC-CR166-07 | deterministic reruns | 10 次→1 hash |
| QAC-CR166-08 | existing-consumer projection | 3/3 |
| QAC-CR166-09 | C3/C4 calculators in CR166 | 0 |
| QAC-CR166-10 | external dereference / forbidden operations | 0 / 0 |
| QAC-CR166-11 | Stage claim flags | Stage2 complete=true；Stage3 started=false；real evidence available=false |
| QAC-CR166-12 | repository regression | CR166 新增代码路径引入失败=0；若触及 CR165 已重基线历史路径，CP7 必须逐项列出触发、归因与非回归理由 |

## CR166 CP3 Design Obligations

状态：`RESOLVED`（2026-07-13，CP3 人工批准；决策引用 `DQ-CP3-CR166-001..004`）。以下义务原文保留用于追溯，并作为 CP4/CP5 的强制设计输入。

1. 冻结 C2 envelope header、versioned component registry、canonical serialization 与 unknown-component decision table。
2. 冻结 fold 时间边界、purge/embargo 下限和 daily/ML policy 映射；event-time 语义单独作 applicability decision。
3. 显式定义 producer→三个 consumers 的调用方向、时机、输入、输出、降级与同步修改面。

## CR168 Economic Cost / Slippage / Impact Producer Requirements

### REQ-CR168-001 Versioned Typed C3 Component

- 必须复用 CR166 neutral strategy evidence envelope 和 canonical serialization/hash；不得创建平行 envelope、evidence registry 或 admission gate。
- `economic_cost@reserved` 只演进为 `1` 个 active typed C3 component，active schema version 为 `1` 个。
- 未注册/未知 component 不得满足 mandatory C3 evidence 或产生 Gate 4/aggregate PASS。

成功标准：typed C3 component 类型 `1`；active schema version `1`；平行 gate/envelope/registry `0`。

### REQ-CR168-002 Nine-Family Explicit Input Contract

输入合同必须精确覆盖 `9/9` 字段族：

1. manifest/run/strategy identity；
2. gross return 或 pre-cost performance basis；
3. trade、position change、turnover、notional basis；
4. commission/fee assumptions；
5. tax/levy assumptions；
6. spread/slippage assumptions；
7. impact model family/parameters 或 structured N/A，以及 `cost_underestimation_status`、model assumptions、structured limitations；
8. unit、currency、calendar、price/notional basis 与显式 conversion declaration；
9. lineage、provenance、authorization refs。

每个字段族必须有 required/optional/N/A/authorization 规则。C3/C4 可共享 identity、basis 与 lineage 的最小 header；capacity curve、ADV participation、liquidity sizing、alpha decay 字段由 C4 独占。

成功标准：9/9 字段族规则均可机器检查；C4 专属字段由 C3 计算的数量为 `0`。

### REQ-CR168-003 Transparent Static Cost and Impact Approximation

- 只允许使用显式传入的合成或静态参数，确定性计算 commission/fee、tax/levy、spread/slippage、impact approximation、total cost 与 gross-to-net reconciliation。
- 输出必须携带 availability/outcome、reason codes、lineage/provenance、model/version、`cost_underestimation_status`、`no_real_tca_claim=true`、structured limitations 与 canonical identity。
- impact approximation 不得被描述为真实 TCA、真实成交还原或经市场校准的 impact。

成功标准：每个 present C3 component 的成本分项、total 与 net 算术可重算；真实 TCA/market calibration claim 数为 `0`。

### REQ-CR168-004 Ten-Class Fail-Closed Validation

以下 `10/10` P0 类别必须分别形成 machine-readable reason，且不得产生 present/PASS：

1. 缺 gross/pre-cost basis；
2. 缺 trade/turnover/notional basis；
3. 缺 cost model/version；
4. 非有限值；
5. 未经策略允许的负成本或不可能数值；
6. unit/price/notional basis 不一致；
7. currency/price-basis/calendar 跨字段不一致且无显式汇率/转换声明；
8. gross/cost/net 算术不一致；
9. lineage/provenance/authorization 缺失或不一致；
10. canonical identity/hash tamper。

成功标准：10/10 类各有正交 negative fixture；false PASS 数为 `0`。

### REQ-CR168-005 Deterministic Canonical Identity

- 规范化、字段排序、数值编码、N/A 表达和 optional component 顺序必须确定。
- 同一规范化输入、schema/model version 与参数重复运行 `10` 次，必须只产生 `1` 个 canonical hash。
- 任何字段 tamper 后保留旧 hash 的输入必须 blocked；语义等价规范化输入不得因键顺序变化产生不同 hash。

成功标准：`10 runs -> 1 hash`；tamper false negative 数为 `0`。

### REQ-CR168-006 Joint Gate 4 C3 Compatibility Projection

- Gate 4 canonical 名称为 `GATE_4_CAPACITY_IMPACT`，是 C3+C4 联合门禁，不是 C3-only gate。
- CR168 的 `1` 条 compatibility projection 只能提供 C3 字段：`impact_model_family`、`impact_model_ref`、`cost_underestimation_status`、`no_real_tca_claim`。
- Envelope 中 C4 `reserved/not-built/typed_unavailable` 必须在 projection 输出中翻译为 `adv_participation_ref`、`capacity_dollars_ref`、`liquidity_sizing_refs` 三个字段 absent；不得输出与这三个字段相关的 `*_na_reason`、`*_n_a_reason`，也不得输出通用 `na_reason` 或 `n_a_reason`。
- CR168 adapter 必须按 key presence 精确拒绝以下 `8/8` 键：`adv_participation_ref_na_reason`、`adv_participation_ref_n_a_reason`、`capacity_dollars_ref_na_reason`、`capacity_dollars_ref_n_a_reason`、`liquidity_sizing_refs_na_reason`、`liquidity_sizing_refs_n_a_reason`、`na_reason`、`n_a_reason`；不得依赖私有 helper `_has_na_reason`，也不得把任意上游 mapping 直接透传。
- 任何字段级或通用 na-reason 逃逸输入必须在调用 canonical Gate 4 前由 projection `BLOCKED/REJECTED`，该路径的 canonical 调用数必须为 `0`。合法 absent-no-na-reason 路径调用后必须断言 Gate 4 不是 PASS；若出现意外 PASS，adapter 必须返回内部合同错误/阻断结果。
- 本 CR 的整改是 projection 入口局部 containment，不修改 `GATE_4_CAPACITY_IMPACT` canonical validator 或 aggregate orchestration，也不声明绕过 adapter 的未来直接调用已安全；全局语义复核归属 `FU-CR161-007` 或独立治理 CR。

成功标准：C3-to-Gate-4 projection `1`；合法 absent-no-na-reason 路径与 reason 逃逸负向路径均产生 capacity/aggregate PASS `0`；C1-C4 aggregate orchestration `0`。

### REQ-CR168-007 Multi-Strategy-Type Fixture Compatibility

- fixture 族精确为 `2/2`：1 个 daily multifactor synthetic economic-cost fixture；1 个同时验证 daily multifactor 与 ML package attach 的 multi-strategy-type compatibility fixture。
- 两种 strategy type 必须共享相同成本算术、basis、availability、reason 与 hash 语义；strategy-type 差异不得改变 C3 cost 定义。
- event-specific economic-cost 语义显式 N/A/deferred，event producer 数为 `0`。

成功标准：fixture 族 `2/2`；event-specific producer `0`；真实 model training/event feed 调用 `0`。

### REQ-CR168-008 Authorization and Claim Ceiling

- 本 CR 不授权 lake/NAS/provider/data vendor、credential/secret、真实 order/fill/quote/book/flow/ADV/liquidity、历史灌入/回填/校准、external runtime、broker/trading、catalog/store/registry pointer、publish/deploy/release/tag/push。
- CP2 approval 只允许进入 CP3 solution design，不授权实现；CP5 前不得实现。
- claim ceiling 固定：`stage2_complete=true`、`stage3_started=false`、`c3_fixture_static_foundation=false`（直至实际完成）、`real_tca_available=false`、`real_market_impact_calibrated=false`、`real_data_connected=false`、`runtime_ready=false`、`c4_calculators=0`、`event_specific_producer=false`、`cr155_promoted=false`。

成功标准：真实数据读取、真实 TCA、外部 runtime、broker/trading、Git remote write 等禁止操作计数分别为 `0`；overclaim 数为 `0`。

### REQ-CR168-009 C4, FU-007 and CR155 Regression Boundary

- C4 capacity curve、ADV participation、liquidity sizing、alpha decay calculator 保留给 `FU-CR161-005`，CR168 实现数为 `0`。
- C1-C4 aggregate orchestration、StrategyAdmissionPackage 最终聚合、existing-gate 全链路 integration 与 CR155 综合 regression/promotion decision 保留给 `FU-CR161-007`。
- CR155 formal CR lifecycle 已关闭，但现有 admission package 必须保持 `BLOCKED` 且 `paper_candidate=false`；C3 结果不得提升、解除或重解释。

成功标准：C4 calculator `0`；aggregate integration `0`；CR155 admission 状态提升 `0`。

## CR168 Quantitative Acceptance Criteria

| QAC | 指标 | 精确目标 | 失败行为 |
|---|---|---:|---|
| QAC-CR168-01 | 正式 C3 typed component 类型 | 1 | 非 1 阻断 CP7 |
| QAC-CR168-02 | active C3 schema version | 1 | 多版本并行 active 或缺版本阻断 |
| QAC-CR168-03 | 输入字段族规则覆盖 | 9/9 | 任一族无 required/optional/N/A/auth 规则阻断 |
| QAC-CR168-04 | fixture 族 | 2/2 | 任一族缺失阻断 |
| QAC-CR168-05 | P0 fail-closed 类别 | 10/10 | 任一类别 false PASS 阻断 |
| QAC-CR168-06 | deterministic reruns | 10 次 -> 1 canonical hash | hash 漂移或 tamper 漏检阻断 |
| QAC-CR168-07 | C3-to-Gate-4 compatibility projection | 1 | 缺投影或越界填充 C4 阻断 |
| QAC-CR168-08 | C4 缺失产生的 capacity/aggregate PASS | 0 | 任一 PASS 阻断 |
| QAC-CR168-09 | 新建平行 gate/envelope/registry | 0 | 任一新增阻断 |
| QAC-CR168-10 | C4 calculator | 0 | 任一实现阻断 |
| QAC-CR168-11 | event-specific producer | 0 | 任一实现阻断 |
| QAC-CR168-12 | 真实数据/TCA/runtime/broker/trading 操作 | 各 0 | 任一非 0 阻断 |
| QAC-CR168-13 | CR155 admission 状态提升 | 0 | 任一提升阻断 |
| QAC-CR168-14 | CR168 新增代码路径引入的测试失败 | 0 | 无法证明为既有问题时不得过 CP7 |
| QAC-CR168-15 | 带 process 前缀的错误质量引用 | 0 | 任一引用必须修正到 `docs/quality/` |

## CR168 Non-Functional Requirements

| NFR ID | 维度 | 要求 | 精确度量 |
|---|---|---|---|
| NFR-CR168-001 | 可审计性 | 所有分项、total、gross-to-net、model assumptions 与 limitations 可由输入重算。 | present component 的算术重算一致率 100%；orphan refs=0。 |
| NFR-CR168-002 | 确定性 | canonical serialization 对字段顺序与规范化等价输入稳定。 | 10 次执行仅 1 个 hash；tamper 检出率 100%。 |
| NFR-CR168-003 | 安全与权限 | fixture/static 路径不执行真实数据/runtime/trading/remote write。 | 每个 forbidden-operation counter=0。 |
| NFR-CR168-004 | 可演进性 | C3 复用 neutral envelope，最小共享 header 不占用 C4 专属语义。 | 平行 envelope/registry/gate=0；C4 calculator=0。 |

## CR168 CP3 Design Obligations

状态：`IN_PROGRESS_CP3`（CP2 于 2026-07-14 批准；以下作为 CP3 强制设计输入，尚未构成实现授权）。

1. 冻结 9 字段族的具体 schema、normalization、N/A、reason-code 与 numeric domain。
2. 冻结透明 impact approximation 的方法族、参数表达、`cost_underestimation_status` decision table 和 no-real-TCA wording。
3. 冻结 C3/C4 最小共享 header 与 C4-exclusive field ownership；禁止 C3 预占 capacity/ADV/liquidity/alpha-decay calculator。
4. 冻结 C3 producer → neutral envelope → Gate 4 compatibility projection 的调用方向、时机、输入、输出、降级和调用方同步修改面；canonical Gate 4 validator 与 aggregate orchestration 不在修改面。
5. 冻结 envelope availability 到 Gate 4 扁平 payload 的完整映射表：C3 `PRESENT/TYPED_UNAVAILABLE/BLOCKED` 与 C4 `reserved/not-built/typed_unavailable` 分别如何映射；C4 unavailable 的唯一安全映射为三个 refs absent-no-na-reason。
6. 冻结 projection-side reason-key denylist 与失败合同：精确 `8/8` 禁止键按 key presence 触发 `BLOCKED/REJECTED`；禁止对任意上游 mapping 盲目透传；reason 逃逸路径 canonical 调用数=`0`，并由 `SC-CR168-B02` 验证 Gate 4/capacity/aggregate PASS=`0`。
7. 处理当前 capability registry 缺失：优先记录 N/A-with-reason 并使用既有 feature/module refs；不得为了 CR168 新建平行 registry。若证明必须建立项目级 registry，转独立治理 CR 后再决定。
8. 把 `fixture_static_c3_typed_component`、`c3_gate4_compatibility_projection`、`cr155_admission_blocked_regression` 映射到既有结构化 evidence kind/taxonomy 或写出明确 N/A/替代验证路径；不得等到 CP7 才发现未知 kind。
9. 冻结 `impact_model_family=n/a-with-reason` 的合法 C3 条件：必须使用 impact 专属 reason/claim-limit/owner/trigger，不得输出通用或 C4 字段 na-reason；C3 可有效但 Gate 4 仍因 C4 absent 而 fail-closed，并在 CP5 场景/测试设计中保留验证。
10. 分离并冻结 component semantic hash 与完整 envelope canonical hash 的输入域；strategy type 不得改变相同规范化 C3 成本语义，但 subject/provenance/auth 不同的完整 envelope hash 允许不同，不新增“跨 strategy type 完整 hash 必须相同”的模糊 QAC。
11. 冻结 CR168 adapter-only 调用面：CR168 新增的 Gate 4 调用必须 `100%` 经过 projection adapter，adapter 外直接调用数=`0`；不得在运行时导入或依赖私有 `_has_na_reason`。
12. 冻结调用后安全断言：C4 unavailable 的合法 absent-no-na-reason 路径进入 canonical validator 后，Gate 4 status 必须为非 PASS；意外 PASS 必须转为内部合同错误/阻断，不得继续 aggregate。该断言不等价于 canonical Gate 4 已全局修复。
13. 将 canonical Gate 4 的全局 N/A 语义复核登记到 `FU-CR161-007`：任何未来绕过 CR168 adapter 的直接调用或 aggregate integration 前，必须重新评估并决定是否独立硬化 canonical validator。

## CR169 Capacity / Liquidity / ADV Producer Requirements

### CR169 需求清单

| Requirement ID | 名称 | 优先级 | 状态 | 精确要求 |
|---|---|---:|---|---|
| REQ-CR169-001 | Versioned typed C4 component | P0 | awaiting-CP2 | `capacity_liquidity@reserved` 只演进为 `1` 个 active C4 component / `1` 个 schema；平行 envelope/registry/gate=0。 |
| REQ-CR169-002 | Independent C4 input and correlation header | P0 | awaiting-CP2 | C4 计算字段独立；最小 C3/C4 correlation header 覆盖 identity、basis、currency、calendar、as-of、horizon、lineage/auth；CP3 冻结其规则，且不得默认进入 component semantic hash。 |
| REQ-CR169-003 | Transparent static C4 proxy | P0 | awaiting-CP2 | 仅显式 synthetic/static ADV/reference basis、participation cap、capacity curve 和 liquidity sizing 输出可审计 C4 proxy、refs、availability、reason、limitations 与 lineage。 |
| REQ-CR169-004 | Twelve-class fail-closed validation | P0 | awaiting-CP2 | 12/12 指定缺失、数值、关联、完整性、reason escape 与越权类别不得产生 present/PASS。 |
| REQ-CR169-005 | Deterministic C4 identity | P0 | awaiting-CP2 | 同一规范化 C4 输入运行 10 次只产生 1 个 canonical hash；tamper 必须 blocked。 |
| REQ-CR169-006 | Strict C3+C4 Gate 4 fixture compatibility | P0 | awaiting-CP2 | 新 joint adapter 只组合已验证的 `economic_cost@v1` + `capacity_liquidity@v1`，重建精确七字段 payload；有效 fixture 可产生 `gate4_fixture_contract_pass`，但 aggregate/capacity admission PASS=0。 |
| REQ-CR169-007 | C3-only regression and multi-strategy fixtures | P0 | awaiting-CP2 | 2/2 fixture 族；CR168 C3-only adapter 仍以 absent C4 fail-closed；C4 present 不得进入该 adapter。 |
| REQ-CR169-008 | Authorization and claim ceiling | P0 | confirmed-CP2 | real ADV/liquidity/data/calibration/runtime/trading/remote-write=0；`stage2_complete=true` 不蕴含可进入 Stage 3，`stage3_started=false`、`stage3_entry_ready=false`；真实能力 claim=false。 |
| REQ-CR169-009 | Alpha, verifier, FU-007, Stage exit and CR155 boundary | P0 | confirmed-CP2 | alpha-decay 只在 CP3 决定归属；CP8 / formal Stage 2 exit 前必须输出 `STAGE2-EXIT-VERIFICATION.result.json` 并核验 7/7 合同；FU-006 风险 CP8 披露；FU-007 的潜在 007a/007b 拆分只属后续提案，任何启动均需独立 CR/CP0/用户授权；CR155 保持 BLOCKED 与 `paper_candidate=false`。 |

### CR169 P0 fail-closed 分类

`12/12`：关联头缺失；synthetic ADV/reference basis 缺失；participation cap/method 缺失或非法；capacity model/ref 缺失；liquidity sizing/ref 缺失；非有限/负值/不可行数值；unit/currency/calendar/as-of/horizon 跨字段不一致；C3/C4 correlation mismatch；lineage/provenance/authorization 缺失或不一致；canonical identity/hash tamper；C4 N/A reason 或任意 flat-payload injection；真实数据/真实容量/runtime 越权声明或操作。

### CR169 Quantitative Acceptance Criteria

| QAC ID | 指标 | 目标值 | 失败处理 |
|---|---|---:|---|
| QAC-CR169-01 | 正式 C4 typed component 类型 | 1 | 非 1 阻断 CP7 |
| QAC-CR169-02 | active C4 schema version | 1 | 缺失或多 active 阻断 |
| QAC-CR169-03 | Gate 4 C4 refs | 3/3 | 任一缺失阻断 joint fixture contract |
| QAC-CR169-04 | C3/C4 correlation header 合同 | 1 | CP3 未冻结不得进入实现 |
| QAC-CR169-05 | fixture 族 | 2/2 | 任一缺失阻断 |
| QAC-CR169-06 | P0 fail-closed 类别 | 12/12 | 任一 false PASS 阻断 |
| QAC-CR169-07 | deterministic reruns | 10 次 -> 1 hash | 漂移或 tamper 漏检阻断 |
| QAC-CR169-08 | CR168 C3-only absent-C4 回归 | 1 | 行为变更阻断 |
| QAC-CR169-09 | strict C3+C4 Gate 4 fixture contract PASS | 1 | 缺失或非严格 payload 阻断 |
| QAC-CR169-10 | capacity/aggregate admission PASS、real-capacity claim、CR155 promotion、`stage3_entry_ready` | 0/0/0/false | 任一非零或 true 阻断 |
| QAC-CR169-11 | canonical Gate 4 / aggregate orchestration 修改 | 0/0 | 任一修改阻断 |
| QAC-CR169-12 | real data/calibration/runtime/broker/trading 操作 | 0 | 任一非零阻断 |
| QAC-CR169-13 | alpha-decay calculator（CP3 未归入时） | 0 | 任一实现阻断 |
| QAC-CR169-14 | CR169 新增路径引入的测试失败 | 0 | 无法归因既有问题时不得过 CP7 |
| QAC-CR169-15 | 带错误 `process/` 前缀的质量文档引用 | 0 | 必须修正到 `docs/quality/` |

### CR169 Non-Functional Requirements

| NFR ID | 维度 | 要求 | 精确度量 |
|---|---|---|---|
| NFR-CR169-001 | 可审计性 | C4 proxy、三个 refs、limitations、correlation 与 lineage 均可由 static input 重算。 | present component 重算一致率 100%；orphan refs=0。 |
| NFR-CR169-002 | 确定性 | 规范化、canonical serialization 与 hash 对等价输入稳定。 | 10 次仅 1 hash；tamper 检出率 100%。 |
| NFR-CR169-003 | 安全与权限 | 禁止真实数据、真实容量校准、runtime/trading/remote write。 | 每个 forbidden-operation counter=0。 |
| NFR-CR169-004 | 可演进性 | C4 复用 neutral envelope；joint adapter 不侵入 CR168 adapter/canonical Gate 4/aggregate。 | 三个既有边界修改数=0；C4 semantic hash 不被 correlation header 隐式污染。 |

### CR169 CP3 Design Obligations

状态：`CP2_APPROVED`。CP2 批准后，CP3 必须：

1. 冻结 C4 static proxy 的方法族、numeric domain、participation 边界、reason-code 与 no-real-ADV/capacity wording。
2. 冻结 minimal C3/C4 correlation header 的 owner、required/optional、cross-component equality 与它不进入 component semantic hash 的规则。
3. 冻结 strict joint adapter 的调用方向、type/version/identity/limitation checks、精确七字段 payload、denylist/allowlist、canonical postcondition 与降级行为；不得改变 CR168 adapter 或 canonical Gate 4。
4. 决定 alpha-decay 的归属（C4、C2 或独立 CR）并回写 Deferred 状态；未归入时维持 calculator=0。
5. 冻结 FU-006 verifier independence 的 CP8 披露模板与触发条件；不得把 fixture contract PASS 表述为真实 capacity readiness。
6. 保留 `stage3_entry_ready=false`，在设计中引用 CP8 / formal Stage 2 exit 的 `STAGE2-EXIT-VERIFICATION.result.json`（7/7）；仅把 FU-007 007a/007b 写作非绑定后续提案，不预建 CR、不修改 canonical Gate 4。

## CR170 Canonical Reliability N/A Semantics and Admission Requirements

### CR170 需求清单

| REQ ID | 标题 | 优先级 | 精确要求 |
|---|---|---:|---|
| REQ-CR170-001 | Gate 1-5 N/A policy inventory | P0 | 固定 `21/21` policy units；每项必须记录 Gate、证据字段族、mandatory/conditional 适用条件、owner、合法完整边界和结果规则。 |
| REQ-CR170-002 | Five-state business semantics | P0 | 冻结 PRESENT、MISSING、NA_WITH_COMPLETE_BOUNDARY、NA_WITH_INCOMPLETE_BOUNDARY、GENERIC_REASON_ESCAPE 五种业务语义；CP2 不预先冻结 enum/dataclass 代码形态。 |
| REQ-CR170-003 | Gate 1 masked-escape observability | P0 | 对 multiple-testing/FDR 等被其他 unavailable claim 掩盖的路径执行字段判定、mandatory claim 生成、最终 worst-state 三层断言；不得只断言最终 status。 |
| REQ-CR170-004 | Gate 2-5 fail-closed consumption | P0 | mandatory missing、generic reason escape、incomplete boundary 不得因存在 reason 字符串而被当作 present；所有适用 policy unit 均有正/负/边界测试。 |
| REQ-CR170-005 | Preserve verified lower-level worst-state merge | P0 | 先证明 `build_shared_gate_summary` 对 `NEEDS_REVIEW` 的现有传播 `1/1 PASS`；无失败证据时该逻辑修改数必须为 `0`。 |
| REQ-CR170-006 | Admission-tier hardening boundary | P0 | 在 `resolve_admission_policy` 或 CP3 选定的最小公共边界处理 mandatory `NEEDS_REVIEW`：T0 返回 NEEDS_REVIEW 且不得声称 PASS；T1/T2 BLOCKED；T3 NOT_AUTHORIZED。 |
| REQ-CR170-007 | Public compatibility and adapter regression | P0 | 公共 Gate API/结果 schema 保持兼容；CR168 C3-only 与 CR169 strict joint adapter 回归 `2/2 PASS`，局部 guard 不在本 CR 删除。 |
| REQ-CR170-008 | State/baseline correction with traceability | P0 | BACKLOG、CURRENT-REQUIREMENT-BASELINE 与 MULTIFACTOR-RESEARCH 三类已知状态偏差 `3/3` 增量修正；历史记录保留并标注需独立 Stage 3 CR revalidation。 |
| REQ-CR170-009 | Authorization, Stage 3 and CR155 boundary | P0 | 真实数据、Stage 3 Launch/current runner integration、aggregate、runtime/trading、remote publish 与 CR155 promotion 均为 `0`；`stage3_entry_ready=false`。 |

### CR170 Gate 1-5 Policy Inventory

固定分母为 `21` 个 policy units：Gate 1=`6`（multiple-testing、FDR、WRC/SPA、PBO/CSCV、DSR/deflation、trial-count）；Gate 2=`6`（split、walk-forward、OOS、purge、embargo、event-safe-gap）；Gate 3=`1`（PIT/survivorship-free universe）；Gate 4=`5`（impact-model、ADV participation、capacity dollars、liquidity sizing、cost-underestimation）；Gate 5=`3`（regime、attribution、reconciliation）。conditional unit 必须记录适用条件，不得因非适用样本减少 inventory 分母。

### CR170 Quantitative Acceptance Criteria

| QAC | 精确标准 |
|---|---|
| QAC-CR170-01 | Gate 1-5 policy inventory=`21/21`，mandatory/conditional/owner/boundary/result 规则完整率=`100%`。 |
| QAC-CR170-02 | 五种业务语义=`5/5`；generic reason 不得替代 mandatory evidence。 |
| QAC-CR170-03 | Gate 1 masked-escape 三层断言=`3/3`，至少覆盖 multiple-testing 与 FDR 两条路径。 |
| QAC-CR170-04 | Gate 1-5 任一 applicable mandatory `{missing,generic_reason_escape,incomplete_boundary}` 导致无条件 PASS 的数量=`0`。 |
| QAC-CR170-05 | NA_WITH_COMPLETE_BOUNDARY 的 owner、reason、scope、profile/authorization 边界完整率=`100%`，结果不得越过 tier policy。 |
| QAC-CR170-06 | `build_shared_gate_summary` 既有 NEEDS_REVIEW 传播回归=`1/1 PASS`；无失败证据时相关生产逻辑修改=`0`。 |
| QAC-CR170-07 | mandatory NEEDS_REVIEW 的 tier 结果：T0=`NEEDS_REVIEW`、T1=`BLOCKED`、T2=`BLOCKED`、T3=`NOT_AUTHORIZED`，匹配=`4/4`。 |
| QAC-CR170-08 | `resolve_admission_policy` 与底层 worst-state merge 的职责边界在 CP3 ADR/HLD 中明确=`1/1`。 |
| QAC-CR170-09 | public Gate API 和结果 schema 非兼容变更=`0`。 |
| QAC-CR170-10 | CR168/CR169 adapter 回归=`2/2 PASS`；本 CR 删除或简化 guard=`0`。 |
| QAC-CR170-11 | current Stage 3 runner 新增 canonical Gate 调用=`0`；aggregate orchestration 修改=`0`。 |
| QAC-CR170-12 | BACKLOG/baseline/historical Stage3 marker 三类状态修正=`3/3` 且修订记录/CR ref 完整。 |
| QAC-CR170-13 | CR155 promotion=`0`，`paper_candidate=false` 保持。 |
| QAC-CR170-14 | real-data/lake/provider/NAS/credential/runtime/broker/QMT/trading/catalog/publish/remote-write 操作=`0`。 |
| QAC-CR170-15 | CR170 新增路径引入测试失败=`0`；无法证明为既有失败时不得通过 CP7。 |

### CR170 Non-Functional Requirements

- **正确性**：mandatory evidence 的业务状态与 tier/admission 结果必须可由公开输出审计，不以 reason 字符串存在性替代证据有效性。
- **兼容性**：优先局部硬化判定边界，不破坏公共 callable/result schema；adapter 保持 defense-in-depth。
- **确定性**：相同 normalized evidence、profile 与 policy 必须得到相同 status、claim IDs 和 reasons。
- **可审计性**：所有 N/A policy unit 必须关联 owner、适用条件、完整边界与 canonical reason code。
- **安全性**：T0 只允许非真实数据诊断探索且不得声称 admission PASS；T1/T2 fail-closed；T3 不授权。

### CR170 CP3 Design Obligations

- 明确五态业务语义到代码形态的最小映射；不得仅修改 `_has_na_reason` 的布尔含义而误伤合法结构化 N/A。
- 绘制 Gate 1-5 policy consumption 与 Gate 6 两层边界：底层 `build_shared_gate_summary` worst-state merge 和上层 `resolve_admission_policy` tier/admission decision。
- 把现有 bottom-up NEEDS_REVIEW 传播设为受保护回归；只有失败证据才能授权重写。
- 为 Gate 1 masked escape 固化字段判定、claim 生成、最终 worst-state 三层测试契约。
- 明确 CR168/CR169 adapter 的保留条件，以及仅由后续 FU-CR161-009 + ADR 评估简化的边界。

## CR171 Stage 3 Launch / Real-Lake Entry Requirements

### REQ-CR171-001 Stage 3 Evidence-Route Decision

CP2 必须在 `current_runner` 与 `c1_c4_real_producer` 中选择一条唯一路线。推荐 `c1_c4_real_producer`，其后续 real computation、producer binding 与 aggregate orchestration 必须由独立 Real-Evidence Activation CR 明确授权；`current_runner` 路线则必须由 CP3 先冻结完整 read-only execution boundary。

成功标准：CP2 Decision Brief 只记录 1 条 selected route；路线未确认时 `stage3_started=false`、`real_computation_authorized=false`；路线选择本身不执行任何操作。

### REQ-CR171-002 Event-Bounded FU-006 Verifier Waiver

CP2 可以选择 `fu006_first` 或 `event_bounded_waiver`。若选择 waiver，其不可延展的到期事件为：首个 real-evidence admission 决策可为 `PASS` / `PASS_WITH_RISK` 前，或 Stage 3 exit gate 可启动前。CR170 历史 CP8 的 verifier 风险接受不得继承为本 CR 的授权。

成功标准：waiver 到期事件为 2/2 且可机械判断；到期前外的例外数量为 0；任何到期事件发生后无 FU-006 证据不得产生 admission PASS/PASS_WITH_RISK 或启动 exit gate。

### REQ-CR171-003 Deny-Default Frozen Read Contract

任何未来 read-only 授权必须在 CP2 中冻结 `data_release`、datasets、date range、read identity 和 output directory 五元组，且同时 deny credentials/environment read、provider fetch、lake/NAS write、catalog/current-pointer mutation、runtime 与 trading。本 CP1 只记录该决策合同，不读取真实数据或环境。

成功标准：允许项字段族为 5/5；deny-default 类别为 6/6；本 CR CP1 的真实数据读取、凭据读取、provider 调用、写入、runtime/trading 操作均为 0。

### REQ-CR171-004 Historical Evidence Legacy / Revalidation Ceiling

历史 Stage 3 叙事必须带 `legacy / require-revalidation` 标记。若在后续获授权的审计中进行 revalidation，它只能判定、标注和报告；权威 current-entry verdict 只能是 `revalidated_for_current_entry`、`insufficient_for_current_entry` 或 `incompatible_rework_required`，`reaffirmed_as_legacy_only` 仅作 legacy annotation。数据、schema、PIT、lineage、代码、manifest 或证据缺陷均须路由到新 follow-up/CR，不得在 CR171 修复。

成功标准：合法 revalidation verdict 为 3/3；repair/backfill/rerun/manifest rewrite 数为 0；任何历史事实均不使 `stage3_entry_ready=true` 或 `real_evidence_available=true`。

### REQ-CR171-005 Claim Ceiling and Adjacent-Debt Isolation

CR171 必须把 CP8 delivery 成功与 Stage 3 entry readiness 分离：CP8 只能确认本 CR 的决策/文档/验证闭环，不能确认 `stage3_started`、`stage3_entry_ready`、`real_data_read_authorized`、`real_computation_authorized` 或 runtime/trading。CR010、CR018 和 CR032 仅披露历史邻接债务而不重开；新消费者必须使用 `R-CR170-RUNNER-GAP`，历史 `R-CR170-STAGE3-OVERCLAIM` 仅经 alias 解析。

成功标准：5 个禁止提升的 claim 始终为 false；邻接 CR 修改数为 0；当前风险 ID 仅使用 `R-CR170-RUNNER-GAP` 1 个 canonical consumer ID。

## CR171 Quantitative Acceptance Criteria

| QAC | 指标 | 精确目标 | 失败行为 |
|---|---|---:|---|
| QAC-CR171-01 | CP2 formal decisions | 3/3 | 缺任一决策不得进入 CP3 |
| QAC-CR171-02 | frozen read-contract allow fields / deny classes | 5/5 / 6/6 | 缺字段或 deny 项则 read scope 不成立 |
| QAC-CR171-03 | revalidation verdicts / repair actions | 3 / 0 | 非法 verdict 或任何 repair 阻断 |
| QAC-CR171-04 | historical claim marker | 1/1 legacy/require-revalidation | 无标记不得宣称 current entry ready |
| QAC-CR171-05 | real data / credentials / provider / write / runtime-trading actions in CP1 | 0 / 0 / 0 / 0 / 0 | 任一非零即 CP1 FAIL |
| QAC-CR171-06 | CP8-to-entry-ready implication | 0 | 任一暗示或状态提升阻断 |

## CR172 Stage 3 Real-Evidence Activation Requirements

### REQ-CR172-001 Finite Five-Field Authorization Contract

CP2 必须由授权 data owner 冻结 `data_release`、`datasets`、`date_range`、`read_identity`、`output_directory` 五个精确有限值。禁止 `*`、latest/current 等动态通配语义、从上游隐式继承、从历史目录/manifest 反向推断或把 `output_directory` 解释成写授权。

成功标准：五字段有限值 `5/5`；通配符、隐式继承、目录推断与隐含写授权各为 `0`；任一字段缺失时 activation 必须保持 `BLOCKED`。

### REQ-CR172-002 Conditional PATH-B/C/A Routing

CP2 必须在 PATH-B、PATH-C、PATH-A 中记录一个最终路径。五字段不可冻结或方法学必须先完成时采用 PATH-B；五字段可冻结且优先最小 blast radius、或未显式接受三 producer 联合激活时，默认 PATH-C；只有用户明确接受 C1-C3 首次联合风险时才可采用 PATH-A。

成功标准：最终路径选择 `1/1`；推荐/备选/触发条件覆盖 `3/3`；未显式三 producer 风险接受时 PATH-A 隐式选择数为 `0`。

### REQ-CR172-003 PATH-B Activation Recovery Chain

PATH-B 只完成 `FU-CR164-004` effective-trial estimator 的离线方法、schema、golden vectors 和 consumer projection，不读取真实数据，也不关闭 OI-CR171-001..005。PATH-B 完成后，一旦五字段可冻结，Host Orchestrator 必须恢复 CR172 的 CP2 路由并重新选择 PATH-C 或 PATH-A；estimator 完成不得被表述为 activation 或 Stage 3 完成。

成功标准：PATH-B 后 activation resume route=`1`；OI-001..005 关闭数=`0`；Stage3/activation 完成声明数=`0`。

### REQ-CR172-004 C1 Typed-Unavailable Degradation

FU-CR164-004 未完成或未并入时，C1 必须支持：`effective_trial_count=typed_unavailable`、effective ref/method 为空、`raw_trial_count` 不得别名 effective count。该状态允许设计/验证 channel、release/schema/PIT/lineage/run-identity binding，但不得产生 C1 computable、effective-count available 或 admission PASS 声明。

成功标准：raw-to-effective alias=`0`；缺 estimator 时 channel binding 可判定 `1/1`；C1 computable/admission PASS 错误声明=`0`。

### REQ-CR172-005 Producer Isolation and C2/C3 Governance

五字段缺失/歧义、read identity 未授权、release/date 越界、共享 PIT/lineage 失效或 forbidden operation 会阻断所有 producer；producer-local 输入或计算失败只阻断本 producer，不阻止共享前置满足的其他 producer 独立形成 truthful evidence。该隔离不构成 aggregate OR-pass。PATH-C 获批后，C2、C3 默认分别进入两个独立 runtime-high-risk follow-up CR，总 activation CR 数预计为 `3`；同 parent 顺序 slice 只允许作为 CP2 显式备选。

成功标准：共享 blocker 全局阻断覆盖率=`100%`；局部失败错误串扰=`0`；PATH-C 后 C2/C3 owner lane=`2/2`；aggregate OR-pass=`0`。

### REQ-CR172-006 Effective-Trial Owner and Joint Approval

`FU-CR164-004` 默认保持独立方法学 scope。若 data/activation owner 与 strategy-admission methodology owner 不同但拟合并，两位 owner 必须分别对同一 `scope_revision` / `scope_hash` 写入 approved gate ledger 事件，并共同引用一个 approval group；风险、权限和回滚边界采用二者交集及更严格限制。任一批准缺失、hash 不同或 revision 变化时，旧批准失效并拆分 estimator。

成功标准：需要合并时 individual approvals=`2/2`、revision/hash match=`100%`、partial approval 合并数=`0`、权限并集扩张数=`0`。

### REQ-CR172-007 E1, OI-005 and Adjacent-Scope Ceiling

CR172 CP8 与 producer component generation 均不触发 E1；E1 只在后续 admission CR 首次试图给出 `PASS/PASS_WITH_RISK` 前触发。`OI-CR171-005` classification/revalidation audit、C4 rework、FU-006 independent verifier 和 FU-CR161-009 aggregate/CR155 regression 全部保持独立，CR172 不关闭 OI-003/004/005。

成功标准：错误 E1 触发数=`0`；OI-003/004/005 在 CR172 内关闭数=`0`；OI-005 repair/classification 执行数=`0`。

### REQ-CR172-008 Runtime-High-Risk Gate and Claim Ceiling

CR172 使用 standard + runtime-high-risk 路线。CP2 approval 最多确认路径、五字段、owner identity、降级/治理合同与有限风险边界；Story 仍需 CP3/CP4，实施需 CP5，真实行为需获批合同和 CP6/CP7 证据。任何 provider fetch、credential/env read、lake/NAS write、catalog/current-pointer mutation、QMT/trading、publish/deploy/Git remote write 均不在当前授权内。

成功标准：CP2 前真实数据、credential、provider、write、runtime/trading 操作各=`0`；`stage3_started`、`stage3_entry_ready`、`mature_admission_pass`、`aggregate_orchestration_implemented`、`cr155_promoted` 全为 `false`。

### REQ-CR172-009 Trial-Return Source and Object Contract

PATH-I 必须先定义真实 trial-return 上游，而不能把 CR163 的 metadata/ref、现有 `layered_returns.csv` 因子分层 forward return、CR173 的显式 dependency matrix `R` 输入或任意回测汇总指标当作 trial-return series。推荐来源是未来经独立授权的 multi-trial runner：每个 `family_id/run_id/trial_id` 产生一个有序、不可变、可 seal 的 `trial_portfolio_return_series@v1`，最小产品字段覆盖 object kind、family/run/trial identity、ordered time index、return value、return basis、source lineage、schema version、content hash 与 seal status。具体列名和数值约束由 CP3 冻结，本轮不得伪装为现有能力。

成功标准：source kind 可判定=`1/1`；identity 三元组=`3/3`；最小语义字段=`9/9`；错误 returns 对象、source 缺失、trial identity 错配与 unsealed source 的 fail-closed 覆盖=`100%`；真实 trial-return generation=`0`。

### REQ-CR172-010 Research-Local Canonical, NAS Verified Replica and Stable Logical URI

每个 trial-return artifact 的 identity 保存 stable logical URI + content hash。研究机路径 `${QUANT_LAB_RESEARCH_RUNS_ROOT}/experiment-families/...` 是实际运行路径和 active canonical；NAS `${NAS_RESEARCH_SYNC_ROOT}/runs/experiment-families/...` 只能是 versioned/hash-verified replica、backup 与 distribution source；执行机从 NAS 拉取到 temporary staging，校验 release/manifest/hash 后原子物化为 `${EXECUTION_RESEARCH_CACHE_ROOT}/experiment-families/...` immutable cache。执行 runtime 不直接读 NAS，绝对挂载路径不进入 lineage identity。

成功标准：logical URI + hash=`100%`；research-local active canonical=`1/1`；额外 canonical 声明=`0`；replica stale/partial/hash mismatch 接受数=`0`；execution direct-NAS runtime read=`0`；pull 校验 release/manifest/hash=`3/3`；当前 sync/pull/materialize=`0`。

### REQ-CR172-011 Multi-Trial Per-Action Authorization

以下六类真实动作必须拥有独立 owner、scope revision/hash、允许/禁止路径、到期/撤销条件和证据：`data_lake_read`、`multi_trial_runtime_and_workspace_write`、`trial_return_generation`、`empirical_R_computation`、`nas_replica_sync`、`execution_pull_verify_materialize`。CP2、fixture implementation 或任一动作批准均不能扩张到其他动作。

成功标准：动作=`6/6`；每类授权字段=`6/6`；跨动作隐含授权=`0`；partial approval 下未批准动作执行=`0`；本轮真实动作=`0/6`。

### REQ-CR172-012 Four-Component Data Ownership and GitHub Ceiling

四组件职责必须可审计：研究机承载 checkout/uv/runtime workspace、本地 data lake、实验/回测报告与 trial returns active canonical；NAS 承载 verified replica/backup/distribution，并隔离 data-lake、research、package-exchange、conditional signal-exchange、trading-archive zone；执行机只消费批准策略包和经过 pull+verify+atomic materialize 的本地 immutable cache，runtime 不直读 NAS；GitHub 只保存 code/schema/docs/manifest/hash/pointer/release metadata。

成功标准：组件=`4/4`；NAS zone=`5/5`；允许/禁止流=`100%`；execution direct-NAS runtime read=`0`；GitHub real data/returns/credential/account-order payload=`0`；当前 sync/pull/deploy/remote write=`0`。

### REQ-CR172-013 New-Run Semantic Path and Legacy Read-Only Compatibility

新单次研究运行的默认根必须替换为 `${QUANT_LAB_RESEARCH_RUNS_ROOT}/multifactor-strategy-research/{run_id}/`，不得继续生成 `stage3_mature_multifactor/{run_id}`。历史 `/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor/{run_id}/` 仅作为 read-only audit reference；本 delta 不 move、rename、copy-recanonicalize、rewrite manifest 或改写历史 lineage。新旧目录不能同时宣称当前默认/canonical；任何未来迁移必须独立 CR、独立授权、可回滚且保持 stable logical URI。

成功标准：新运行默认语义路径=`1/1`；新 run 写 legacy path=`0`；历史 move/rename/manifest rewrite=`0`；legacy/new 双默认=`0`；历史审计引用保留=`100%`；当前 migration 操作=`0`。

### REQ-CR172-014 Declared-Exact versus Empirical-R Fail-Closed

所有 dependency matrix 必须显式分类为 `declared_exact` 或 `empirical`。CR173 fixture/golden-vector 的显式矩阵只能作为 declared-exact 方法输入，不能证明真实 empirical R 已存在。未来 empirical R 必须绑定同一 sealed family/run 的 ordered trial IDs、每个 trial-return logical URI + content hash、共同估计窗口、对齐/缺失处理、估计方法/version/hash、数值有效域与 PSD/repair policy；任何字段缺失、跨 trial 对齐失败、source/hash 不一致、未经批准 repair 或计算授权缺失时必须 `typed_unavailable` / `BLOCKED`，且 `c1_computable=false`。

登记 `FU-CR173-001`（Empirical dependency-matrix methodology v2 and sampling-error validation）作为候选。它不是重开 PATH-C/A 设计的绝对前置：按 DQ-003，设计可保留 `effective_trial_count=typed_unavailable` 降级。凡要输出 available effective trial count 或声明 `c1_computable=true`，必须先完成 `FU-CR173-001` 的 sampling-error/uncertainty evidence、method version 2 + hash、有效域/偏差界限和独立验证。未来 PATH-C/A CP2 必须显式三选一：完成 v2；拆为 future activation；或采用 DQ-003 降级。

成功标准：R classification=`1/1`；empirical provenance 字段=`8/8`；trial order/return alignment 覆盖=`100%`；错配或未授权 repair 的 available result=`0`；declared-exact 冒充 empirical=`0`；未完成 `FU-CR173-001` 时 available effective count / `c1_computable=true`=`0/false`；PATH-C/A 三选一记录=`1/1`；本轮 empirical-R computation=`0`。

### REQ-CR172-015 Execution-Local Signal Generation and Optional Batch-Contract Boundary

默认由执行机基于批准策略包和本地行情生成交易信号，研究机与执行机之间不传信号。PATH-I/CP3 只冻结低频/EOD 可选 immutable `SignalBatch/TargetPositionBatch` 的精确 8 个最小字段：`schema_version`、`batch_id`、`strategy_id`、`strategy_package_hash`、`content_sha256`、`signature/key_id`、`valid_from/valid_until`、`sequence_no`。batch 不得携带 credential、account secret 或 broker order command。

七级状态机、具体 mailbox 物理路径、ack 状态机、idempotency/replay 规则、真实 sync/transport/消费实现不属于 PATH-I 当前规范，登记为 `DF-CR172-SIGNAL-BATCH-EXCHANGE`；intraday/低延迟传输登记为 `DF-CR172-INTRADAY-REALTIME-SIGNAL`。两者均为 candidate/backlog，不创建正式 CR。

成功标准：默认 execution-local generation boundary=`1/1`；默认跨机信号传输=`0`；最小字段=`8/8` 且额外 mandatory 字段=`0`；forbidden payload 接受=`0`；mailbox path/state-machine/ack/idempotency/replay/sync/transport/consumer implementation=`0/0/0/0/0/0/0/0`；intraday implementation=`0`。

### CR172 PATH-I Phase Guards

| Gate | 允许的最高动作 | 必须保持为零 / false |
|---|---|---|
| CP2 | 只确认产品基线并解锁 CP3 | design implementation、目录创建、NAS write、multi-trial、signal transport=`0` |
| CP3 | 只冻结设计 | 目录创建、NAS write、multi-trial runtime、signal generation/transport=`0` |
| CP5 | 只允许 repository-local code/test/fixture | 六类真实动作授权=`0/6`，真实 sync/pull/signal/runtime=`0` |
| CP7 | 验证设计合同与零操作证据 | 六类真实动作执行计数=`0/6` |
| CP8 | 最高声明 `path_i_design_ready=true` 或等价 verified contract-ready | `stage3_entry_ready=false`、`c1_computable=false`、`real_data_authorized=false`、`multi_trial_runtime_authorized=false`、`signal_transport_authorized=false` |

## CR172 CP2 Decisions

### 历史已决 DQ（保留 ID 与 PATH-B 基线）

| DQ | 历史决定 | 正式状态 |
|---|---|---|
| DQ-CR172-001 | 五字段当时不可冻结，因此进入 PATH-B；未来五字段必须重新冻结。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-002 | effective-trial 方法学保持独立，由 CR173 承接。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-003 | C1 必须支持 effective count typed-unavailable 降级，raw alias=`0`。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-004 | 不接受 C1-C3 首次联合 blast radius；PATH-A 不得隐式选择。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-005 | E1 只在后续 admission maturity action 前触发。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-006 | OI-CR171-005 保持独立 audit lane。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-007 | 未来 C2/C3 默认使用独立 runtime-high-risk CR。 | RESOLVED-PRIOR-CP2 |
| DQ-CR172-008 | owner 合并要求同 revision/hash 双 ledger，权限与风险取交集；否则拆分。 | RESOLVED-PRIOR-CP2 |

### Scope-delta CP2 已批准 DQ

| DQ | 待确认问题 | 推荐方案 | 可执行备选 | 优劣、影响与风险 | 回退 / 切换条件 | 正式状态 |
|---|---|---|---|---|---|---|
| DQ-CR172-009 | trial-return source 采用什么对象和生产入口？ | PATH-I 冻结 future native multi-trial runner 的 per-trial `trial_portfolio_return_series@v1`；source 不存在或错型时 fail-closed。 | A：只接收外部预计算 series，但必须先建 import/provenance contract；B：保持 source absent、C1 typed-unavailable。 | 推荐方案 lineage 最完整但新增 runner/instrumentation 设计与独立 runtime 授权；A 集成快但外部 provenance 风险高；B 最安全但无真实 C1。 | 若 CP3 证明 native producer 不可行或 owner 缺失，切 A；任何 provenance 不足回退 B。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-010 | active canonical、replica 与执行缓存如何分工？ | 研究机本地 active canonical → NAS verified replica/backup/distribution → 执行机 pull+verify+atomic local immutable cache。 | A：保持 research-local canonical 但不提供执行机分发；B：storage/distribution 全部 blocked。 | 推荐符合用户主权且运行不依赖共享盘；A 无法满足执行数据分发；B 最安全但阻断 activation。 | NAS 或执行机校验能力缺失时回退 B；不得回退为 NAS runtime canonical。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-011 | multi-trial、sync、pull/materialize 是否拆分授权？ | 六类数据动作逐项授权、逐项撤销、逐项证据。 | A：runtime+generation 合并；sync+pull 合并；B：全不授权。 | 推荐 blast radius 最小但门禁多；A 归因/撤销较粗；B 只能 fixture/static。 | 授权系统无法表达六项时先回退 B，再由 CP3 提出不降低安全性的最小合并。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-012 | 四组件 ownership 与允许流向如何确定？ | 研究机 active canonical；NAS verified replica/distribution；执行机 approved package + verified local cache；GitHub metadata-only。 | A：执行机 runtime 直读 NAS；B：GitHub 承载小型 return samples。 | 推荐隔离运行与副本；A 引入共享盘可用性/一致性风险；B 破坏 data ceiling。 | 仅独立安全/合规 CR 可评估备选；本轮不切换。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-013 | 新运行路径与历史 stage3 路径如何共存？ | 新 run 切到 `multifactor-strategy-research/{run_id}`；历史路径只读、不迁移、不 rewrite。 | A：继续使用旧路径；B：一次性迁移并 rewrite 历史引用。 | 推荐方案语义清晰且审计风险最低；A 保持兼容但延续 stage-based 误导；B 目录统一但身份漂移/回滚风险最高。 | 仅在独立 migration CR 具备 inventory、hash、rollback 和用户授权后评估 B；兼容阻断时可临时停止新 run，不能回写旧默认。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-014 | empirical R 不可验证或尚未获计算授权时如何处理？ | 显式区分 declared-exact/empirical；PATH-C/A 设计可按 DQ-003 typed-unavailable 降级继续，但 available effective count 或 `c1_computable=true` 必须先完成 `FU-CR173-001`。 | A：拆 positive empirical path 为 future activation；B：当前只允许 declared-exact fixture；C：接受外部 empirical R，但另建 import/validation contract。 | 推荐方案保留设计推进能力且防止 sampling-error overclaim；A 隔离真实计算；B 最安全但无 positive empirical；C 可复用外部结果但 provenance 风险高。 | 未来 PATH-C/A CP2 必须在“完成 v2 / 拆 future activation / DQ-003 降级”三者中记录 `1/1`；未完成 v2 时 positive claim 必须为 0。 | RESOLVED-APPROVED-CP2 |
| DQ-CR172-015 | 研究机与执行机之间是否以及如何传交易信号？ | 默认执行机本地生成；低频/EOD 只冻结 immutable batch 精确 8 字段；详细 exchange 与 intraday 分别 deferred。 | A：完全禁用跨机 batch；B：所有频率经 NAS；C：研究机直接推送。 | 推荐边界最小且不给实现偷跑；A 更简单但无 EOD 候选；B/C 扩大一致性、连接和安全面。 | 只要需要物理路径、状态机、ack、idempotency/replay、真实 sync/transport/消费或 intraday，就退出 PATH-I，分别路由两个 deferred candidate。 | RESOLVED-APPROVED-CP2 |

本轮改变产品范围的 DQ-CR172-009~015 已于 `2026-07-17T16:54:09+08:00` 全部按推荐值获得用户批准。原 DQ-001~008 与 PATH-B 历史继续有效；`ready_for_design=true`，但只解锁 CP3 design-only，不授权任何真实动作。

## CR173 Effective-Trial Offline Methodology Requirements

### REQ-CR173-001 Effective-Count Estimand and Non-Alias Boundary

CR173 v1 必须把历史 envelope 字段 `effective_trial_count` 中的新方法语义精确限定为：对与 sealed trial IDs 对齐的显式 canonical correlation matrix `R`，用 `spectral_participation_ratio=(tr R)^2/tr(R²)` 计算二阶 effective dimensionality。它不是 `raw_trial_count` 的复制、重命名或默认值，也不是 Li–Ji effective independent tests、BH/FWER/Šidák 校正或 DSR/admission calibration。

成功标准：estimand 边界 `1/1`；raw-to-effective copy/rename/default/implicit-fallback 路径 `0`；raw 与 effective dimensionality 的来源字段、方法字段和 provenance 域相互独立 `3/3`；Li–Ji/BH/FWER/Šidák/DSR/admission calibration 正向声明 `0`。

### REQ-CR173-002 CP3 Method and Input-Contract Freeze

CP2 只冻结用户可观察行为与度量。CP3 已选定 `spectral_participation_ratio`，并必须在设计证据中冻结：sealed identity、ordered trial IDs、canonical exact-decimal PSD correlation matrix、method ID/version/hash、确定性数值契约、二阶充分性假设、`[1,n]` 输出域和 Spike/版本升级切换条件。CR173 只消费显式 matrix，不估计真实 correlation matrix。

成功标准：CP3 input-contract inventory 覆盖率 `100%`；每一输入类别均有 required/optional、valid/invalid 与缺失行为；方法、版本、hash、假设和切换条件 `5/5` 非空；未冻结时进入实现的 Story 数 `0`。

### REQ-CR173-003 Typed-Unavailable Fail-Closed Semantics

缺少批准方法、方法版本/hash、必要输入、有效相关矩阵或 lineage/provenance，或出现 NaN/Inf、定义域非法、输入矛盾、method/hash/evidence mismatch 时，standalone evidence 必须 fail-closed：缺失/不足为 `typed_unavailable`，矛盾、篡改或伪造 provenance 为 `blocked`。任何失败不得退回 raw count。

成功标准：枚举失败类 `8/8` 均不产生 present/available；raw fallback `0`；错误 C1 computable/PASS `0`；修正输入后必须形成新 evidence version，旧失败记录保留 `1/1`。

### REQ-CR173-004 Seven-Field Typed Evidence and Provenance

standalone evidence schema 固定为 `7/7` 字段：`effective_trial_count`、`effective_trial_count_status`、`effective_trial_method`、`effective_trial_method_version`、`effective_trial_method_hash`、`effective_trial_input_lineage_ref`、`effective_trial_computation_ref`。`typed_unavailable` 时 count/method/ref 的空值规则由 CP3 设计契约精确定义，但 status 与 machine reason 必须可审计。本 schema 不是 public C1 contract。

成功标准：present evidence 的七字段完整率 `100%`；任一字段缺失时 present/available 数 `0`；orphan lineage/computation refs `0`；schema version 未声明的证据接受数 `0`。

### REQ-CR173-005 Strategy-Agnostic Offline Boundary

estimator 的 estimand、方法、schema 和 golden-vector 不得要求、推断或冻结具体 `strategy_id` / `strategy_name`。输入只能来自仓库内 synthetic、fixture 或 golden-vector；未来 CR172 activation 才负责真实策略身份、five-field scope、run identity 与 real producer binding。

成功标准：CR173 必填 strategy identity 字段 `0`；从目录、manifest、run 或历史记录推断策略身份 `0`；真实 lake/NAS/provider/credential 输入 `0`；strategy-agnostic vectors 覆盖 `6/6`。

### REQ-CR173-006 Deterministic Golden-Vector Acceptance

CP3 必须为六类固定 golden vectors 冻结输入与预期：独立试验、正相关试验、高度/完全相关边界、单试验边界、无效/非有限输入、provenance/hash mismatch。每类在同一规范化输入、方法版本和参数下重复三次。

成功标准：类别 `6/6`；每类重复 `3/3`；合法类别每组只产生 `1` 个 canonical result/hash；无效与 mismatch 两类 available/PASS `0`；排序或等价规范化导致的结果漂移 `0`。

### REQ-CR173-007 Standalone Evidence and Public-Boundary Stop

CR173 只生成 `1` 份符合七字段契约的 standalone typed evidence，并在 public C1 边界停止。本 CR 修改 public C1 / Gate 1 / statistical summary / DSR / admission consumer 生产文件数和向其传入新结果的调用数均必须为 `0`；当前 `effective_trial_count`、C1/Gate1/admission 继续 `typed_unavailable`。`offline_method_ready` 只表示 fixture-only standalone estimator 可用，不表示 public C1 可计算。

成功标准：standalone seven-field evidence `1/1`；public C1 projection/write `0/0`；新增 competing gate `0`；raw-to-effective alias `0`；`public_effective_trial_count_populatable`、`c1_computable`、`real_evidence_available`、`stage3_started`、`stage3_entry_ready`、`mature_admission_pass`、`aggregate_orchestration_implemented` 均为 `false`。真正 `c1_computable` 只能由未来经独立 owner 批准的 versioned projection CR 建立。

### REQ-CR173-008 Gate, Authorization and CR172 Prerequisite Ownership

CR173 遵循 standard-code CP0-CP8；CP2 只批准产品范围，CP3 批准方法/HLD，CP5 批准全量设计证据后才可 fixture-only 实现。任何真实 lake/NAS、credential、provider、真实 computation/producer binding、runtime、write、trading、publish/deploy 或 Git remote write 均未授权。CR173 只关闭 CR172 的 methodology prerequisite，不解决五字段具体值、data owner identity、fresh conflict precheck、strategy identity 和 runtime/real-producer binding，也不会自动关闭、恢复或批准 CR172。CR172 可按 `DQ-CR172-003` 保留 effective count unavailable 的降级绑定，但不得因此声称 `c1_computable`。

成功标准：CP5 前实现数 `0`；上述禁止操作每项 `0`；CR173 CP8 后 CR172 自动关闭/自动恢复/自动 activation 数 `0/0/0`；CR172 外部前置归属审计 `5/5`；five-field + data-owner 冻结、fresh precheck、strategy identity、runtime binding 均保持独立 owner/门禁。

## CR173 Non-Functional Requirements

| NFR ID | 维度 | 要求 | 精确度量 |
|---|---|---|---|
| NFR-CR173-001 | 正确性 | participation-ratio estimand、方法 limitation 和 raw/effective-dimensionality 边界可审计。 | alias/default/fallback=`0`；Li–Ji/BH/FWER/DSR calibration claim=`0`；失败类 `8/8` fail-closed。 |
| NFR-CR173-002 | 确定性 | 相同规范化 vector、方法版本和参数产生稳定结果。 | `6` 类 × `3` 次；每组 canonical result=`1`。 |
| NFR-CR173-003 | 可追溯性 | 七字段 evidence 全量绑定方法与 lineage/computation refs。 | schema `7/7`；orphan refs=`0`。 |
| NFR-CR173-004 | 安全性 | 只允许本地 fixture/static 设计和后续验证。 | 真实数据/credential/provider/write/runtime/trading/remote-write 各=`0`。 |

## CR173 CP2 Decisions

| DQ | 待决问题 | 推荐方案 | 备选方案 | 优劣与风险 | 回退 / 切换条件 | 状态 |
|---|---|---|---|---|---|---|
| DQ-CR173-001 | effective-count 的产品 estimand 如何与 raw count 区分？ | 冻结为相关性/依赖调整后的独立试验等价量；严禁 alias。 | 保持全量 typed-unavailable，暂不设计 estimator。 | 推荐可创造方法价值但需 CP3 审慎选型；备选最安全但不能解除不可计算。 | CP3 无法证明可识别性或偏差边界时回退 typed-unavailable。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-002 | CP3 必须冻结哪些输入合同与有效性前提？ | 冻结输入类别 inventory、有效域、依赖表示、方法/版本/hash、假设和切换条件，覆盖率 100%。 | 先做方法 Spike，CP3 不批准正式 HLD。 | 推荐可直接进入可评审设计；备选降低错误选型风险但延长交付。 | 候选方法缺稳定输入映射或 owner 无法接受假设时转 Spike。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-003 | 缺失、无效或矛盾输入如何处理？ | 缺失/不足=`typed_unavailable`，矛盾/篡改=`blocked`，永不退回 raw。 | 所有失败统一 `typed_unavailable`。 | 推荐保留安全严重度差异；备选简单但弱化篡改信号。 | 若 CP3 证明 consumer 只支持单一失败态，可统一 unavailable 但必须保留 machine reason 和无 alias。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-004 | consumer evidence schema 是否固定七字段？ | 固定 `7/7` 字段及 provenance，不允许隐式默认。 | CP3 增加字段但不得删除七个基线字段。 | 推荐使 CP2 可测且兼容；备选允许设计扩展但增加 schema 负担。 | 仅在 CP3 证明新增字段是可审计性 blocker 时扩展并记录 ADR。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-005 | estimator 是否绑定具体策略身份？ | strategy-agnostic，具体身份完全留给 CR172 activation。 | 针对一个 fixture strategy profile 作为非身份化测试标签。 | 推荐避免授权混合；备选便于示例但有被误读为真实策略的风险。 | 任何标签可回链真实策略时删除标签，改用纯合成 case ID。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-006 | 如何验收 deterministic golden vectors？ | 六类 `6/6`，每类重复 `3/3`，合法组唯一结果，无效组零 available。 | 增加随机 property tests，但不替代固定 vectors。 | 推荐确定且审计成本低；备选扩展覆盖但可能引入随机脆弱性。 | 固定 vectors 通过后，CP5 可把 seeded property tests 作为附加项。 | RESOLVED-APPROVED-CP2 |
| DQ-CR173-007 | C1 consumer projection 可产生哪些声明？ | 只产生 offline typed evidence；real evidence、Stage3、admission、aggregate 全 false。 | 只交付 estimator，不做 projection。 | 推荐证明实际 consumer 价值；备选 blast radius 更小但保留 public C1 unavailable。 | 若 CP3 发现公共 C1 contract 需跨域修改，拆 projection 为后续 CR 并保持本 CR estimator-only。 | RESOLVED-APPROVED-CP2-CONDITION-TRIGGERED-CP3 |
| DQ-CR173-008 | CR173 与 CR172 的恢复和授权关系是什么？ | CR173 是前置；完成后不自动恢复，须 five fields + fresh precheck + CR172 CP2。 | CR173 完成后保持 CR172 blocked，等待用户另行发起。 | 推荐保留可执行恢复链且不越权；备选更保守但增加人工重启成本。 | 任一恢复前置不满足时采用备选并保持 blocked。 | RESOLVED-APPROVED-CP2 |

CR173 的 CP2 未决项=`0`；八项推荐已于 2026-07-16 获用户批准。CP3 将 `DO-CR173-CP3-001` 判定为 `PASS`，方法限定为 participation-ratio 二阶 effective dimensionality；将 `DO-CR173-CP3-002` 判定为 `PASS_BY_SPLIT`，public C1 projection/write 从 CR173 移除并只登记 backlog 候选。CR173 已完成后续 Story/LLD/fixture 实现/验证并以 `closed/cp8_closed/READY_WITH_RISK` 交付；该完成不改变 8 REQ / 8 SC / 8 matrix trace，也不产生 CR172 activation、public C1 或真实 runtime 授权。
