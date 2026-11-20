# Reference architecture audit

Sibling checkout `../paul-reference`, revision `65ae242adf4c00c80a5c151444fc412d205826af`. Reviewed source and deployment configuration statically. [Upstream repository](https://github.com/paultongyoo/churn-model-evaluation-platform)

|Reference pattern|Decision for this platform|Integration cost or risk|
|---|---|---|
|Prefect orchestrates Python tasks in a container|Wrap tested batch functions with task retries only after the manual pipeline works|Retries need a durable run key|
|Optuna search and MLflow experiment/model artifacts|Search grouped development folds, register a complete preprocessing and ranker bundle|Classification metrics and thresholds do not measure editorial queue quality|
|Evidently reports and Grafana dashboards|Start with run counts, null rates, coverage and run age. Add dashboards when operators need historical comparisons|Small client groups make distribution alerts noisy|
|Docker and Terraform-backed AWS services|Use local Compose volumes and one-shot jobs. Defer ECR, remote compute and managed databases|Cloud IAM, networking and idle costs complicate reproduction|
|GitHub Actions deploy-prefect.yml builds on orchestration changes|Use CI tests on synthetic fixtures. Keep release credentials outside PR jobs|Reference workflow embeds an HTTP Prefect endpoint and uses AWS key secrets. Future deployments need private transport and short-lived identity|

The transferable boundary is the versioned artifact between training and scoring. Spring owns analyst operations. A churn classifier or a hosted prediction endpoint would add another serving contract without improving a daily review queue.
