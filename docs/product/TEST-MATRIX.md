---
status: draft
version: "0.8"
source_scenarios: "docs/product/SCENARIOS.yaml"
source_requirements: "docs/product/REQUIREMENTS.md"
cr_id: "CR-164"
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

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164`
- 当前门禁：CR164 CP3 已批准、CP4 PASS；5/5 LLD ready，等待 CP5 全量确认

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

## Notes

- CR157 verification must use fixture/static/no-lake evidence unless a later authorization gate explicitly changes scope.
- A CP2 approval authorizes only product/design progression, not implementation and not runtime execution.
- CR158 verification must use fixture/static/no-runtime evidence. CP2 approval does not authorize real event feed, real model training, model registry write, provider/lake/NAS/credential access, runtime, trading, publish or Git remote write.
- CR160 verification is design-only and existing-evidence-only. CP8 approval does not authorize code implementation, checker/schema, new lake access, observation execution, simulation, paper, live, trading, publish or deployment.
- CR161 / CR162 verification is static documentation and existing-evidence traceability only. The matrix does not represent FDR/PBO/DSR, fold-level OOS, TCA, market-impact or capacity computation.
- CR163 verification remains fixture/static unless a later gate grants separate runtime/data authorization. Future native instrumented runs may set `ExperimentFamilyManifest=present` only after seal/completeness/reference/count/tamper validation; uninstrumented paths remain `typed_unavailable`; invalid/tampered lineages are `blocked`. This prepares only the C1 raw-lineage input and does not make C1 computable.
- CR164 verification is fixture/static only. Four methods are mandatory but no OR-pass is allowed; DSR raw count must be explicitly identified and never alias effective count; WRC/SPA stationary-bootstrap parameter selection is a CP3 obligation. UC-59/60 rows prove compatibility semantics only, not adapter implementation or real feed/training authorization.
