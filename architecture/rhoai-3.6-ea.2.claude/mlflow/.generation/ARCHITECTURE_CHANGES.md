# Architecture Changes: mlflow

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Row key migrated: generic "HTTP API" replaced with specific "Tracking Server API" to reflect actual deployment surface | Dockerfile.konflux:80, mlflow/server/__init__.py:219 |
| add | authentication | Tracking Server API :: All | * | <empty> | <empty> | Dockerfile CMD configures --app-name kubernetes-auth loading mlflow-kubernetes-plugins auth plugin with Kubernetes SA bearer token authentication and workspace isolation | Dockerfile.konflux:80, requirements/konflux-pypi.in:13, mlflow/tracking/request_auth/kubernetes_request_auth_provider.py:39-42, mlflow/server/__init__.py:219 |
| update | internal_dependencies | Kubernetes API | Interaction Type | Python client library | Python client library (BatchV1Api) | Source inspection shows specific BatchV1Api usage for Job creation via create_namespaced_job() | mlflow/projects/kubernetes.py:86-87 |
| update | internal_dependencies | Kubernetes API | Purpose | Kubernetes resource operations via Python SDK | Creates and monitors Kubernetes Jobs for MLflow project execution | kubernetes.py creates Jobs via BatchV1Api.create_namespaced_job() and monitors via read_namespaced_job_status() | mlflow/projects/kubernetes.py:86-88, mlflow/projects/kubernetes.py:125-127 |
