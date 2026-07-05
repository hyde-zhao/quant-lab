---
status: draft
version: "0.3"
source_scenarios: "docs/product/SCENARIOS.yaml"
source_requirements: "docs/product/REQUIREMENTS.md"
cr_id: "CR-158"
template_deviation_reason: "CR157 uses Scenario/Requirement/Test Layer/Validation Mode columns to preserve gate and no-runtime evidence mapping; coverage statistics remain present below."
---

# Test Matrix

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级测试覆盖矩阵草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充 frontmatter 和模板偏差原因。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 覆盖矩阵；保留 CR157 baseline rows。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158`
- 当前门禁：CR158 CP2 pending user review

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

## Coverage Summary

| Metric | Value |
|---|---:|
| P0 requirements | 11 |
| P0 scenarios | 10 |
| P0 scenarios with planned coverage | 10 |
| External runtime tests authorized | 0 |
| Provider / NAS / credential tests authorized | 0 |
| Trading / simulation / live tests authorized | 0 |
| Real event feed tests authorized | 0 |
| Real model training / registry tests authorized | 0 |

## Notes

- CR157 verification must use fixture/static/no-lake evidence unless a later authorization gate explicitly changes scope.
- A CP2 approval authorizes only product/design progression, not implementation and not runtime execution.
- CR158 verification must use fixture/static/no-runtime evidence. CP2 approval does not authorize real event feed, real model training, model registry write, provider/lake/NAS/credential access, runtime, trading, publish or Git remote write.
