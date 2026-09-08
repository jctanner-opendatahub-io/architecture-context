# Architecture Changes: trainer-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | :8443/metrics :: GET | * | <empty> | <empty> | Metrics endpoint uses HTTPS with Kubernetes TokenReview and SubjectAccessReview authn/authz via controller-runtime WithAuthenticationAndAuthorization filter | internal/tls/metrics.go:42, cmd/main.go:78-79, cmd/main.go:112 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | Health probe is unauthenticated by design; analyzer had Unknown | cmd/main.go:199 |
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Health probe on port 8081 has no TLS | cmd/main.go:82 |
| update | http_endpoints | GET :: /healthz | Owner |  | cmd | Owner is the cmd entrypoint main function | cmd/main.go:199 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Readiness probe is unauthenticated by design; analyzer had Unknown | cmd/main.go:203 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Readiness probe on port 8081 has no TLS | cmd/main.go:82 |
| update | http_endpoints | GET :: /readyz | Owner |  | cmd | Owner is the cmd entrypoint main function | cmd/main.go:203 |
