# Architecture Changes: model-registry-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | internal_dependencies | ODH Platform Auth (services.platform.opendatahub.io) | * | <empty> | <empty> | Operator watches services.platform.opendatahub.io/Auth resources for platform authentication configuration; RBAC marker confirms get/list/watch permissions | internal/controller/kubebuilder.go:23 |
| add | internal_dependencies | ODH Component Manager (components.platform.opendatahub.io) | * | <empty> | <empty> | Operator watches components.platform.opendatahub.io/ModelRegistries for component lifecycle coordination with the ODH operator | internal/controller/kubebuilder.go:22 |
