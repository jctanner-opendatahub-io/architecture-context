# Architecture Changes: workload-variant-autoscaler

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Health probe on plain HTTP port 8081, no TLS configured | cmd/main.go:664 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | healthz.Ping handler registered without authentication | cmd/main.go:664 |
| update | http_endpoints | GET :: /healthz | Owner |  | cmd | Source confirms handler registered in cmd/main.go | cmd/main.go:664 |
| update | http_endpoints | GET :: /healthz | Transport |  | HTTP/1.1 | Health probe served on plain HTTP/1.1 | cmd/main.go:664 |
| update | http_endpoints | GET :: /healthz | Purpose | httpGet probe | Health probe (healthz.Ping) | Clarified probe implementation | cmd/main.go:664 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Readiness probe on plain HTTP port 8081, no TLS configured | cmd/main.go:668 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Custom readiness handler registered without authentication | cmd/main.go:668-676 |
| update | http_endpoints | GET :: /readyz | Owner |  | cmd | Source confirms handler registered in cmd/main.go | cmd/main.go:668 |
| update | http_endpoints | GET :: /readyz | Transport |  | HTTP/1.1 | Readiness probe served on plain HTTP/1.1 | cmd/main.go:668 |
| update | http_endpoints | GET :: /readyz | Purpose | httpGet probe | Readiness probe (ConfigMap bootstrap gate) | Readiness depends on ConfigMap bootstrap completion | cmd/main.go:668-676 |
| update | internal_dependencies | prometheus-operator | Role | unknown | runtime-observability | Manages ServiceMonitor CRDs for metrics collection pipeline | config/base/rbac/manager-clusterrole.yaml:2 |
| update | internal_dependencies | prometheus-operator | Purpose | Manage Prometheus monitoring resources | Manage ServiceMonitor CRDs for metrics collection pipeline | Clarified specific CRD type managed | config/base/rbac/manager-clusterrole.yaml:2 |
| update | internal_dependencies | Kubernetes API (nodes) | Role | unknown | runtime-integration | Runtime node discovery for GPU capacity and allocatable resource inventory | internal/discovery/k8s_with_gpu_operator.go:83 |
| update | internal_dependencies | Kubernetes API (nodes) | Purpose | nodes resource access via RBAC | Runtime node discovery for GPU capacity and allocatable resource inventory | Source confirms GPU operator uses node listing for resource discovery | internal/discovery/k8s_with_gpu_operator.go:83 |
| update | internal_dependencies | Prometheus | Role | unknown | runtime-integration | Required Prometheus HTTP API client with TLS 1.2+ and bearer token auth | internal/prometheus/prometheus_transport.go:38-73, internal/prometheus/tls.go:48-51 |
| update | internal_dependencies | Prometheus | Purpose | Required Prometheus API client used for runtime metrics queries | Required Prometheus HTTP API client for workload saturation metrics queries; supports TLS 1.2+ and bearer token authentication | Source confirms TLS configuration and auth mechanism | internal/prometheus/tls.go:32-88, internal/prometheus/prometheus_transport.go:38-73 |
| update | services | controller-manager-metrics-service | Protocol | TCP | HTTPS | Metrics endpoint uses HTTPS with self-signed TLS | cmd/main.go:261-265 |
| update | services | controller-manager-metrics-service | Encryption | Unknown | TLS (self-signed) | controller-runtime generates self-signed TLS certificates for metrics server | cmd/main.go:275-280 |
| update | services | controller-manager-metrics-service | Auth | Unknown | TokenReview + SubjectAccessReview | controller-runtime authn/authz filter protects metrics endpoint | cmd/main.go:267-272 |
| add | egress | Prometheus | * | <empty> | <empty> | Required Prometheus API client connects to configurable HTTP/HTTPS endpoint for metrics queries | internal/prometheus/prometheus_transport.go:38-42, internal/prometheus/tls.go:48-51 |
