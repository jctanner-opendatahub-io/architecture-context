# Architecture Changes: ogx-distribution

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /v1/health | * | <empty> | <empty> | Health check endpoint confirmed by smoke test curl and server config | tests/smoke.sh:99, distribution/config.yaml:257 |
| add | http_endpoints | GET :: /v1/models | * | <empty> | <empty> | Model listing endpoint confirmed by smoke test | tests/smoke.sh:116 |
| add | http_endpoints | POST :: /v1/chat/completions | * | <empty> | <empty> | OpenAI-compatible chat completions endpoint confirmed by smoke test | tests/smoke.sh:134 |
| add | http_endpoints | POST :: /v1/responses | * | <empty> | <empty> | Responses API endpoint established by config apis list | distribution/config.yaml:15 |
| add | http_endpoints | POST :: /v1/messages | * | <empty> | <empty> | Anthropic Messages API endpoint established by config apis list and provider comment | distribution/config.yaml:136 |
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Prometheus metrics endpoint established by ServiceMonitor configuration | config/monitoring/servicemonitor.yaml:16 |
| add | authentication | All API endpoints :: All | * | <empty> | <empty> | OAuth2 JWT authentication with JWKS validation and access policies configured in server auth block | distribution/config.yaml:259-281 |
| add | internal_dependencies | PostgreSQL | * | <empty> | <empty> | Required KV and SQL storage backend for all server subsystems | distribution/config.yaml:199-214 |
| add | internal_dependencies | vLLM | * | <empty> | <empty> | Primary inference backend configured as remote::vllm provider | distribution/config.yaml:25-29 |
| add | internal_dependencies | ogx-operator | * | <empty> | <empty> | Lifecycle management via ServiceMonitor label selector (app.kubernetes.io/managed-by: ogx-operator) | config/monitoring/servicemonitor.yaml:13 |
| add | integration_points | PostgreSQL :: SQL/KV client | * | <empty> | <empty> | KV and SQL state storage for all server subsystems | distribution/config.yaml:199-214 |
| add | integration_points | vLLM (inference) :: HTTP client | * | <empty> | <empty> | Primary inference backend for chat completions | distribution/config.yaml:25-29 |
| add | integration_points | vLLM (embedding) :: HTTP client | * | <empty> | <empty> | Embedding model inference | distribution/config.yaml:33-40 |
| add | integration_points | Milvus :: Client | * | <empty> | <empty> | Optional vector database for RAG with mTLS support | distribution/config.yaml:82-94 |
| add | integration_points | PGVector :: SQL client | * | <empty> | <empty> | Optional vector database via PostgreSQL extension | distribution/config.yaml:95-105 |
| add | integration_points | Qdrant :: HTTP/gRPC client | * | <empty> | <empty> | Optional vector database for RAG | distribution/config.yaml:106-121 |
| add | integration_points | OAuth2 Identity Provider :: JWKS client | * | <empty> | <empty> | JWT token validation via JWKS endpoint when AUTH_ISSUER configured | distribution/config.yaml:263-268 |
| add | integration_points | OpenTelemetry Collector :: OTLP exporter | * | <empty> | <empty> | Traces and metrics export when OTEL_SERVICE_NAME is set | distribution/entrypoint.sh:70-77 |
