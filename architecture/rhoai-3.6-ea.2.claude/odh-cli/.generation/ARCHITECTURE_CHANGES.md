# Architecture Changes: odh-cli

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | internal_dependencies | opendatahub-operator (failureclassifier) | * | <empty> | <empty> | opendatahub-operator failureclassifier package is imported for platform diagnostics failure classification | pkg/diagnose/run.go:1, pkg/diagnose/types.go:1 |
| add | internal_dependencies | opendatahub-operator (mcptools) | * | <empty> | <empty> | opendatahub-operator mcptools package is imported for MCP tool definitions | pkg/mcp/tools.go:1 |
| add | integration_points | TrustYAI Service :: HTTP Client | * | <empty> | <empty> | CLI makes HTTP GET/POST requests to TrustYAI Service via OpenShift Routes for metrics backup/restore during migration | pkg/migrate/actions/trustyai/metrics/http.go:29-36, pkg/migrate/actions/trustyai/metrics/http.go:71-120 |
| add | http_endpoints | GET :: /sse | * | <empty> | <empty> | MCP server SSE transport exposes HTTP endpoint on localhost:8080 for AI agent JSON-RPC integration (conditional, only when mcp serve --transport sse is invoked) | cmd/mcp/mcp.go:33-34, pkg/mcp/server.go:81-88 |
