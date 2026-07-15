---
status: confirmed-cp2
version: "1.9"
source_scenarios: "docs/product/SCENARIOS.yaml"
source_requirements: "docs/product/REQUIREMENTS.md"
cr_id: "CR-170"
template_deviation_reason: "CR157 uses Scenario/Requirement/Test Layer/Validation Mode columns to preserve gate and no-runtime evidence mapping; coverage statistics remain present below."
---

# Test Matrix

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级测试覆盖矩阵草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充 frontmatter 和模板偏差原因。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 覆盖矩阵；保留 CR157 baseline rows。 |
| v0.4 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review workflow 覆盖矩阵和产品基线刷新检查。 |
| v0.5 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 evidence-availability、fail-closed、CR155 negative regression、no-overclaim 和九文档刷新静态覆盖。 |
| v0.6 | 2026-07-11 | meta-pm | CR163 追加 12 个 P0 lineage lifecycle、count、integrity、permission 和 CR155 regression 场景映射。 |
| v0.7 | 2026-07-11 | meta-pm | 回填 SGQ-A 语义，明确 2 条 producer chains / 4 个 mappings，以及 present / typed_unavailable / blocked 与 C1 raw-input-only 验证。 |
| v0.8 | 2026-07-12 | meta-pm | 追加 CR164 13 个 P0 method/input/disagreement/boundary/recovery/permission/compatibility/precheck 场景的 fixture/static 覆盖。 |
| v0.9 | 2026-07-13 | host-orchestrator-inline | 追加 CR166 10 个 P0 与 1 个 P1 场景映射，覆盖 daily/ML、8 类 fail-closed、event applicability、Stage claim 与零外部操作。 |
| v1.0 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 批准；11/11 场景保持 planned fixture/static，作为 CP3 架构与后续 CP5/CP7 验证输入。 |
| v1.1 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 批准；11/11 场景映射到五个正式 Story 和 CP5 LLD/Feature 测试设计，验证仍为 planned、未执行。 |
| v1.2 | 2026-07-13 | host-orchestrator-inline | CR168 增量追加 16 个场景的 planned fixture/static 覆盖，精确覆盖 10/10 fail-closed、2/2 fixture、Gate 4 联合边界、权限与 CR155 regression。 |
| v1.3 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见新增 `SC-CR168-B02`，覆盖字段级与通用 na-reason 逃逸必须由 projection 阻断；CR168 场景 17/17、P0 16、P1 1，10 类 C3 输入 fail-closed 仍为 10/10。 |
| v1.4 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准；把 B01/B02 的 planned evidence 收紧为 adapter-only 调用、8/8 禁止键拒绝、逃逸路径 canonical 调用=0、safe absent 路径 post-call 非 PASS，且不修改 canonical Gate 4。 |
| v1.5 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 17/17 C4 fixture/static scenarios 的 requirement/matrix 覆盖；包含 CR168 C3-only 回归、strict C3+C4 joint adapter、CR155 blocked 和 alpha-decay applicability，均未执行实现或真实数据操作。 |
| v1.6 | 2026-07-14 | host-orchestrator-inline | CR169 CP2 评审整改与批准：E01 追加 `stage3_entry_ready=false` 与 CP8/formal Stage 2 exit 的 7/7 核验期望；场景、QAC 和范围计数不变。 |
| v1.7 | 2026-07-14 | host-orchestrator-inline-meta-se | CR169 CP4：把 17/17 场景映射到 S01–S05 full-lld 与 5 个串行 Wave；覆盖数量不变，仍未授权实现。 |
| v1.8 | 2026-07-15 | host-orchestrator-inline-meta-pm | 增量追加 CR170 20/20 场景的 planned coverage，包含 Gate 1 三层 masked-escape 断言、Gate 1-5 五态、底层 merge 保留回归、tier admission、adapter/CR155/Stage3 边界。 |
| v1.9 | 2026-07-15 | host-orchestrator-inline | 回填 CR170 CP2 批准并补 consumer 边界：FU-006 独立验证者为 future consumer，本 CR 的 planned verification 由 Gate 维护者自验证承担；20/20 场景、19 P0/1 P1、21/21 inventory 与 15 QAC 不变。 |

