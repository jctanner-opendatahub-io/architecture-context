# Architecture Changes: ai-gateway-controller

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Source confirms healthz.Ping handler on plain HTTP with no TLS configuration | cmd/manager/main.go:101, config/self/manager/manager.yaml:69 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | healthz.Ping handler requires no authentication; unauthenticated by design | cmd/manager/main.go:101, config/self/manager/manager.yaml:67 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Source confirms readyz handler on plain HTTP with no TLS configuration | cmd/manager/main.go:105, config/self/manager/manager.yaml:74 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | readyz handler requires no authentication; unauthenticated by design | cmd/manager/main.go:105, config/self/manager/manager.yaml:73 |
| update | http_endpoints | GET :: /healthz | Owner | | cmd/manager | Health check registered in cmd/manager/main.go via mgr.AddHealthzCheck | cmd/manager/main.go:101 |
| update | http_endpoints | GET :: /readyz | Owner | | cmd/manager | Readiness check registered in cmd/manager/main.go via mgr.AddReadyzCheck | cmd/manager/main.go:105 |
| add | integration_points | Istio Service Mesh :: CRD CRUD | * | <empty> | <empty> | Controller manages Istio networking CRDs (EnvoyFilter, DestinationRule, ServiceEntry) via SSA for praxis-extproc traffic routing | config/manifests/praxis-extproc/overlays/odh/pre-processing/kustomization.yaml:24, cmd/manager/main.go:63 |
