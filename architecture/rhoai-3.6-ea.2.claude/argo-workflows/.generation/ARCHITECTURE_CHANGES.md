# Architecture Changes: argo-workflows

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Argo Server API :: All | * | <empty> | <empty> | Gatekeeper interceptor enforces Bearer/Basic/SSO authentication on all argo-server gRPC and HTTP API endpoints | server/auth/gatekeeper.go:48-53, server/auth/gatekeeper.go:90-104, server/auth/mode.go:14-18, server/auth/gatekeeper.go:166-218 |
