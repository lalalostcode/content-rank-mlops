# Content Ranking MLOps · Master PRD

Planning baseline for review, 20 November 2026.

## 1. Executive Summary

Prioritize a limited number of editorial investigations per client using reproducible batch scores and inspectable evidence.

## 2. Project Background

The internship capstone measured P@50 on the pooled top 50 items in each held-out fold, then averaged the five fold values equally. The historical blend scored 92.4% and the rule scored 46.4% under that protocol. The platform evaluates each client's queue independently and requires fresh validation. Reproduction of the historical score remains unverified. [Historical report](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/work/capstone_report.md)

## 3. Business Problem

Analysts need to choose which pages to investigate under a finite review budget and retain the evidence behind each decision.

## 4. Product Vision

Connect a dated observation to its ranking, analyst action and subsequent observation in one client-scoped workflow.

## 5. Goals and Non-Goals

Deliver insights, prioritization and auditability. Exclude automated content edits, causal attribution, search-algorithm prediction and guaranteed improvements. Rich recommendations and approvals belong to V2.

## 6. Target Users and Personas

Content analyst owns review decisions. ML operator validates releases and runs. Recruiter explores the synthetic demonstration.

## 7. User Journeys

[Walkthrough and exception paths](USER_JOURNEYS.md)

## 8. Functional Requirements

[FR-01 through FR-11](FUNCTIONAL_REQUIREMENTS.md) define actor, contract and verification.

## 9. Non-Functional Requirements

[Provisional quality budgets](NON_FUNCTIONAL_REQUIREMENTS.md) specify workload and measurement.

## 10. Data Requirements and Governance

Use authorized snapshots with cutoff, checksum and schema revision. A single snapshot supports queue ranking and analyst review. Show follow-up as unavailable until the same item has a comparable observation from a post-action window. Display both observation cutoffs and source provenance when comparing values. [Governance](../governance/DATA_GOVERNANCE.md) · [Analyst journey](USER_JOURNEYS.md)

## 11. Machine Learning Requirements

Binary relevance is observed `trend_direction=down`. Exclude identifiers, trend fields, product decisions and overlapping windows that reconstruct the label. Audit missingness by content type. Freeze a seeded final client holdout before development. Use five GroupKFold splits on the remaining clients, fit preprocessing on training clients and use contiguous client query groups for LambdaRank. Compare the fixed rule, base and engineered LambdaRank and their equal-weight blend on the same eligible items.

The capstone blended fold-level percentiles. The platform computes each component's percentile within a client's eligible inventory before averaging the two ranks. Use average ranks for score ties and content ID for final ordering ties. This changes the blend and requires fresh validation. Compute P@10, P@25 and P@50 per nonempty client using `min(K, eligible count)` as denominator, then average clients equally. Compute binary NDCG on the same cutoff. Tune only on development folds and evaluate the frozen candidate once on the final holdout. Ranking scores express order. A future authorized temporal backtest must split by cutoff and isolate outcome windows. [Evaluation protocol and reporting rules](../phases/PHASE_03_MACHINE_LEARNING.md#evaluation-protocol)

## 12. Frontend Requirements

React/Vite supports keyboard navigation, client-scoped filters, loading, stale data, empty and error states. Adapter interface is shared by API and static fixtures.

## 13. Backend Requirements

Spring Boot owns authorization, the review case lifecycle and query DTOs. Track review state per case and retain terminal cases in immutable history. A qualifying issue from a newer observation cutoff can start another case. Separate controllers, services and JPA repositories. Flyway migrations run before readiness. [Review lifecycle and persistence](../architecture/DATABASE_DESIGN.md)

## 14. REST API Specification

[Endpoint contract](../architecture/API_CONTRACT.md)

## 15. Database Design

[Keys, constraints and ERD](../architecture/DATABASE_DESIGN.md)

## 16. MLOps Architecture

For Phases 3–5, train and score using reproducible local commands. The scoring CLI loads a pinned local artifact and verifies its SHA-256 digest and feature schema version before scoring. PostgreSQL records the model ID, artifact digest, schema version, snapshot lineage and scoring run metadata. The local publisher commits verified ranks and their published pointer atomically.

Phase 6 adds MLflow experiment tracking and registry operations, plus Prefect orchestration with bounded retries. Register the same verified bundle format and pin the resolved version per run. Promote after development evidence beats the rule on macro P@50, client regressions are reviewed and the frozen candidate passes final evaluation. Keep the rule as a fallback if the learned candidate fails and require a fresh holdout for subsequent selection. The Product MVP requires a validated learned model. [Phase 6](../phases/PHASE_06_MLOPS.md)

## 17. Monitoring and Observability

Record run ID, duration, row counts, missingness, client coverage, stale cutoff and last successful publication. Alert on failed validation or missed scheduled batch. Compute quality only when matched labels exist.

## 18. Security Requirements

Loopback-only single-user MVP. Isolate database roles and keep secrets in runtime configuration. Validate request scope, bounds and transitions. Exclude notes and row data from logs.

## 19. Testing Strategy

[Verification strategy](../governance/TESTING_STRATEGY.md)

## 20. Local Deployment Requirements

For Phase 4–5 integration, start local PostgreSQL, apply Flyway migrations, then start Spring Boot and React. Use synthetic fixtures for clean-room development tests and authorized local inputs for Product MVP verification. Phase 7 packages the full local stack in Compose and verifies recovery to a fresh volume. [Local bootstrap](../LOCAL_BOOTSTRAP.md)

## 21. Public Demo Requirements

Static site labels simulated content, resets local actions on reload and needs no backend credentials. Audit generated bundle before release.

## 22. System Architecture

[Component ownership](../architecture/SYSTEM_OVERVIEW.md), [context](../architecture/SYSTEM_CONTEXT.md), [containers](../architecture/CONTAINER_ARCHITECTURE.md) and [flow](../architecture/DATA_FLOW.md).

## 23. Architecture Decision Records

ADRs 001–005 document backend, inference, persistence, orchestration and demonstration boundaries in docs/adr.

## 24. Assumptions, Risks, and Open Questions

[Risk register](../governance/RISK_REGISTER.md) assigns owners and release decisions.

## 25. Implementation Roadmap

[Mandatory phases and iteration gates](../roadmap/IMPLEMENTATION_ROADMAP.md)

## 26. Acceptance Criteria

Pass the acceptance check for each Must requirement and the applicable phase gates. The Phase 5 Product MVP must produce a live queue through authorized local data → feature engineering → trained model artifact → actual batch scoring → PostgreSQL → Spring Boot REST API → React dashboard → persistent analyst review. Retain evidence that ties the displayed ranking and saved review to that scoring run. Synthetic fixtures support development, unit tests and the public demo. [Product MVP acceptance test](../phases/PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test)

## 27. Definition of Done

A second developer reproduces the Product MVP journey on authorized local data and traces a displayed rank to its model artifact. Run CI-equivalent tests on synthetic fixtures and verify history after a restore during Phase 7. Report historical, synthetic and validated results with their protocols and limitations.

## 28. Future Cloud Expansion

[Phase 9 — AWS Cloud Deployment (Deferred)](../phases/PHASE_09_AWS_FUTURE.md)
