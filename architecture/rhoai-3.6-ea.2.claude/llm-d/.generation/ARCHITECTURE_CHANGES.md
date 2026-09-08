# Architecture Changes: llm-d

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | POST :: /v1/completions | * | <empty> | <empty> | vllm OpenAI-compatible text completions endpoint established by Dockerfile entrypoint | docker/Dockerfile.cpu:142 |
| add | http_endpoints | POST :: /v1/chat/completions | * | <empty> | <empty> | vllm OpenAI-compatible chat completions endpoint established by Dockerfile entrypoint | docker/Dockerfile.cpu:142 |
| add | grpc_services | envoy.service.ext_proc.v3.ExternalProcessor | * | <empty> | <empty> | EPP gRPC ext_proc service for inference routing decisions via Envoy | guides/no-kubernetes-deployment/router/envoy/envoy.yaml:120 |
| add | internal_dependencies | vllm | * | <empty> | <empty> | Model serving runtime backend started by Dockerfile entrypoint | docker/Dockerfile.cpu:142 |
| add | internal_dependencies | llm-d-router | * | <empty> | <empty> | Envoy proxy and EPP for intelligent inference request routing | guides/recipes/router/base.values.yaml:1-2 |
| add | internal_dependencies | Gateway API (InferencePool) | * | <empty> | <empty> | InferencePool CRD defines model server pool for routing decisions | guides/recipes/router/base.values.yaml:17 |
| add | integration_points | llm-d-router EPP :: ext_proc gRPC | * | <empty> | <empty> | EPP provides routing decisions via Envoy ext_proc on port 9002 | guides/no-kubernetes-deployment/router/envoy/envoy.yaml:60-63 |
| add | integration_points | OpenTelemetry Collector :: OTLP export | * | <empty> | <empty> | Distributed tracing via OTLP gRPC on port 4317 | guides/recipes/observability/tracing/otel-collector.yaml:14 |
| add | integration_points | nixl :: RDMA transfer | * | <empty> | <empty> | KV-cache transfer between prefill and decode pods on port 5600 | guides/recipes/modelserver/base/single-host/pd/base/prefill-deployment.yaml:29 |
| add | authentication | Model Server API :: GET, POST | * | <empty> | <empty> | vllm serving endpoints have no built-in auth; security is platform-delegated | guides/recipes/modelserver/base/single-host/default/decode-deployment.yaml:24-26 |
| add | authentication | ModelExpress Broker :: gRPC | * | <empty> | <empty> | Strict mTLS with AuthorizationPolicy restricts port 8001 to decode ServiceAccount | guides/modelexpress-p2p/security/istio-mtls-authz.yaml:9-42 |
