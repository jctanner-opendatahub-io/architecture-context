# Architecture Changes: rhods-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Metrics (port 8443) :: HTTPS | * | <empty> | <empty> | Metrics endpoint uses controller-runtime authentication and authorization filter when MetricsSecure is enabled; conditional RBAC enforcement on the metrics serving surface | cmd/main.go:491-493 |
| add | internal_dependencies | kuadrant | * | <empty> | <empty> | Auth controller watches kuadrant-system namespace lifecycle events to reconcile RBAC permissions; establishes runtime integration dependency on Kuadrant API gateway policy engine | internal/controller/services/auth/auth_controller.go:75 |
