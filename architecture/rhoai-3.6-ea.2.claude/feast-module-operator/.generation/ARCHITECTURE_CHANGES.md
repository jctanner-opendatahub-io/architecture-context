# Architecture Changes: feast-module-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Metrics (:8443) :: GET | * | <empty> | <empty> | Metrics endpoint uses TokenReview + SubjectAccessReview authentication via controller-runtime metrics server, enforced by metrics-auth-role RBAC | config/rbac/metrics_auth_role.yaml:1-18, pkg/manager/manager.go:92-93, config/default/metrics_service.yaml:10-11 |
| add | authentication | Health probes (:8081) :: GET | * | <empty> | <empty> | Health and readiness probes are unauthenticated Kubernetes probe endpoints | pkg/manager/manager.go:143-148, pkg/config/config.go:52 |
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Prometheus metrics endpoint served on port 8443 with TLS and TokenReview+SubjectAccessReview authentication | pkg/manager/manager.go:92-93, config/default/metrics_service.yaml:10-11, config/rbac/metrics_auth_role.yaml:1 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | Health probe uses healthz.Ping with no authentication | pkg/manager/manager.go:143-144 |
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Health probe is plain HTTP on port 8081 | pkg/config/config.go:52 |
| update | http_endpoints | GET :: /healthz | Owner | | controller-runtime | Health check registered via controller-runtime AddHealthzCheck | pkg/manager/manager.go:143 |
| update | http_endpoints | GET :: /healthz | Purpose | httpGet probe | Liveness probe (healthz.Ping) | Clarified as liveness probe using healthz.Ping handler | pkg/manager/manager.go:143 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Readiness probe uses healthz.Ping with no authentication | pkg/manager/manager.go:145-146 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Readiness probe is plain HTTP on port 8081 | pkg/config/config.go:52 |
| update | http_endpoints | GET :: /readyz | Owner | | controller-runtime | Readiness check registered via controller-runtime AddReadyzCheck | pkg/manager/manager.go:145 |
| update | http_endpoints | GET :: /readyz | Purpose | httpGet probe | Readiness probe (healthz.Ping) | Clarified as readiness probe using healthz.Ping handler | pkg/manager/manager.go:145 |
| update | services | opendatahub-feast-metrics-service | Encryption | Unknown | TLS | Metrics service port named 'https' targeting port 8443 with RBAC-protected endpoint | config/default/metrics_service.yaml:11, config/rbac/metrics_auth_role.yaml:1 |
| update | services | opendatahub-feast-metrics-service | Auth | Unknown | TokenReview + SubjectAccessReview | Metrics endpoint protected by controller-runtime authn/authz using TokenReview and SubjectAccessReview | config/rbac/metrics_auth_role.yaml:1-18, pkg/manager/manager.go:92-93 |
