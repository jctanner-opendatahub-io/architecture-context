# Architecture Changes: eval-hub

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | MLflow Tracking Server :: HTTP client | * | <empty> | <empty> | MLflow Tracking Server is a runtime integration for experiment tracking with configurable TLS and token auth | internal/eval_hub/config/mlflow_config.go:7-15 |
| add | integration_points | PostgreSQL / SQLite :: SQL client | * | <empty> | <empty> | Pluggable SQL storage backend is a core runtime integration for evaluation data persistence | internal/eval_hub/storage/sql/sql.go:33-37 |
