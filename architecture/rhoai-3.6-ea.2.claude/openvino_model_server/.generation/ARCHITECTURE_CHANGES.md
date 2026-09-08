# Architecture Changes: openvino_model_server

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | POST :: /v1/models/{model}:predict | * | <empty> | <empty> | TFS v1 prediction endpoint registered in REST handler | src/http_rest_api_handler.cpp:102-103 |
| add | http_endpoints | POST :: /v1/models/{model}:classify | * | <empty> | <empty> | TFS v1 classification endpoint registered in REST handler | src/http_rest_api_handler.cpp:102-103 |
| add | http_endpoints | POST :: /v1/models/{model}:regress | * | <empty> | <empty> | TFS v1 regression endpoint registered in REST handler | src/http_rest_api_handler.cpp:102-103 |
| add | http_endpoints | GET :: /v1/models/{model}/metadata | * | <empty> | <empty> | TFS v1 model metadata endpoint registered in REST handler | src/http_rest_api_handler.cpp:104-105 |
| add | http_endpoints | POST :: /v1/config/reload | * | <empty> | <empty> | TFS v1 config reload endpoint registered in REST handler | src/http_rest_api_handler.cpp:106 |
| add | http_endpoints | GET :: /v1/config | * | <empty> | <empty> | TFS v1 config status endpoint registered in REST handler | src/http_rest_api_handler.cpp:107 |
| add | http_endpoints | GET :: /v2/health/ready | * | <empty> | <empty> | KServe v2 server readiness probe endpoint | src/http_rest_api_handler.cpp:115-116 |
| add | http_endpoints | GET :: /v2/health/live | * | <empty> | <empty> | KServe v2 server liveness probe endpoint | src/http_rest_api_handler.cpp:117-118 |
| add | http_endpoints | GET :: /v2 | * | <empty> | <empty> | KServe v2 server metadata endpoint | src/http_rest_api_handler.cpp:119-120 |
| add | http_endpoints | GET :: /v2/models/{model}/ready | * | <empty> | <empty> | KServe v2 model readiness endpoint | src/http_rest_api_handler.cpp:109-110 |
| add | http_endpoints | GET :: /v2/models/{model} | * | <empty> | <empty> | KServe v2 model metadata endpoint | src/http_rest_api_handler.cpp:111-112 |
| add | http_endpoints | POST :: /v2/models/{model}/infer | * | <empty> | <empty> | KServe v2 model inference endpoint | src/http_rest_api_handler.cpp:113-114 |
| add | http_endpoints | GET :: /v3/v1/models | * | <empty> | <empty> | OpenAI-compatible list models endpoint | src/http_rest_api_handler.cpp:122-123 |
| add | http_endpoints | GET :: /v3/v1/models/{model} | * | <empty> | <empty> | OpenAI-compatible retrieve model endpoint | src/http_rest_api_handler.cpp:124-125 |
| add | http_endpoints | POST :: /v3/{path} | * | <empty> | <empty> | OpenAI-compatible generative endpoints (chat completions, etc.) | src/http_rest_api_handler.cpp:126-127 |
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Prometheus metrics endpoint (when --metrics_enable is set) | src/http_rest_api_handler.cpp:129 |
| add | authentication | /v3/* generative endpoints :: All | * | <empty> | <empty> | API key authentication for generative endpoints via --api_key_file or API_KEY env var | src/cli_parser.cpp:42,174-177 |
| add | authentication | /v1/* and /v2/* inference endpoints :: All | * | <empty> | <empty> | Platform-delegated authentication for standard inference endpoints | src/cli_parser.cpp:70-80 |
| add | authentication | All endpoints (nginx-mtls-auth sidecar) :: All | * | <empty> | <empty> | mTLS authentication via optional nginx reverse proxy sidecar | extras/nginx-mtls-auth/model_server.conf.template:27-35 |
| add | integration_points | KServe :: ServingRuntime CR | * | <empty> | <empty> | OVMS registers as a KServe serving runtime via ClusterServingRuntime and ServingRuntime CRs | extras/kserve/kserve-openvino.yaml:1, extras/openshift_AI/ServingRuntime.yaml:1 |
| add | integration_points | Model Storage (PVC/S3) :: File system / object storage | * | <empty> | <empty> | Loads model artifacts from /mnt/models mount path | extras/kserve/kserve-openvino.yaml:18 |
| add | integration_points | Prometheus :: HTTP scrape | * | <empty> | <empty> | Exposes /metrics endpoint for Prometheus scraping when --metrics_enable is set | extras/kserve/kserve-openvino.yaml:12-13, src/cli_parser.cpp:138-141 |
| add | internal_dependencies | KServe | * | <empty> | <empty> | OVMS registers as a KServe serving runtime via ClusterServingRuntime and ServingRuntime CRs | extras/kserve/kserve-openvino.yaml:1, extras/openshift_AI/ServingRuntime.yaml:1 |
| add | grpc_services | tensorflow.serving.PredictionService | * | <empty> | <empty> | TFS PredictionService registered in gRPC server builder | src/grpcservermodule.cpp:140 |
| add | grpc_services | tensorflow.serving.ModelService | * | <empty> | <empty> | TFS ModelService registered in gRPC server builder | src/grpcservermodule.cpp:141 |
| add | grpc_services | inference.GRPCInferenceService | * | <empty> | <empty> | KServe v2 gRPC inference service registered in gRPC server builder | src/grpcservermodule.cpp:142 |
