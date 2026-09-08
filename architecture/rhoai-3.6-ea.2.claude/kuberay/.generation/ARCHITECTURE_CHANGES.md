# Architecture Changes: kuberay

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Ray Dashboard :: GET, POST | * | <empty> | <empty> | AuthenticationController injects kube-rbac-proxy sidecar for OIDC/OAuth authentication on Ray dashboard access | ray-operator/controllers/ray/authentication_controller.go:45-53, ray-operator/controllers/ray/authentication_controller.go:147-161 |
| update | internal_dependencies | Prometheus | Role | unknown | metrics-provider | Service annotations confirm standard Prometheus scrape pattern on port 8080 | ray-operator/config/manager/service.yaml:3-7 |
| update | internal_dependencies | cert-manager | Role | unknown | certificate-provider | RayClusterMTLSController creates Certificate and Issuer CRDs for Ray cluster mTLS | ray-operator/controllers/ray/raycluster_mtls_controller.go:24-39 |
| update | internal_dependencies | Gateway API | Role | unknown | runtime-transport | AuthenticationController creates HTTPRoute and ReferenceGrant for authenticated dashboard routing | ray-operator/controllers/ray/authentication_controller.go:110-112 |
| update | internal_dependencies | cert-manager | Role | unknown | certificate-provider | Second cert-manager dependency also serves certificate provisioning for head/worker mTLS | ray-operator/controllers/ray/raycluster_mtls_controller.go:24-39 |
