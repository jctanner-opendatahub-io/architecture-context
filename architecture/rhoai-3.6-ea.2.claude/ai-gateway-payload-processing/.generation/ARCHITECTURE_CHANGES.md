# Architecture Changes: ai-gateway-payload-processing

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Controller-runtime metrics server exposes Prometheus metrics endpoint with optional authentication | cmd/runner.go:147-155 |
| add | integration_points | networking.istio.io/ServiceEntry :: Resource CRUD | * | <empty> | <empty> | ExternalProvider controller creates Istio ServiceEntry for each provider to register external endpoints in the service mesh | pkg/controller/externalprovider/reconciler.go:117-122 |
| add | integration_points | networking.istio.io/DestinationRule :: Resource CRUD | * | <empty> | <empty> | ExternalProvider controller creates Istio DestinationRule for TLS origination to external provider endpoints | pkg/controller/externalprovider/reconciler.go:124-129 |
