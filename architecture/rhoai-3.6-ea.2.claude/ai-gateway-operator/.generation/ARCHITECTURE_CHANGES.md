# Architecture Changes: ai-gateway-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Controller-runtime metrics server exposes Prometheus metrics on the configured metrics bind address, served via ai-gateway-metrics-service on port 8443 | cmd/operator/operator.go:86-88, pkg/config/config.go:44, config/default/metrics_service.yaml:1 |
| add | authentication | Metrics endpoint :: GET | * | <empty> | <empty> | Metrics endpoint uses TokenReview/SubjectAccessReview authentication via dedicated RBAC roles ai-gateway-metrics-auth-role and ai-gateway-metrics-reader | config/rbac/metrics_auth_role.yaml:1, config/rbac/metrics_reader_role.yaml:1, cmd/operator/operator.go:86-88 |
| add | integration_points | Kuadrant :: CRD CRUD | * | <empty> | <empty> | Operator manages Kuadrant AuthPolicies, RateLimitPolicies, and TokenRateLimitPolicies for API policy enforcement; RBAC grants full CRUD on kuadrant.io resources | config/rbac/role.yaml:2 |
| add | integration_points | Authorino :: CRD Watch | * | <empty> | <empty> | Operator reads Authorino CRs (operator.authorino.kuadrant.io/authorinos) to verify authentication infrastructure availability; RBAC grants get, list, watch | config/rbac/role.yaml:2 |
