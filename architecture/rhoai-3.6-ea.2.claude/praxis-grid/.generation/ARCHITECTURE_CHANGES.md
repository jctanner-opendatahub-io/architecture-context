# Architecture Changes: praxis-grid

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | integration_points | Praxis proxy :: Sidecar volume | * | <empty> | <empty> | Overlay-sync sidecar writes routing overlays to shared emptyDir consumed by Praxis | overlay-sync/src/main.rs:8 |
| add | integration_points | Provider Gateway Service :: Service Discovery | * | <empty> | <empty> | Operator discovers LoadBalancer IP of provider-gateway Service for SWIM advertisement | operator/src/gateway.rs:1-5, operator/src/gateway.rs:48 |
| add | integration_points | InferenceProvider backends :: HTTP probe | * | <empty> | <empty> | Operator probes health and scrapes metrics from inference endpoints over TLS | operator/src/resources/endpoint_tls.rs:8-9 |
| add | integration_points | SWIM peers :: UDP gossip | * | <empty> | <empty> | SWIM membership protocol for multi-site state propagation with optional AES-256-GCM encryption | operator/src/main.rs:162-208 |
| add | internal_dependencies | Praxis proxy | * | <empty> | <empty> | Data-plane gateway consuming routing overlays from shared emptyDir sidecar volume | overlay-sync/src/main.rs:8 |
| add | internal_dependencies | Kubernetes API Server | * | <empty> | <empty> | CRD management, Secret reading, ConfigMap management, and Service discovery | operator/src/main.rs:110-116, operator/src/resources/credentials.rs:35 |
