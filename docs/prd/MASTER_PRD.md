# Content Ranking MLOps · Master PRD

Planning baseline for review, 20 November 2026.

## 1. Executive Summary

Prioritize a limited number of editorial investigations per client using reproducible batch scores and inspectable evidence.

## 2. Project Background

The internship capstone compared a rule with a fixed blend on client-grouped folds. Historical mean fold P@50 was 92.4% versus 46.4%. The new platform has no measured ranking result. [Historical report](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/work/capstone_report.md)

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

Use authorized snapshots with cutoff, checksum and schema revision. [Governance](../governance/DATA_GOVERNANCE.md)

## 11. Machine Learning Requirements

Binary relevance is observed trend_direction=down. Exclude identifiers, trend fields, product decisions and overlapping window features that reconstruct the label. Audit missingness by content type. Freeze seeded final client holdout before development. Within remaining clients use five GroupKFold folds, fit preprocessing only on training clients and order contiguous query groups by client. Compare a fixed documented editorial rule, base and engineered LightGBM LambdaRank, and fixed equal average of within-client percentile ranks. Fix tie-break on content ID. Tune on development folds only. Freeze candidate before one final evaluation. For each nonempty client divide hits by min(K,n) at K=10,25,50. Average client metrics equally. Report undersized and empty counts. Binary NDCG uses the same cutoff, zero for no relevant items with count reported. Report client-level misses and rule deltas. Ranking scores are ordinal. A future authorized temporal backtest must split by cutoff and isolate outcome windows.

## 12. Frontend Requirements

React/Vite supports keyboard navigation, client-scoped filters, loading, stale data, empty and error states. Adapter interface is shared by API and static fixtures.

## 13. Backend Requirements

Spring Boot owns authorization, review lifecycle and query DTOs. Separate controllers, services and JPA repositories. Flyway migrations run before readiness.

## 14. REST API Specification

[Endpoint contract](../architecture/API_CONTRACT.md)

## 15. Database Design

[Keys, constraints and ERD](../architecture/DATABASE_DESIGN.md)

## 16. MLOps Architecture

Log dataset and code digests, feature revision, split IDs, seeds, metrics and bundle in MLflow. Pin immutable registry version per run. Prefect retries transient IO with bounded backoff. Promote only after development evidence beats rule on macro P@50, client regressions are reviewed and untouched evaluation recorded. A failed final check retains the rule and requires a fresh holdout for subsequent selection.

## 17. Monitoring and Observability

Record run ID, duration, row counts, missingness, client coverage, stale cutoff and last successful publication. Alert on failed validation or missed scheduled batch. Compute quality only when matched labels exist.

## 18. Security Requirements

Loopback-only single-user MVP. Isolate database roles and keep secrets in runtime configuration. Validate request scope, bounds and transitions. Exclude notes and row data from logs.

## 19. Testing Strategy

[Verification strategy](../governance/TESTING_STRATEGY.md)

## 20. Local Deployment Requirements

Compose creates private service network and persistent stores. Start database, migrate, start API, then dashboard. Seed synthetic fixtures for clean-room testing. Restore a backup into a fresh volume and compare history and published pointer.

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

Pass the acceptance check for each Must requirement and each phase gate. Retain reports with environment and commit.

## 27. Definition of Done

A second developer reproduces the local journey on synthetic inputs, runs CI-equivalent tests, restores history, and traces a rank to its artifact. Publish limitations and separate historical, synthetic and validated results.

## 28. Future Cloud Expansion

[Phase 9 — AWS Cloud Deployment (Deferred)](../phases/PHASE_09_AWS_FUTURE.md)
