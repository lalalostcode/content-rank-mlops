# Quality budgets

Provisional until measured on a documented laptop with 30k synthetic items and 32 clients. Record CPU, memory, seed, dataset size and cold/warm state.

|Quality|Target and evidence|
|---|---|
|Read latency|p95 under 500 ms across 200 warmed queue requests with 5 concurrent users and pages of 50|
|Batch runtime|Under 10 minutes for one local scoring pass. Log stage duration and peak memory|
|Integrity|Zero partially visible runs across 20 injected failures. Zero lost updates in two-writer test|
|Reproduction|Same locked dependencies, seed and inputs produce identical ordered IDs across two runs|
|Accessibility|Keyboard-only completion of client selection, item inspection and review. Label controls and focus errors|
|Isolation|All cross-client read and write contract tests denied. Built demo makes zero requests for private data|
