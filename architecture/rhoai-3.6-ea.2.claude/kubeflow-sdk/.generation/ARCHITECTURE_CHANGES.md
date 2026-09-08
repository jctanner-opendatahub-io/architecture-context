# Architecture Changes: kubeflow-sdk

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Analyzer extracted authentication surface from test file (transformers_test.py), not a production API; SDK is a client library with no HTTP server | kubeflow/trainer/backends/kubernetes/backend.py:53-56 |
| add | authentication | Kubernetes API :: All | * | <empty> | <empty> | SDK authenticates to Kubernetes API via kubernetes Python client using kube-config or in-cluster SA tokens; this is the actual authentication boundary | kubeflow/trainer/backends/kubernetes/backend.py:53-56 |
| add | internal_dependencies | Kubeflow Trainer API | * | <empty> | <empty> | Direct core dependency providing TrainJob API models imported in Kubernetes backend | kubeflow/trainer/backends/kubernetes/backend.py:27, pyproject.toml:32 |
| add | internal_dependencies | Kubeflow Katib API | * | <empty> | <empty> | Direct core dependency providing hyperparameter tuning API models | pyproject.toml:33 |
