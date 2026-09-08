# Architecture Changes: trainer

Changes identified during partial-route gap resolution for authentication, integration_points, internal_dependencies, fips_compliance, and grpc_services.

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | internal_dependencies | OpenShift TLS Profile | * | <empty> | <empty> | Operator reads OpenShift config.openshift.io/v1 APIServer resource at startup to resolve cluster TLSSecurityProfile for webhook and metrics server TLS configuration | pkg/tls/tls.go:69-73, pkg/tls/tls.go:93-104, cmd/trainer-controller-manager/main.go:119-124 |
| update | integration_points | /v1/Pod :: Resource read | Purpose | list operations | List training workload pods to track TrainJob progression status | Progression tracker lists pods by namespace and label selectors to find primary/launcher pod for status reporting | pkg/rhai/progression/progression.go:147-168 |
| update | integration_points | config.openshift.io/v1/apiservers :: Resource read | Purpose | get operations | Read OpenShift TLSSecurityProfile for webhook and metrics server TLS configuration | TLS profile resolution reads APIServer resource to configure cipher suites and minimum TLS version | pkg/tls/tls.go:69-73, pkg/tls/tls.go:93-104 |
| update | integration_points | networking.k8s.io/v1/NetworkPolicy :: Resource CRUD | Purpose | get, update operations | Reconcile per-TrainJob NetworkPolicies for training workload network isolation | NetworkPolicy reconciler creates and updates ingress policies scoped by JobSet labels per TrainJob | pkg/rhai/networkpolicy.go:152-180 |
