# Batch and review flow

```mermaid
flowchart TD
 Snapshot --> Validate --> Features --> Score --> Staging --> Checks -->|atomic pointer update| Queue
 Queue --> Review --> History
 Later[Later dated snapshot] --> Comparison
 History --> Comparison
```

A failed validation or staging check records a failed run. Readers retain the previous published run. Historical comparisons require distinct dated observations of the same item.
