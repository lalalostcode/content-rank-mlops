# PRD review changelog

|Area|Correction|
|---|---|
|Product MVP|Phase 5 requires a verified run from authorized local data through actual batch scoring, PostgreSQL, Spring REST and React, with a review event that survives an API restart.|
|Dependencies|Phase 3 exports a verified local model bundle. Phase 4 adds database publication and REST provenance. Phase 6 adds MLflow Registry and Prefect around the established scorer and publisher.|
|Evaluation|Historical 92.4% is mean pooled P@50 across held-out folds. The new protocol computes P@10, P@25 and P@50 per client and uses within-client percentile blending, with fresh validation required.|
|Review and follow-up|State belongs to a review case. A newer qualifying observation can start a new case after resolution. Audit events persist and the UI shows unavailable follow-up until comparable observations exist.|
|Developer setup and decisions|Repaired README encoding, documented Windows bootstrap and expanded the five ADRs. The roadmap retains phases 0–8.|

## Unresolved blockers

- **Authorized inputs.** Project authorization for a local snapshot and its provenance still need confirmation. The gated warehouse is optional. A single authorized snapshot supports MVP acceptance with the unavailable follow-up path. [Data governance](governance/DATA_GOVERNANCE.md)
- **Learned artifact and evidence.** Fresh client-level evaluation, a verified trained bundle and the real-data acceptance run are pending. The scoring CLI, database/API and dashboard are planned implementation deliverables. [Phase 3](phases/PHASE_03_MACHINE_LEARNING.md) · [Phase 5 test](phases/PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test)
- **Local runtime.** Docker Engine was unavailable in the audit, the Windows Store Python alias failed and the Maven wrapper is a Phase 4 deliverable. A managed Python executable was found. Container startup, the wrapper build and integration tests still require verification. [Local bootstrap](LOCAL_BOOTSTRAP.md)
