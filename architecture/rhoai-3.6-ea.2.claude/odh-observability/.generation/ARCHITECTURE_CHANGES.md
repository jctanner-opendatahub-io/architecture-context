# Architecture Changes: odh-observability

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | data-science-prometheus-cluster-proxy:8443 :: All | * | <empty> | <empty> | kube-rbac-proxy enforces SubjectAccessReview against metrics.k8s.io/nodes:get for cluster-wide Prometheus access | internal/controller/resources/data-science-prometheus-cluster-proxy.tmpl.yaml:51-56,78-97 |
| add | authentication | data-science-prometheus-namespace-proxy:8443 :: All | * | <empty> | <empty> | kube-rbac-proxy enforces namespace-scoped SubjectAccessReview against metrics.k8s.io/pods via query parameter rewrite | internal/controller/resources/data-science-prometheus-namespace-proxy.tmpl.yaml:74-84,109-120 |
