# Architecture Changes: odh-model-controller

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | authentication | /metrics :: Unknown | Auth Mechanism | Unknown | None (TLS transport only) | Source inspection confirms promhttp.Handler() served behind TLS without authentication middleware | server/observability/observability.go:87 |
| update | authentication | /metrics :: Unknown | Enforcement Point | Application (model-serving-api) | N/A | No application-level authentication middleware wraps the metrics handler; enforcement is transport-only via TLS | server/observability/observability.go:87-93 |
| update | authentication | /metrics :: Unknown | Policy | Dedicated metrics listener on port 8080; authentication not established by source | model-serving-api metrics on port 8080; TLS-encrypted via OpenShift service-ca certificate but no application-level authentication middleware | Source confirms TLS config present but no auth handler wrapping promhttp.Handler() | server/observability/observability.go:87-93, config/server/service.yaml:1 |
| add | authentication | model-serving-api /api/v1/gateways :: Unknown | * | <empty> | <empty> | Bearer token authentication enforced by middleware.Auth; extracts token from Authorization header and returns 401 if missing | server/server.go:23, server/middleware/auth.go:24-38 |
| add | authentication | model-serving-api /api/v1/samples/llm-d :: Unknown | * | <empty> | <empty> | Explicitly unauthenticated by design; serves static embedded YAML sample templates | server/server.go:25-27 |
