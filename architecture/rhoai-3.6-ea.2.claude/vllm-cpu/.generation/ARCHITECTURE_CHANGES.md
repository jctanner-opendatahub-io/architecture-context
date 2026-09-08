# Architecture Changes: vllm-cpu

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Replace generic auth row with guarded-prefix and unauthenticated rows reflecting actual enforcement | vllm/entrypoints/serve/utils/server_utils.py:41, vllm/entrypoints/serve/utils/server_utils.py:89 |
| add | authentication | /v1, /v2, /inference prefixed paths :: All (except OPTIONS) | * | <empty> | <empty> | Auth middleware guards only paths starting with /v1, /v2, /inference; conditional on api-key being set | vllm/entrypoints/serve/utils/server_utils.py:41-42, vllm/entrypoints/serve/utils/server_utils.py:89, vllm/entrypoints/openai/api_server.py:258-261 |
| add | authentication | /health, /ready, /readyz, /load, /docs, /ping :: All | * | <empty> | <empty> | Operational endpoints bypass authentication middleware because they do not match GUARDED_PREFIX | vllm/entrypoints/serve/utils/server_utils.py:41, vllm/entrypoints/serve/utils/server_utils.py:89 |
| add | grpc_services | VllmEngine | * | <empty> | <empty> | gRPC inference service backed by smg-grpc-servicer on default port 50051 with insecure transport | vllm/entrypoints/grpc_server.py:101, vllm/entrypoints/grpc_server.py:109, vllm/entrypoints/grpc_server.py:118, vllm/entrypoints/grpc_server.py:184 |
| add | grpc_services | grpc.health.v1.Health | * | <empty> | <empty> | Standard gRPC health service for Kubernetes probes co-hosted on port 50051 | vllm/entrypoints/grpc_server.py:104-105, vllm/entrypoints/grpc_server.py:110 |
| add | integration_points | smg-grpc-servicer :: Python package | * | <empty> | <empty> | Optional gRPC servicer package providing VllmEngine implementation | vllm/entrypoints/grpc_server.py:31-33, vllm/entrypoints/grpc_server.py:36-40 |
