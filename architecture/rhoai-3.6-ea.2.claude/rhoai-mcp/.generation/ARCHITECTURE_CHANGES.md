# Architecture Changes: rhoai-mcp

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | GET :: /health | Auth | Unknown | None | Health endpoint is explicitly excluded from OIDCAuthMiddleware; no authentication is enforced | src/rhoai_mcp/server.py:385 |
| update | http_endpoints | GET :: /health | Purpose | httpGet probe | httpGet probe (Kubernetes liveness/readiness) | Clarifies the probe is used for both K8s liveness and readiness checks | src/rhoai_mcp/server.py:516-517 |
| add | http_endpoints | GET :: /.well-known/oauth-protected-resource | * | <empty> | <empty> | OIDC Protected Resource Metadata endpoint registered via custom_route when OIDC is enabled | src/rhoai_mcp/server.py:370-380 |
| add | authentication | MCP API (SSE/streamable-http) :: All | * | <empty> | <empty> | OIDCAuthMiddleware wraps SSE and streamable-http ASGI apps; validates bearer tokens via JWT or TokenReview; tool-level RBAC filtering via SubjectAccessReview | src/rhoai_mcp/server.py:382-415, src/rhoai_mcp/server.py:419-504 |
| add | authentication | /health :: GET | * | <empty> | <empty> | Health endpoint excluded from authentication middleware via exclude_paths | src/rhoai_mcp/server.py:385 |
| add | authentication | /.well-known/oauth-protected-resource :: GET | * | <empty> | <empty> | OIDC metadata endpoint excluded from authentication middleware via exclude_paths | src/rhoai_mcp/server.py:385-386 |
| add | internal_dependencies | Data Science Pipelines (opendatahub.io) | * | <empty> | <empty> | RBAC ClusterRole grants CRUD on datasciencepipelinesapplications.opendatahub.io CRDs | deploy/kustomize/base/clusterrole.yaml:1 |
| add | internal_dependencies | Kubeflow Training (trainer.kubeflow.org) | * | <empty> | <empty> | RBAC ClusterRole grants CRUD on trainjobs, trainingruntimes, and clustertrainingruntimes CRDs | deploy/kustomize/base/clusterrole.yaml:1 |
| add | internal_dependencies | Model Registry | * | <empty> | <empty> | HTTP client integration with configurable URL, auth mode, and TLS settings | src/rhoai_mcp/config.py:190-219 |
| add | internal_dependencies | Planner Backend | * | <empty> | <empty> | HTTP client integration with planner service for intent extraction | src/rhoai_mcp/config.py:222-231 |
