# Architecture Changes: odh-gitops

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | architecture_components | rhai-on-openshift-chart | * | <empty> | <empty> | Helm chart is a deployable architecture component for OpenShift RHOAI dependency installation | charts/rhai-on-openshift-chart/Chart.yaml:1-3 |
| add | architecture_components | rhai-on-xks-chart | * | <empty> | <empty> | Helm chart is a deployable architecture component for non-OpenShift RHAI installation | charts/rhai-on-xks-chart/Chart.yaml:1-3 |
| add | architecture_components | kustomize-dependencies | * | <empty> | <empty> | Kustomize overlay composes operator subscriptions as a deployable configuration unit | dependencies/operators/kustomization.yaml:4-17 |
| add | architecture_components | kustomize-configurations | * | <empty> | <empty> | Kustomize overlay applies post-install operator configurations | configurations/kustomization.yaml:4-10 |
| add | authentication | Platform Services :: All | * | <empty> | <empty> | Authorino CR deployed cluster-wide with TLS listener for platform-wide authorization | configurations/rhcl-operator/tls-enabled/authorino-tls.yaml:6-15 |
| add | integration_points | Authorino :: CRD Configuration | * | <empty> | <empty> | Deploys cluster-wide Authorino instance with TLS-enabled listener | configurations/rhcl-operator/tls-enabled/authorino-tls.yaml:1-15 |
| add | integration_points | Kuadrant :: CRD Configuration | * | <empty> | <empty> | Deploys Kuadrant control plane CR in kuadrant-system namespace | configurations/rhcl-operator/kuadrant.yaml:1-5 |
| add | integration_points | cert-manager :: OLM / Helm Sub-chart | * | <empty> | <empty> | Provisions TLS certificate automation for platform services | charts/dependencies/cert-manager-operator/Chart.yaml:1-3 |
| add | integration_points | Sail Operator :: Helm Sub-chart | * | <empty> | <empty> | Installs Istio service mesh on non-OpenShift clusters | charts/dependencies/sail-operator/Chart.yaml:1-3 |
| add | integration_points | Gateway API :: Helm Sub-chart | * | <empty> | <empty> | Installs Gateway API CRDs for ingress on non-OpenShift clusters | charts/dependencies/gateway-api/Chart.yaml:1-3 |
| add | internal_dependencies | Kueue Operator | * | <empty> | <empty> | Required operator for job scheduling and resource quota management | dependencies/operators/kustomization.yaml:6 |
| add | internal_dependencies | JobSet Operator | * | <empty> | <empty> | Required operator for multi-pod job orchestration | dependencies/operators/kustomization.yaml:7 |
| add | internal_dependencies | LeaderWorkerSet | * | <empty> | <empty> | Required operator for leader-worker topology distributed workloads | dependencies/operators/kustomization.yaml:8 |
| add | internal_dependencies | RHCL Operator (Kuadrant) | * | <empty> | <empty> | Required operator for API gateway, authorization (Authorino), and rate limiting | dependencies/operators/kustomization.yaml:9 |
| add | internal_dependencies | cert-manager | * | <empty> | <empty> | Required operator for TLS certificate lifecycle management | dependencies/operators/kustomization.yaml:5 |
| add | internal_dependencies | Cluster Observability Operator | * | <empty> | <empty> | Required operator for cluster monitoring and metrics | dependencies/operators/kustomization.yaml:6 |
| add | internal_dependencies | OpenTelemetry Operator | * | <empty> | <empty> | Required operator for distributed tracing instrumentation | dependencies/operators/kustomization.yaml:7 |
| add | internal_dependencies | Tempo Operator | * | <empty> | <empty> | Required operator for trace storage backend | dependencies/operators/kustomization.yaml:12 |
| add | internal_dependencies | Custom Metrics Autoscaler | * | <empty> | <empty> | Required operator for HPA-based autoscaling with custom metrics | dependencies/operators/kustomization.yaml:13 |
| add | internal_dependencies | Sail Operator (Istio) | * | <empty> | <empty> | XKS-only operator for service mesh on non-OpenShift deployments | charts/dependencies/sail-operator/Chart.yaml:3 |
| add | internal_dependencies | Gateway API CRDs | * | <empty> | <empty> | XKS-only Gateway API resource definitions | charts/dependencies/gateway-api/Chart.yaml:3 |
| add | internal_dependencies | NFD | * | <empty> | <empty> | Optional operator for node feature discovery for GPU/accelerator nodes | configurations/kustomization.yaml:10 |
| add | internal_dependencies | NVIDIA GPU Operator | * | <empty> | <empty> | Optional operator for GPU device plugin and driver management | configurations/kustomization.yaml:11 |
