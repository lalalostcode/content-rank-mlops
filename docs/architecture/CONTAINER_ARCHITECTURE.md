# Logical containers

```mermaid
flowchart LR
 React -->|JSON REST| Spring --> Postgres
 Prefect --> Python -->|publish transaction| Postgres
 Python <--> DuckDB
 Python <--> MLflow
```
