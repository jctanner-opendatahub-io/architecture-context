# Architecture Changes: mcp-lifecycle-operator

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /healthz | Transport | `<empty>` | HTTP/1.1 | HTTP/2 disabled by default; probe endpoint bound to plain HTTP port 8081 | cmd/main.go:84, cmd/main.go:98-101 |
| update | http_endpoints | GET :: /healthz | Encryption | Unknown | None | Probe endpoint on port 8081 uses plain HTTP with no TLS; TLS only applies to metrics port 8443 | cmd/main.go:71, cmd/main.go:205 |
| update | http_endpoints | GET :: /healthz | Auth | Unknown | None | Health probe uses healthz.Ping handler with no authentication middleware | cmd/main.go:205 |
| update | http_endpoints | GET :: /healthz | Owner | `<empty>` | cmd | Handler registered in cmd/main.go main function via mgr.AddHealthzCheck | cmd/main.go:205 |
| update | http_endpoints | GET :: /healthz | Purpose | httpGet probe | Health probe endpoint | Descriptive purpose label for health check endpoint | cmd/main.go:205 |
| update | http_endpoints | GET :: /readyz | Transport | `<empty>` | HTTP/1.1 | HTTP/2 disabled by default; probe endpoint bound to plain HTTP port 8081 | cmd/main.go:84, cmd/main.go:98-101 |
| update | http_endpoints | GET :: /readyz | Encryption | Unknown | None | Probe endpoint on port 8081 uses plain HTTP with no TLS; TLS only applies to metrics port 8443 | cmd/main.go:71, cmd/main.go:209 |
| update | http_endpoints | GET :: /readyz | Auth | Unknown | None | Readiness probe uses readyz.Ping handler with no authentication middleware | cmd/main.go:209 |
| update | http_endpoints | GET :: /readyz | Owner | `<empty>` | cmd | Handler registered in cmd/main.go main function via mgr.AddReadyzCheck | cmd/main.go:209 |
| update | http_endpoints | GET :: /readyz | Purpose | httpGet probe | Readiness probe endpoint | Descriptive purpose label for readiness check endpoint | cmd/main.go:209 |
