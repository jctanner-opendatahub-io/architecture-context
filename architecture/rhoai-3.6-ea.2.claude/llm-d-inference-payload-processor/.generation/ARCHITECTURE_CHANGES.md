# Architecture Changes: llm-d-inference-payload-processor

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Controller-runtime metrics server exposes Prometheus metrics endpoint with optional Kubernetes TokenReview authentication | cmd/runner/runner.go:173-182, pkg/server/options.go:65 |
| update | grpc_services | ExternalProcessor | Port |  | 9004 | Default gRPC port for ExtProc server defined in options constants | pkg/server/options.go:28 |
| update | grpc_services | ExternalProcessor | Purpose | Registered External Processor gRPC service | Envoy External Processor gRPC service | Clarify purpose to reflect Envoy ExtProc API role | pkg/server/runserver.go:76 |
| update | grpc_services | Health | Port |  | 9005 | Default gRPC health port defined in options constants | pkg/server/options.go:29 |
| update | grpc_services | Health | Purpose | Registered Health gRPC service | gRPC health check service for liveness and readiness probes | Clarify purpose to reflect probe role | cmd/runner/runner.go:312-322 |
| add | authentication | Metrics HTTP :: HTTP | * | <empty> | <empty> | Metrics endpoint uses Kubernetes TokenReview/SubjectAccessReview auth via controller-runtime filters (default enabled) | cmd/runner/runner.go:175-181, pkg/server/options.go:68 |
