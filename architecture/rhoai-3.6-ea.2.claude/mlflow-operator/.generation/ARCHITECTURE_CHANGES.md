# Architecture Changes: mlflow-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | internal_dependencies | Auth (services.platform.opendatahub.io) | * | <empty> | <empty> | NamespaceRBACReconciler watches the platform Auth CR (services.platform.opendatahub.io/v1alpha1) to trigger namespace RBAC propagation for workspace-labeled namespaces | internal/controller/namespace_rbac_controller.go:48-52, internal/controller/namespace_rbac_controller.go:84-85, internal/controller/namespace_rbac_controller.go:104-106 |
| add | integration_points | services.platform.opendatahub.io/v1alpha1/Auth :: Controller watch (Watches) | * | <empty> | <empty> | NamespaceRBACReconciler registers a Watches source for the Auth CR using an unstructured object with authGVK, triggering reconciliation of namespace RoleBindings when Auth changes | internal/controller/namespace_rbac_controller.go:48-52, internal/controller/namespace_rbac_controller.go:84-85, internal/controller/namespace_rbac_controller.go:104-106 |
