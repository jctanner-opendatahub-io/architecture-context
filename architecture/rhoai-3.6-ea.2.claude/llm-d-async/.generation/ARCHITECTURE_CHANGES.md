# Architecture Changes: llm-d-async

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | /metrics :: HTTP | * | <empty> | <empty> | Metrics endpoint on port 9090 uses controller-runtime WithAuthenticationAndAuthorization filters delegating to Kubernetes API server | pkg/server/runner.go:353-361, pkg/server/options.go:98 |
| add | integration_points | Redis :: TCP client | * | <empty> | <empty> | Redis is a primary message queue transport backend (redis-pubsub, redis-sortedset) for async inference request routing | pkg/server/runner.go:302-315, pkg/redis/redis_conn.go:10-18 |
| add | integration_points | Google Cloud Pub/Sub :: gRPC client | * | <empty> | <empty> | Google Cloud Pub/Sub is an alternative message queue transport backend for async inference request routing | pkg/server/runner.go:316-328, pkg/pubsub/pubsubimpl.go:12-14 |
| add | integration_points | Inference Gateway :: HTTP client | * | <empty> | <empty> | Outbound HTTP client dispatches inference requests to downstream model servers with optional mTLS | pkg/server/runner.go:374-392, pkg/server/options.go:152-155 |
| add | integration_points | Prometheus :: HTTP client | * | <empty> | <empty> | Prometheus metric queries drive flow-control gate decisions for worker pool dispatch | pkg/server/runner.go:97-98, pkg/server/options.go:112-113 |
| update | integration_points | gateway-api-inference-extension :: Go library | Encryption | Unknown | N/A | Go library dependency has no network transport; encryption is not applicable | pkg/async/inference/flowcontrol/binary_metric_dispatch_gate.go:27 |
| update | integration_points | gateway-api-inference-extension :: Go library | Purpose | Use runtime packages from sigs.k8s.io/gateway-api-inference-extension | Flow-control primitives and logging utilities | Source inspection shows the dependency provides flow-control gate types and logging utilities, not generic runtime packages | pkg/async/inference/flowcontrol/binary_metric_dispatch_gate.go:27, pkg/pubsub/pubsubimpl.go:24 |
