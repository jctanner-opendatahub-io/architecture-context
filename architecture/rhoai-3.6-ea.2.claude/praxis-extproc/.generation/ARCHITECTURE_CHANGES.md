# Architecture Changes: praxis-extproc

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Prometheus metrics HTTP endpoint served by hyper on port 9090 | src/metrics.rs:60-72, deploy/base/instance/deployment.yaml:40-42 |
| add | grpc_services | envoy.service.ext_proc.v3.ExternalProcessor | * | <empty> | <empty> | Primary gRPC service implementing Envoy ExtProc protocol on port 9004 | src/bin/praxis_extproc.rs:18, src/server.rs:106, deploy/base/instance/deployment.yaml:34-36 |
| add | grpc_services | grpc.health.v1.Health | * | <empty> | <empty> | tonic-health gRPC health check service on port 50052 for Kubernetes probes | src/health.rs:25-43, deploy/base/instance/deployment.yaml:37-39 |
| add | integration_points | Envoy Gateway (maas-default-gateway) :: gRPC ext_proc | * | <empty> | <empty> | ExtProc receives processing streams from the MaaS Envoy gateway via EnvoyFilter | deploy/overlays/odh/envoy-filter.yaml:19-75, deploy/overlays/odh/after/destination-rule.yaml:1-13 |
| add | integration_points | Kuadrant WasmPlugin :: EnvoyFilter ordering | * | <empty> | <empty> | ExtProc filters positioned before/after Kuadrant auth in the gateway filter chain | deploy/overlays/odh/envoy-filter.yaml:6-11 |
| add | integration_points | Kubernetes API server :: REST | * | <empty> | <empty> | Reads ConfigMaps, Secrets, ExternalProviders, ExternalModels via ClusterRole | deploy/overlays/odh/rbac/clusterrole.yaml:6-15, deploy/overlays/odh/networking/networkpolicy.yaml:59-65 |
| add | integration_points | Prometheus :: HTTP scrape | * | <empty> | <empty> | Exposes /metrics endpoint for Prometheus monitoring scrape | src/metrics.rs:60-72, deploy/overlays/odh/networking/networkpolicy.yaml:37-48 |
| add | internal_dependencies | Istio/Envoy Gateway (maas-default-gateway) | * | <empty> | <empty> | Receives ext_proc gRPC streams from the MaaS gateway Envoy proxy | deploy/overlays/odh/envoy-filter.yaml:12-14, deploy/overlays/odh/after/destination-rule.yaml:6-13 |
| add | internal_dependencies | Kuadrant | * | <empty> | <empty> | ExtProc filters positioned relative to Kuadrant WasmPlugin in filter chain | deploy/overlays/odh/envoy-filter.yaml:6-11 |
| add | internal_dependencies | Kubernetes API | * | <empty> | <empty> | Reads ConfigMaps, Secrets, ExternalProviders, and ExternalModels CRDs | deploy/overlays/odh/rbac/clusterrole.yaml:6-15 |
| add | authentication | ExtProc gRPC :: All | * | <empty> | <empty> | Network-level auth via NetworkPolicy restricting ingress to gateway pods; optional TLS via DestinationRule | deploy/overlays/odh/networking/networkpolicy.yaml:26-36, deploy/overlays/odh/after/destination-rule.yaml:7-13 |
| add | authentication | Kubernetes API :: All | * | <empty> | <empty> | ServiceAccount token-based RBAC via ClusterRole payload-processing-reader | deploy/overlays/odh/rbac/clusterrole.yaml:1-15, deploy/overlays/odh/rbac/clusterrolebinding.yaml:1-12 |
