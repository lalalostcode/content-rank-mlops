# Testing strategy

Pytest validates contracts, feature lineage, split disjointness, query lengths, metric math and deterministic bundle reloads. Use hand-ranked clients of sizes 0, 1, K−1 and K+1, ties and all-negative labels. Keep restricted data outside CI. Compare batch reruns by ordered IDs and hashes.

JUnit/Mockito cover decision and transition logic. Run Flyway on disposable PostgreSQL for composite foreign keys, paging, rollback, request replay and two simultaneous updates. Browser tests run the same analyst journey against local API and static adapter. Inject a failed scoring insert and verify the old queue remains visible. Restore to a fresh database and compare published version and action history. Record tool versions, revision and fixture seed with each release.
