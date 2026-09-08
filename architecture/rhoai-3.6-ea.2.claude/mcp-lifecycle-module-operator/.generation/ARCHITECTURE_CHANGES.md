# Architecture Changes: mcp-lifecycle-module-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Health probe on :8081 uses plain HTTP with no TLS; healthz.Ping is a simple HTTP handler | cmd/main.go:155 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | Health probe is unauthenticated by design; uses controller-runtime healthz.Ping | cmd/main.go:155 |
| update | http_endpoints | GET :: /healthz | Owner | (empty) | cmd | The health check is registered in the cmd main function | cmd/main.go:155 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Readiness probe on :8081 uses plain HTTP with no TLS; healthz.Ping is a simple HTTP handler | cmd/main.go:159 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Readiness probe is unauthenticated by design; uses controller-runtime healthz.Ping | cmd/main.go:159 |
| update | http_endpoints | GET :: /readyz | Owner | (empty) | cmd | The readiness check is registered in the cmd main function | cmd/main.go:159 |
