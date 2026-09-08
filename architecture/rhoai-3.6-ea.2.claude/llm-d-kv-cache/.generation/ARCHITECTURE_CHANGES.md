# Architecture Changes: llm-d-kv-cache

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| update | http_endpoints | Unknown :: /metrics | Method | Unknown | GET | Prometheus handler is read-only GET endpoint | examples/kv_events/online/main.go:244 |
| update | http_endpoints | Unknown :: /metrics | Port | (empty) | 8080/TCP | HTTP server binds to port from HTTP_PORT env, default 8080 | examples/kv_events/online/main.go:57, 301-304 |
| update | http_endpoints | Unknown :: /metrics | Encryption | Unknown | None | ListenAndServe without TLS, no TLS configuration | examples/kv_events/online/main.go:316 |
| update | http_endpoints | Unknown :: /metrics | Auth | Unknown | None | No auth middleware on HTTP mux | examples/kv_events/online/main.go:242-244 |
| update | http_endpoints | Unknown :: /score_completions | Method | Unknown | POST | Handler decodes JSON request body | examples/kv_events/online/main.go:248-253 |
| update | http_endpoints | Unknown :: /score_completions | Port | (empty) | 8080/TCP | HTTP server binds to port from HTTP_PORT env, default 8080 | examples/kv_events/online/main.go:57, 301-304 |
| update | http_endpoints | Unknown :: /score_completions | Encryption | Unknown | None | ListenAndServe without TLS | examples/kv_events/online/main.go:316 |
| update | http_endpoints | Unknown :: /score_completions | Auth | Unknown | None | No auth middleware on HTTP mux | examples/kv_events/online/main.go:242, 248 |
| update | http_endpoints | Unknown :: /score_chat_completions | Method | Unknown | POST | Explicit MethodPost check in handler | examples/kv_events/online/main.go:275-277 |
| update | http_endpoints | Unknown :: /score_chat_completions | Port | (empty) | 8080/TCP | HTTP server binds to port from HTTP_PORT env, default 8080 | examples/kv_events/online/main.go:57, 301-304 |
| update | http_endpoints | Unknown :: /score_chat_completions | Encryption | Unknown | None | ListenAndServe without TLS | examples/kv_events/online/main.go:316 |
| update | http_endpoints | Unknown :: /score_chat_completions | Auth | Unknown | None | No auth middleware on HTTP mux | examples/kv_events/online/main.go:242, 274 |
| update | grpc_services | IndexerService | Port | (empty) | Configured by runtime | Server listens on configurable address | examples/kv_cache_index_service/server/main.go:103-104 |
| update | grpc_services | IndexerService | Encryption | Unknown | None | grpc.NewServer with no TLS credentials | examples/kv_cache_index_service/server/main.go:98-99 |
| update | grpc_services | IndexerService | Auth | Unknown | None | No auth interceptor configured | examples/kv_cache_index_service/server/main.go:98-99 |
| add | services | {{ .Release.Name }}-kv-cache-manager (zmq) | * | <empty> | <empty> | Helm chart defines ClusterIP Service with ZMQ port for vLLM event subscription | vllm-setup-helm/templates/kv-cache-manager.yaml:2-19 |
| add | services | {{ .Release.Name }}-kv-cache-manager (http) | * | <empty> | <empty> | Helm chart defines ClusterIP Service with HTTP port for scoring API | vllm-setup-helm/templates/kv-cache-manager.yaml:2-23 |
| add | authentication | HTTP Scoring API :: POST | * | <empty> | <empty> | No authentication on HTTP scoring endpoints; handlers registered without middleware | examples/kv_events/online/main.go:242-298 |
| add | authentication | gRPC IndexerService :: All | * | <empty> | <empty> | No authentication on gRPC server; created with stats handler only | examples/kv_cache_index_service/server/main.go:98-101 |
| add | authentication | Kubernetes API :: All | * | <empty> | <empty> | ServiceAccount token authentication for Kubernetes API access | examples/kv_events/pod_reconciler/pod_reconciler.go:91, 180 |
