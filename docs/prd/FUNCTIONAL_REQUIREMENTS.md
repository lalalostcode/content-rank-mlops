# Functional requirements

|ID|Capability|Priority|Actor|Inputs|Behavior|Outputs|Dependency|Acceptance|Test|
|---|---|---|---|---|---|---|---|---|---|
|FR-01|Select client|Must|Analyst|session|List allowed clients|client IDs and labels|membership|Other tenants absent|authorization integration|
|FR-02|Inspect overview|Must|Analyst|client, cutoff|Aggregate dated inventory and counts|totals, window, coverage|observations|Empty client shows zero count and unavailable rates|SQL fixture|
|FR-03|Page queue|Must|Analyst|client, run, status, cursor|Filter frozen run and sort by position|items and opaque cursor|published pointer|Page traversal has unique items across new publication|integration race|
|FR-04|Inspect evidence|Must|Analyst|run and item|Join same-window measurements to reason codes|metric, unit, value, window|snapshot lineage|Every reason traces to an observation|contract fixture|
|FR-05|Record decision|Must|Analyst|act/defer/no_action, note, request key|Append immutable decision once|action ID and status|transaction|Matching retry returns original result|duplicate submission|
|FR-06|Update status|Must|Analyst|expected version, target|Apply open → in_review → closed or reopen closed → open|new version and history event|row version|Stale update returns 409|concurrent writers|
|FR-07|Read history|Must|Analyst|client and item|Return ordered audit events|actor, time, change|events|Events survive rescoring|integration replay|
|FR-08|Compare follow-up|Must|Analyst|item and two snapshots|Show dated observed deltas|paired measures or unavailable|aligned observations|One snapshot displays insufficient history|UI fixture|
|FR-09|Publish batch|Must|Operator|approved manifest and model|Validate, score and atomically publish|run metadata and queue|registry and database|Failed run preserves prior queue|fault injection|
|FR-10|Inspect provenance|Must|Analyst|run ID|Resolve model version and input cutoff|version and freshness|run manifest|Metadata agrees with displayed queue|API contract|
|FR-11|Explore demo|Must|Visitor|synthetic fixture|Simulate selection and review in browser memory|labeled demo views|static adapter|Reload resets edits and no API calls occur|browser network test|
