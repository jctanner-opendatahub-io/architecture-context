# Architecture Changes: llm-d-batch-gateway-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | services | llm-d-batch-gateway-operator-metrics | * | <empty> | <empty> | MetricsController dynamically creates a ClusterIP Service on port 8443 with OpenShift serving-cert annotation for metrics collection | internal/monitoring/controller.go:120-148, config/manager/manager.yaml:44 |
| add | authentication | :8443/metrics :: GET | * | <empty> | <empty> | Metrics endpoint uses controller-runtime SecureServing with WithAuthenticationAndAuthorization filter enforcing TokenReview and SubjectAccessReview | cmd/main.go:133-139 |
| update | internal_dependencies | cert-manager | Role | unknown | runtime-security | RBAC rules confirm cert-manager.io/certificates CRUD for TLS certificate lifecycle in Helm-rendered workloads | config/rbac/role.yaml:2, cmd/main.go:157 |
| update | internal_dependencies | Gateway API | Role | unknown | runtime-transport | RBAC confirms gateway.networking.k8s.io/httproutes and referencegrants CRUD; operator creates HTTPRoutes for batch gateway routing | config/rbac/role.yaml:2, internal/controller/llmbatchgateway_controller.go:568 |
| update | internal_dependencies | prometheus-operator | Role | unknown | runtime-observability | MetricsController creates ServiceMonitor, PrometheusRule, and PodMonitor resources; CRD watches are conditional | internal/monitoring/controller.go:108-115, config/rbac/role.yaml:2 |
