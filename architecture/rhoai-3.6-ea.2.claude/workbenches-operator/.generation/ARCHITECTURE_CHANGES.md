# Architecture Changes: workbenches-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | internal_dependencies | cert-manager | Role | unknown | tls-provider | Operator creates cert-manager Certificate CRs for webhook TLS provisioning; webhook-tls-role grants create/get/patch on cert-manager.io certificates | cmd/main.go:132 |
| update | internal_dependencies | HardwareProfile CR | Role | unknown | runtime-configuration | Hardware profile webhook reads HardwareProfile CRs to inject compute resource requests and tolerations into notebooks | cmd/main.go:88-89 |
| update | internal_dependencies | Kubeflow Notebooks (kubeflow.org) | Role | unknown | managed-workload | Controller has full CRUD RBAC on kubeflow.org notebooks; operator creates and manages notebook workbenches as its primary function | internal/controller/workbenches_controller.go:109 |
| update | internal_dependencies | Platform orchestrator | Role | unknown | configuration-source | Reads odh-workbenches-config ConfigMap for distribution name, version, and platform version handshake | internal/platformconfig/config.go:80 |
| update | integration_points | cert-manager :: Certificate CR | Role | unknown | tls-provider | Webhook TLS certificate provisioning through cert-manager CRD interaction | cmd/main.go:132 |
| update | integration_points | HardwareProfile CR :: CRD CRUD | Role | unknown | runtime-configuration | Hardware profile webhook resolves HardwareProfile CRs for resource injection | cmd/main.go:88-89 |
| update | integration_points | Kubeflow Notebooks :: CRD CRUD | Role | unknown | managed-workload | Operator manages notebook workbench lifecycle as primary function | internal/controller/workbenches_controller.go:109 |
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | HTTP probe endpoint on port 8081 with no TLS; health-probe-bind-address defaults to :8081 | cmd/main.go:80, cmd/main.go:213 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | healthz.Ping handler registered with no authentication middleware | cmd/main.go:213 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | HTTP probe endpoint on port 8081 with no TLS; health-probe-bind-address defaults to :8081 | cmd/main.go:80, cmd/main.go:218 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | readyz.Ping handler registered with no authentication middleware | cmd/main.go:218 |
