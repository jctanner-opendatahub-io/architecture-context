# Architecture Changes: kubeflow

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Mutating webhook :: CREATE, UPDATE | * | <empty> | <empty> | Mutating webhook uses Kubernetes admission with MutatingWebhookConfiguration; injects kube-rbac-proxy sidecar, proxy env vars, and Elyra pipeline secrets | components/odh-notebook-controller/controllers/notebook_mutating_webhook.go:54, components/odh-notebook-controller/main.go:150-151 |
| add | internal_dependencies | DataSciencePipelinesApplication :: CRD read | * | <empty> | <empty> | Controller reads DataSciencePipelinesApplication CRs via typed client to generate Elyra pipeline runtime secrets for notebook workbenches | components/odh-notebook-controller/controllers/notebook_dspa_secret.go:49-51, components/odh-notebook-controller/config/rbac/role.yaml:2 |
| add | integration_points | datasciencepipelinesapplications.opendatahub.io/v1/DataSciencePipelinesApplication :: Resource read | * | <empty> | <empty> | Controller performs get, list, watch on DataSciencePipelinesApplication CRs for Elyra pipeline configuration | components/odh-notebook-controller/controllers/notebook_dspa_secret.go:49-51, components/odh-notebook-controller/config/rbac/role.yaml:2 |
