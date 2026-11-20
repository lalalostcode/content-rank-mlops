# System context

```mermaid
flowchart LR
 Analyst -->|select client and review| Platform
 Operator -->|approve model and inspect jobs| Platform
 Source[Approved snapshot] --> Platform
 Recruiter --> Demo[Synthetic static demonstration]
```
