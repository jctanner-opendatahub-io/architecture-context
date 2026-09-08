# Architecture Changes: trustyai-service-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Metrics server :: GET | * | <empty> | <empty> | Metrics endpoint uses Kubernetes token delegation via controller-runtime WithAuthenticationAndAuthorization when secureMetrics flag is enabled | cmd/main.go:159-161 |
| add | internal_dependencies | OpenDataHub Operator (DSC ConfigMap) :: ConfigMap read | * | <empty> | <empty> | DSCConfigReader reads trustyai-dsc-config ConfigMap created by OpenDataHub operator for evaluation security policy settings (permitOnline, permitCodeExecution) | controllers/dsc/config.go:17-49 |
