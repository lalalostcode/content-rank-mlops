# Logical containers

```mermaid
flowchart LR
 React -->|JSON REST| Spring --> Postgres
 Operator -->|local CLI| Python -->|publish transaction| Postgres
 Python <--> DuckDB
 Prefect[Prefect · Phase 6] --> Python
 Python <--> Registry[MLflow Registry · Phase 6]
```