## 状态

- 文档状态：confirmed-cp2（CR170 基线）
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168` / `CR-169` / `CR-170`
- 当前门禁：CR170 CP2 已批准，进入 CP3 HLD/ADR 人工门禁；coverage 仍是 planned evidence，不代表 Story、实现、验证或真实数据操作已执行

## Coverage Matrix

| Scenario | Requirement | Test Layer | Validation Mode | Expected Evidence | Priority | Status |
|---|---|---|---|---|---|---|
| SC-CR157-P01 | REQ-CR157-001, REQ-CR157-003 | unit / contract | fixture/static | mature admission package builder contract test | P0 | planned |
| SC-CR157-P02 | REQ-CR157-002, REQ-CR157-003 | contract / doc-review | static | handoff contract validation and traceability review | P0 | planned |
| SC-CR157-N01 | REQ-CR157-001, REQ-CR157-003 | unit | fixture/static | missing evidence fail-closed test | P0 | planned |
| SC-CR157-N02 | REQ-CR157-004 | unit / security | fixture/static | no-runtime guard counter test | P0 | planned |
| SC-CR157-B01 | REQ-CR157-006 | review | static | MVP scope and backlog review | P1 | planned |
| SC-CR157-A01 | REQ-CR157-007 | workflow / gate | static | CP2-before-design route check | P0 | planned |
| SC-CR158-P01 | REQ-CR158-001, REQ-CR158-002, REQ-CR158-003 | contract / unit | fixture/static | shared adapter core + event/ML typed extension contract tests | P0 | planned |
| SC-CR158-P02 | REQ-CR158-004 | contract / traceability | static | evidence index typed refs-only validation | P0 | planned |
| SC-CR158-N01 | REQ-CR158-002, REQ-CR158-003 | unit / negative | fixture/static | missing adapter P0 refs fail-closed tests | P0 | planned |
| SC-CR158-N02 | REQ-CR158-005 | unit / security | fixture/static | forbidden operation counter fail-closed tests | P0 | planned |
| SC-CR158-B01 | REQ-CR158-006 | workflow / gate | static | CP2-to-CP3/CP5 route guard check | P0 | planned |
| SC-CR158-A01 | REQ-CR158-007 | doc-review / release | static | release wording no-runtime overclaim review | P1 | planned |
| SC-CR160-P01 | REQ-CR160-001, REQ-CR160-002, REQ-CR160-004 | design-review / contract | static | HLD Stage 4 object and decision table review | P0 | verified-cp7 |
| SC-CR160-P02 | REQ-CR160-003, REQ-CR160-007 | checklist / traceability | static | layered observation review checklist and product baseline review | P0 | verified-cp8 |
| SC-CR160-N01 | REQ-CR160-004, REQ-CR160-005, REQ-CR160-006 | seed-classification / negative | existing-evidence | CR155 blocked_admission_failed classification review | P0 | verified-cp7 |
| SC-CR160-N02 | REQ-CR160-001, REQ-CR160-002 | design-review / negative | static | missing observation plan instance fail-closed review | P0 | verified-cp7 |
| SC-CR160-A01 | REQ-CR160-006 | security / release | static | CP8 non-authorization wording and release boundary review | P0 | verified-cp8 |
| SC-CR160-B01 | REQ-CR160-007 | product-baseline / traceability | static | 6 product docs CR160 promotion and revision-record check | P0 | verified-cp8 |
| SC-CR161-P01 | REQ-CR161-001 | contract / traceability | static | seven-object evidence matrix and C1-C4 mapping review | P0 | planned-cp7 |
| SC-CR161-N01 | REQ-CR161-002 | negative / fail-closed | static | mandatory missing evidence is explicitly typed_unavailable and blocks admission | P0 | planned-cp7 |
| SC-CR161-N02 | REQ-CR161-003 | existing-evidence / negative | static | CR155 remains blocked without reconstructed lineage, p-values or folds | P0 | planned-cp7 |
| SC-CR161-B01 | REQ-CR161-004 | boundary / release | static | product and feature wording contains no computed-proof or runtime readiness claim | P0 | planned-cp7 |
| SC-CR162-P01 | REQ-CR161-001, REQ-CR161-005 | product-baseline / traceability | static | all 9 promised documents contain CR161 references and CR162 revision records | P0 | planned-cp7 |
| SC-CR163-P01 | REQ-CR163-001, REQ-CR163-005 | contract / inventory | fixture/static | 4/4 instrumentation mappings across 2 deduplicated producer chains and pre-search ordering | P0 | planned |
| SC-CR163-P02 | REQ-CR163-002, REQ-CR163-003 | unit / lineage | fixture/static | append-only event graph and distinct-trial recount | P0 | planned |
| SC-CR163-P03 | REQ-CR163-004, REQ-CR163-006, REQ-CR163-007 | contract / integration | fixture/static | deterministic seal; completeness/ref validation; present only when all pass; C1 still non-computable | P0 | planned |
| SC-CR163-N01 | REQ-CR163-001, REQ-CR163-007 | negative / precheck | fixture/static | uninstrumented typed_unavailable; post-hoc/incomplete/invalid lineage blocked | P0 | planned |
| SC-CR163-N02 | REQ-CR163-002, REQ-CR163-007 | negative / integrity | fixture/static | duplicate identity conflict fail-closed | P0 | planned |
| SC-CR163-B01 | REQ-CR163-003 | boundary / count | fixture/static | retry/seed/trial/attempt count assertions | P0 | planned |
| SC-CR163-B02 | REQ-CR163-006, REQ-CR163-008 | boundary / claim-ceiling | static | effective count typed-unavailable, empty ref/method | P0 | planned |
| SC-CR163-F01 | REQ-CR163-002, REQ-CR163-003 | failure-recovery / lineage | fixture/static | failed/cancelled/excluded retention and count | P0 | planned |
| SC-CR163-R01 | REQ-CR163-004, REQ-CR163-007 | recovery / version-chain | fixture/static | immutable v1 plus valid superseding v2 | P0 | planned |
| SC-CR163-T01 | REQ-CR163-004, REQ-CR163-007 | security / tamper | fixture/static | post-seal mutation hash mismatch fail-closed | P0 | planned |
| SC-CR163-A01 | REQ-CR163-008 | permission / security | fixture/static | forbidden operation counters all zero; non-zero fixture blocked | P0 | planned |
| SC-CR163-G01 | REQ-CR163-006, REQ-CR163-008 | negative-regression / existing-evidence | static | CR155 remains blocked without backfill | P0 | planned |
| SC-CR164-P01 | REQ-CR164-001..004 | contract / method-provenance | fixture/static | four approved method evidences bound to one sealed family | P0 | planned |
| SC-CR164-P02 | REQ-CR164-005, REQ-CR164-007 | determinism / integration | fixture/static | 10 reruns -> 1 hash; three consumer projections | P0 | planned |
| SC-CR164-N01 | REQ-CR164-002..004 | negative / insufficiency | fixture/static | missing/partial method inputs fail closed | P0 | planned |
| SC-CR164-N02 | REQ-CR164-001, REQ-CR164-006, REQ-CR164-007 | negative / disagreement | fixture/static | no OR-pass; BH PASS + PBO FAIL is not clean PASS | P0 | planned |
| SC-CR164-B01 | REQ-CR164-004 | boundary / sufficiency | fixture/static | exact-floor and one-below-floor assertions | P0 | planned |
| SC-CR164-B02 | REQ-CR164-008 | boundary / claim-ceiling | fixture/static | dsr_input_method raw count; effective count unavailable/non-aliased | P0 | planned |
| SC-CR164-F01 | REQ-CR164-002, REQ-CR164-003, REQ-CR164-005 | failure-recovery / provenance | fixture/static | append-only corrected evidence recovery | P0 | planned |
| SC-CR164-T01 | REQ-CR164-004, REQ-CR164-005 | numerical / negative | fixture/static | NaN/Inf/degenerate six-class fail-closed matrix | P0 | planned |
| SC-CR164-H01 | REQ-CR164-002, REQ-CR164-005 | integrity / negative | fixture/static | ref/hash/count/membership mismatch blocked | P0 | planned |
| SC-CR164-A01 | REQ-CR164-009 | permission / security | fixture/static | forbidden operation counters 0; non-zero blocked | P0 | planned |
| SC-CR164-G01 | REQ-CR164-006, REQ-CR164-009 | negative-regression / existing-evidence | static | CR155 remains blocked without reconstruction | P0 | planned |
| SC-CR164-C01 | REQ-CR164-007, REQ-CR164-009 | compatibility / contract | fixture/static | UC-58 + UC-59/60 compatibility projection 3/3 | P0 | planned |
| SC-CR164-Q01 | REQ-CR164-001, REQ-CR164-009 | workflow / precheck | static | CP2-before-design, CP5-before-implementation and no-runtime route guards | P0 | planned |
| SC-CR166-P01 | REQ-CR166-001, REQ-CR166-005, REQ-CR166-007 | contract / determinism / integration | fixture/static | daily fold envelope; 10 reruns→1 hash; consumer projection 3/3 | P0 | planned |
| SC-CR166-P02 | REQ-CR166-001, REQ-CR166-008 | compatibility / contract | fixture/static | ML purged-embargo policy mapping without training/runtime | P0 | planned |
| SC-CR166-N01 | REQ-CR166-001, REQ-CR166-003 | negative / sufficiency | fixture/static | missing/empty fold set fail-closed | P0 | planned |
| SC-CR166-N02 | REQ-CR166-002 | temporal / leakage | fixture/static | reversed/overlapping boundary reason codes | P0 | planned |
| SC-CR166-N03 | REQ-CR166-002 | leakage / negative | fixture/static | missing purge with label overlap blocked | P0 | planned |
| SC-CR166-N04 | REQ-CR166-002 | boundary / leakage | fixture/static | one-below vs exact embargo threshold assertions | P0 | planned |
| SC-CR166-N05 | REQ-CR166-003 | numerical / negative | fixture/static | missing/NaN/Inf metric 3/3 fail-closed | P0 | planned |
| SC-CR166-N06 | REQ-CR166-004 | integrity / lineage | fixture/static | missing/ref/hash/membership mismatch; orphan refs=0 | P0 | planned |
| SC-CR166-A01 | REQ-CR166-009 | permission / security | fixture/static | external ref dereference=0; forbidden counters=0 | P0 | planned |
| SC-CR166-H01 | REQ-CR166-005, REQ-CR166-006 | determinism / integrity | fixture/static | canonical equivalence and tamper mismatch; unknown component no-PASS | P0 | planned |
| SC-CR166-E01 | REQ-CR166-008 | compatibility / design-review | static | explicit event N/A decision; no empty producer | P1 | planned-CP7-static |
| SC-CR168-P01 | REQ-CR168-001, REQ-CR168-002, REQ-CR168-003, REQ-CR168-005 | contract / arithmetic / determinism | fixture/static | daily C3 component；9/9 inputs；10 reruns→1 hash；recomputable gross-to-net | P0 | planned-after-CP5 |
| SC-CR168-P02 | REQ-CR168-001, REQ-CR168-007 | compatibility / contract | fixture/static | daily + ML package attach uses one C3 semantic | P0 | planned-after-CP5 |
| SC-CR168-N01 | REQ-CR168-002, REQ-CR168-004 | negative / sufficiency | fixture/static | missing gross/pre-cost basis fail-closed | P0 | planned-after-CP5 |
| SC-CR168-N02 | REQ-CR168-002, REQ-CR168-004 | negative / sufficiency | fixture/static | missing trade/turnover/notional basis fail-closed | P0 | planned-after-CP5 |
| SC-CR168-N03 | REQ-CR168-002, REQ-CR168-004 | negative / model-provenance | fixture/static | missing cost model/version fail-closed | P0 | planned-after-CP5 |
| SC-CR168-N04 | REQ-CR168-003, REQ-CR168-004 | numerical / negative | fixture/static | NaN/Inf variants fail-closed | P0 | planned-after-CP5 |
| SC-CR168-N05 | REQ-CR168-003, REQ-CR168-004 | numerical / policy | fixture/static | unauthorized negative/impossible cost blocked | P0 | planned-after-CP5 |
| SC-CR168-N06 | REQ-CR168-002, REQ-CR168-004 | unit / basis | fixture/static | unit/price/notional basis mismatch blocked | P0 | planned-after-CP5 |
| SC-CR168-N07 | REQ-CR168-002, REQ-CR168-004 | currency / calendar / basis | fixture/static | cross-field mismatch without explicit conversion blocked | P0 | planned-after-CP5 |
| SC-CR168-N08 | REQ-CR168-003, REQ-CR168-004 | arithmetic / reconciliation | fixture/static | itemized/total/gross/net mismatch blocked | P0 | planned-after-CP5 |
| SC-CR168-N09 | REQ-CR168-002, REQ-CR168-004, REQ-CR168-008 | lineage / authorization | fixture/static | missing/inconsistent lineage/provenance/auth fail-closed；dereference=0 | P0 | planned-after-CP5 |
| SC-CR168-N10 | REQ-CR168-004, REQ-CR168-005 | integrity / tamper | fixture/static | canonical equivalence stable；hash tamper blocked | P0 | planned-after-CP5 |
| SC-CR168-B01 | REQ-CR168-006, REQ-CR168-009 | integration / fail-closed | fixture/static | adapter-only C3 projection + C4 typed_unavailable absent；canonical returns non-PASS；adapter-external direct calls=0 | P0 | planned-after-CP5 |
| SC-CR168-B02 | REQ-CR168-006, REQ-CR168-009 | projection-guard / negative-integration | fixture/static | exact 8/8 forbidden reason keys rejected by presence before Gate 4；canonical calls=0；PASS=0 | P0 | planned-after-CP5 |
| SC-CR168-A01 | REQ-CR168-008 | permission / security | fixture/static | real-data/TCA/runtime/trading/remote-write counters all 0 | P0 | planned-after-CP5 |
| SC-CR168-G01 | REQ-CR168-006, REQ-CR168-009 | negative-regression / existing-evidence | static | CR155 admission remains BLOCKED；paper_candidate=false；promotion=0 | P0 | planned-after-CP5 |
| SC-CR168-E01 | REQ-CR168-007, REQ-CR168-009 | applicability / boundary | static | event-specific producer explicit N/A/deferred；count=0 | P1 | planned-static-review |
| SC-CR169-P01 | REQ-CR169-001, REQ-CR169-002, REQ-CR169-003, REQ-CR169-005 | contract / determinism | fixture/static | complete daily C4 component; 10 reruns -> 1 hash | P0 | S01,S02,S05 planned-after-CP5 |
| SC-CR169-P02 | REQ-CR169-002, REQ-CR169-007 | compatibility / contract | fixture/static | daily + ML use one C4 arithmetic contract | P0 | S03,S05 planned-after-CP5 |
| SC-CR169-N01 | REQ-CR169-002, REQ-CR169-004 | negative / sufficiency | fixture/static | missing correlation header or synthetic ADV basis fails closed | P0 | S01,S05 planned-after-CP5 |
| SC-CR169-N02 | REQ-CR169-003, REQ-CR169-004 | negative / numeric | fixture/static | missing/invalid participation cap or method fails closed | P0 | S01,S02,S05 planned-after-CP5 |
| SC-CR169-N03 | REQ-CR169-003, REQ-CR169-004 | negative / model | fixture/static | missing capacity curve/ref fails closed | P0 | S01,S02,S05 planned-after-CP5 |
| SC-CR169-N04 | REQ-CR169-003, REQ-CR169-004 | negative / model | fixture/static | missing liquidity sizing/ref fails closed | P0 | S01,S02,S05 planned-after-CP5 |
| SC-CR169-N05 | REQ-CR169-003, REQ-CR169-004 | numerical / negative | fixture/static | non-finite, negative or infeasible C4 values fail closed | P0 | S01,S02,S05 planned-after-CP5 |
| SC-CR169-N06 | REQ-CR169-002, REQ-CR169-004 | unit / calendar | fixture/static | unit/currency/calendar/as-of/horizon mismatch blocked | P0 | S01,S05 planned-after-CP5 |
| SC-CR169-N07 | REQ-CR169-002, REQ-CR169-006 | integration / boundary | fixture/static | C3/C4 correlation mismatch rejected before canonical Gate4 | P0 | S01,S04,S05 planned-after-CP5 |
| SC-CR169-N08 | REQ-CR169-002, REQ-CR169-004, REQ-CR169-008 | lineage / authorization | fixture/static | missing/inconsistent lineage/auth fails closed; dereference=0 | P0 | S01,S05 planned-after-CP5 |
| SC-CR169-N09 | REQ-CR169-004, REQ-CR169-005 | integrity / tamper | fixture/static | canonical identity tamper blocked | P0 | S01,S03,S05 planned-after-CP5 |
| SC-CR169-N10 | REQ-CR169-004, REQ-CR169-006, REQ-CR169-008 | injection / permission | fixture/static | reason/flat injection and real-capacity claim rejected | P0 | S04,S05 planned-after-CP5 |
| SC-CR169-B01 | REQ-CR169-007, REQ-CR169-009 | regression / fail-closed | static | CR168 C3-only absent-C4 adapter unchanged and non-PASS | P0 | S05 planned-after-CP5 |
| SC-CR169-B02 | REQ-CR169-001, REQ-CR169-003, REQ-CR169-006 | strict joint integration | fixture/static | exact verified C3+C4 payload yields fixture contract PASS only | P0 | S04,S05 planned-after-CP5 |
| SC-CR169-B03 | REQ-CR169-006, REQ-CR169-009 | postcondition / negative | fixture/static | unexpected canonical result contained by public callable double | P0 | S04,S05 planned-after-CP5 |
| SC-CR169-G01 | REQ-CR169-006, REQ-CR169-009 | negative-regression | static | CR155 remains BLOCKED; paper_candidate=false; promotion=0 | P0 | S05 planned-after-CP5 |
| SC-CR169-E01 | REQ-CR169-008, REQ-CR169-009 | applicability / boundary | static / CP8-exit-review | alpha-decay calculator=0; stage3_entry_ready=false; 7/7 Stage 2 exit verification required | P1 | S05/CP8 planned-static-review |
| SC-CR170-P01 | REQ-CR170-001, REQ-CR170-002, REQ-CR170-004 | contract / positive | fixture/static | all applicable Gate1-5 mandatory evidence present without reason substitution | P0 | planned-after-CP5 |
| SC-CR170-P02 | REQ-CR170-002, REQ-CR170-004, REQ-CR170-006 | boundary / policy | fixture/static | complete structured N/A retains owner/scope/profile and never unconditional PASS | P0 | planned-after-CP5 |
| SC-CR170-N01 | REQ-CR170-003, REQ-CR170-004 | Gate1 masked-escape / negative | fixture/static | multiple-testing field classification + mandatory claim + final worst-state 3/3 | P0 | planned-after-CP5 |
| SC-CR170-N02 | REQ-CR170-003, REQ-CR170-004 | Gate1 masked-escape / negative | fixture/static | FDR field classification + mandatory claim + final worst-state 3/3 | P0 | planned-after-CP5 |
| SC-CR170-N03 | REQ-CR170-001, REQ-CR170-004 | Gate2 / negative | fixture/static | split/WF/OOS generic reason escape produces zero PASS | P0 | planned-after-CP5 |
| SC-CR170-N04 | REQ-CR170-001, REQ-CR170-004 | Gate2 / boundary | fixture/static | purge/embargo/event-gap incomplete boundary remains non-PASS | P0 | planned-after-CP5 |
| SC-CR170-N05 | REQ-CR170-001, REQ-CR170-004 | Gate3 / negative | fixture/static | PIT/survivorship generic reason does not waive evidence | P0 | planned-after-CP5 |
| SC-CR170-N06 | REQ-CR170-001, REQ-CR170-004, REQ-CR170-007 | Gate4 / negative-regression | fixture/static | field/generic reason escape non-PASS plus adapter regressions | P0 | planned-after-CP5 |
| SC-CR170-N07 | REQ-CR170-004, REQ-CR170-005 | Gate5 / integration | fixture/static | artifact NEEDS_REVIEW remains visible and non-PASS | P0 | planned-after-CP5 |
| SC-CR170-N08 | REQ-CR170-002, REQ-CR170-004 | semantic-state / boundary | fixture/static | incomplete N/A is distinct from complete N/A | P0 | planned-after-CP5 |
| SC-CR170-N09 | REQ-CR170-002, REQ-CR170-004 | generic-reason / negative | fixture/static | one generic reason satisfies zero multiple mandatory units | P0 | planned-after-CP5 |
| SC-CR170-B01 | REQ-CR170-005 | Gate6 merge / protected-regression | fixture/static | build_shared_gate_summary propagates NEEDS_REVIEW; no rewrite without failure | P0 | planned-after-CP5 |
| SC-CR170-B02 | REQ-CR170-006 | tier-policy / boundary | fixture/static | T0 mandatory NEEDS_REVIEW remains diagnostic and non-PASS | P0 | planned-after-CP5 |
| SC-CR170-B03 | REQ-CR170-006 | tier-policy / boundary | fixture/static | T1 mandatory NEEDS_REVIEW -> BLOCKED | P0 | planned-after-CP5 |
| SC-CR170-B04 | REQ-CR170-006 | tier-policy / boundary | fixture/static | T2 mandatory NEEDS_REVIEW -> BLOCKED | P0 | planned-after-CP5 |
| SC-CR170-B05 | REQ-CR170-006, REQ-CR170-009 | authorization / boundary | fixture/static | T3 -> NOT_AUTHORIZED/no PASS | P0 | planned-after-CP5 |
| SC-CR170-R01 | REQ-CR170-007 | CR168 adapter / regression | fixture/static | C3-only defense-in-depth guard remains intact | P0 | planned-after-CP5 |
| SC-CR170-R02 | REQ-CR170-007 | CR169 adapter / regression | fixture/static | strict joint defense-in-depth guard remains intact | P0 | planned-after-CP5 |
| SC-CR170-G01 | REQ-CR170-009 | CR155 / negative-regression | existing-evidence/static | CR155 remains BLOCKED and paper_candidate=false | P0 | planned-after-CP5 |
| SC-CR170-E01 | REQ-CR170-008, REQ-CR170-009 | applicability / static review | static | current runner integration=0; legacy Stage3 claims require independent revalidation | P1 | planned-static-review |

## Coverage Summary

| Metric | Value |
|---|---:|
| P0 requirements | 18 |
| P0 scenarios | 16 |
| P0 scenarios with planned coverage | 16 |
| External runtime tests authorized | 0 |
| Provider / NAS / credential tests authorized | 0 |
| Trading / simulation / live tests authorized | 0 |
| Real event feed tests authorized | 0 |
| Real model training / registry tests authorized | 0 |
| CR160 product baseline docs refreshed | 6 |
| CR161 / CR162 baseline documents refreshed | 9 |
| CR163 deduplicated producer chains | 2 |
| CR163 frozen P0 instrumentation mappings | 4 |
| CR163 P0 scenarios | 12 |
| CR163 P0 scenarios with planned coverage | 12 |
| CR163 effective-trial computations authorized | 0 |
| CR164 approved MVP methods | 4 |
| CR164 P0 scenarios | 13 |
| CR164 P0 scenarios with planned coverage | 13 |
| CR164 quantitative acceptance criteria | 10 |
| CR164 external/runtime tests authorized | 0 |
| CR166 P0 scenarios | 10 |
| CR166 P0 scenarios with planned coverage | 10 |
| CR166 P1 applicability scenarios | 1 |
| CR166 quantitative acceptance criteria | 12 |
| CR166 P0 fixture families | 2 |
| CR166 existing-consumer projections | 3 |
| CR166 external/runtime tests authorized | 0 |
| CR168 P0 scenarios | 16 |
| CR168 P0 scenarios with planned coverage | 16 |
| CR168 P1 applicability scenarios | 1 |
| CR168 quantitative acceptance criteria | 15 |
| CR168 typed component / active schema | 1 / 1 |
| CR168 input field families | 9/9 |
| CR168 fail-closed classes | 10/10 |
| CR168 fixture families | 2/2 |
| CR168 C3-to-Gate-4 projections | 1 |
| CR168 C4 calculators / event producers | 0 / 0 |
| CR168 external/runtime tests authorized | 0 |
| CR169 P0 scenarios | 16 |
| CR169 P0 scenarios with planned coverage | 16 |
| CR169 P1 applicability scenarios | 1 |
| CR169 quantitative acceptance criteria | 15 |
| CR169 typed component / active schema | 1 / 1 |
| CR169 fail-closed classes | 12/12 |
| CR169 fixture families | 2/2 |
| CR169 strict C3+C4 Gate4 fixture adapters | 1 |
| CR169 canonical/aggregate modifications | 0 / 0 |
| CR169 external/runtime tests authorized | 0 |
| CR170 P0 scenarios | 19 |
| CR170 P0 scenarios with planned coverage | 19 |
| CR170 P1 applicability scenarios | 1 |
| CR170 quantitative acceptance criteria | 15 |
| CR170 Gate1-5 policy inventory | 21/21 |
| CR170 business semantic states | 5/5 |
| CR170 adapter regressions | 2/2 |
| CR170 current-runner/aggregate integration modifications | 0 / 0 |
| CR170 external/runtime tests authorized | 0 |

## Notes

- CR157 verification must use fixture/static/no-lake evidence unless a later authorization gate explicitly changes scope.
- A CP2 approval authorizes only product/design progression, not implementation and not runtime execution.
- CR158 verification must use fixture/static/no-runtime evidence. CP2 approval does not authorize real event feed, real model training, model registry write, provider/lake/NAS/credential access, runtime, trading, publish or Git remote write.
- CR160 verification is design-only and existing-evidence-only. CP8 approval does not authorize code implementation, checker/schema, new lake access, observation execution, simulation, paper, live, trading, publish or deployment.
- CR161 / CR162 verification is static documentation and existing-evidence traceability only. The matrix does not represent FDR/PBO/DSR, fold-level OOS, TCA, market-impact or capacity computation.
- CR163 verification remains fixture/static unless a later gate grants separate runtime/data authorization. Future native instrumented runs may set `ExperimentFamilyManifest=present` only after seal/completeness/reference/count/tamper validation; uninstrumented paths remain `typed_unavailable`; invalid/tampered lineages are `blocked`. This prepares only the C1 raw-lineage input and does not make C1 computable.
- CR170 CP2 前仅确认产品语义和 planned coverage；`build_shared_gate_summary` 现有传播必须先回归再决定是否修改，`resolve_admission_policy` 的 tier/admission 边界留 CP3 冻结。当前 runner 接入、真实数据、aggregate 与 CR155 promotion 均未授权。
- CR164 verification is fixture/static only. Four methods are mandatory but no OR-pass is allowed; DSR raw count must be explicitly identified and never alias effective count; WRC/SPA stationary-bootstrap parameter selection is a CP3 obligation. UC-59/60 rows prove compatibility semantics only, not adapter implementation or real feed/training authorization.
- CR166 验证仅允许 fixture/static：daily multifactor 与 ML compatibility 为 P0；event 为 CP3 applicability/P1。任何真实 fold/OOS 数据、lake/NAS/provider/runtime 或外部 ref 均不得解引用。CP8 也只能声明桥接 foundation，不得声明 Stage 3 已启动或真实 OOS evidence 可用。
- CR168 coverage 只描述 CP2 待批准的 fixture/static 验证合同。Gate 4 是 C3+C4 联合门禁；C4 reserved/not-built/typed_unavailable 必须由 projection 映射为三个 refs absent-no-na-reason，任何字段级或通用 na-reason 逃逸都必须在 projection 侧阻断，capacity/aggregate PASS=`0`。CP2 不授权 HLD 之外的实现，也不授权真实 TCA、真实 impact calibration、真实数据、runtime、C4、event producer、交易或远端写入。
- CR169 coverage 描述已获 CP2 批准但尚未实现的 C4 fixture/static 合同。CR168 C3-only adapter 保持 absent-C4 fail-closed；CR169 的新 joint adapter 仅组合经验证的 C3+C4 components、构造精确七字段 Gate4 payload，并可证明 `gate4_fixture_contract_pass=1`，不产生 aggregate/capacity admission PASS、真实 capacity claim 或 CR155 promotion。alpha-decay 仅为 CP3 disposition；`stage3_entry_ready=false`，正式 Stage 2 exit 必须另以 7/7 核验证据决定。
