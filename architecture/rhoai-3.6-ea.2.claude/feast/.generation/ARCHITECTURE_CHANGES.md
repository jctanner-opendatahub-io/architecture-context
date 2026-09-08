# Architecture Changes: feast

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | internal_dependencies | Kubeflow Notebooks (kubeflow.org) | Interaction Type | CRD CRUD | CRD Watch | RBAC grants only get, list, watch on kubeflow.org/notebooks; operator does not create or modify Notebook CRs | infra/feast-operator/config/rbac/role.yaml:27 |
| update | internal_dependencies | Kubeflow Notebooks (kubeflow.org) | Role | unknown | runtime-integration | Operator watches Notebook CRs to inject FeatureStore connection ConfigMaps into notebook namespaces via NotebookConfigMapReconciler | infra/feast-operator/internal/controller/notebook_configmap_controller.go:154 |
| update | internal_dependencies | Kubeflow Notebooks (kubeflow.org) | Purpose | Create and manage notebook workbenches | Watch notebook instances for ConfigMap injection | Operator reads notebook resources to inject FeatureStore connection ConfigMaps, not to create or manage the notebooks themselves | infra/feast-operator/internal/controller/notebook_configmap_controller.go:154 |
| update | internal_dependencies | prometheus-operator | Role | unknown | runtime-observability | Operator creates and manages ServiceMonitor resources for Prometheus metrics scraping of deployed Feast services | infra/feast-operator/config/rbac/role.yaml:29 |
| update | internal_dependencies | prometheus-operator | Purpose | Manage Prometheus monitoring resources | Manage ServiceMonitor resources for Feast service metrics | ServiceMonitors are the specific prometheus-operator resource type managed by the Feast operator for observability | infra/feast-operator/config/rbac/role.yaml:29 |
