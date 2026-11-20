# Risks and open decisions

|Risk or question|Owner|Resolution gate|
|---|---|---|
|Permission to use starter for new purpose|Data steward|Confirm scope and retention before private ingestion. Synthetic fixtures unblock contract work|
|Authorized data and verified learned bundle for Phase 5|Data steward and ML owner|Record authorized snapshot provenance and approve a freshly evaluated learned model before the Product MVP test|
|Proxy reconstructed from overlapping periods|ML owner|Review feature availability and reconstruction probes before fitting|
|Few clients or too few positives|ML owner|Freeze holdout size and minimum acceptable per-client regressions before tuning. Report uncertainty and coverage|
|Freshness expected by editors unknown|Product owner|Validate batch cadence and provisional latency targets with analyst before operations sign-off|
|No comparable post-action observation|Data steward|Show follow-up unavailable. Enable comparisons only when the source and comparable windows can be verified|
|Tenant identity and roles for shared hosting|Backend owner|Local single-user scope only until authenticated role and membership tests pass|
|Unintended release of derived records|Release owner|Inspect fixtures, Git history, built JS, screenshots and logs before publication|
|Review budget K varies by client|Analyst|Confirm primary K=50 and review secondary K=10,25 before locking evaluation|
