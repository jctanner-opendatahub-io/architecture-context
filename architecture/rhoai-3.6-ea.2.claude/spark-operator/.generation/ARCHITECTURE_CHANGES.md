# Architecture Changes: spark-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | Health probes are unauthenticated by design per Kubernetes probe pattern; consistent with authentication table evidence | cmd/operator/controller/start.go:422 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Readiness probes are unauthenticated by design per Kubernetes probe pattern; consistent with authentication table evidence | cmd/operator/controller/start.go:427 |
| update | integration_points | cert-manager :: Certificate CR | Role | unknown | tls-provider | Module controller manages cert-manager Certificate and Issuer CRDs to provision webhook TLS certificates | spark-operator-module/config/rbac/role.yaml:2, spark-operator-module/go.mod:8 |
| update | integration_points | prometheus-operator :: CRD CRUD | Role | unknown | monitoring-provider | Module controller manages PodMonitor CRDs for Prometheus metrics collection | spark-operator-module/config/rbac/role.yaml:2, spark-operator-module/go.mod:8 |
| update | internal_dependencies | cert-manager | Role | unknown | tls-provider | Module controller manages cert-manager CRDs to provision webhook TLS certificates; RBAC grants cert-manager.io certificates and issuers full CRUD | spark-operator-module/config/rbac/role.yaml:2 |
| update | internal_dependencies | prometheus-operator | Role | unknown | monitoring-provider | Module controller manages PodMonitor CRDs for Prometheus metrics collection; RBAC grants monitoring.coreos.com podmonitors full CRUD | spark-operator-module/config/rbac/role.yaml:2 |
