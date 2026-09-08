# Architecture Changes: trustyai-service

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| delete | authentication | HTTP API :: All | * | <empty> | <empty> | Replaced with port-specific authentication entries reflecting the split-listener architecture | src/trustyai_service/main.py:370-374 |
| add | authentication | Main API (port 8081) :: All | * | <empty> | <empty> | Main API binds to loopback only; kube-rbac-proxy provides authentication | src/trustyai_service/main.py:373-374 |
| add | authentication | Health/Consumer API (port 8080) :: All | * | <empty> | <empty> | Health and consumer endpoints are unauthenticated for kubelet and KServe/ModelMesh access | src/trustyai_service/main.py:336-340, src/trustyai_service/main.py:377 |
| add | authentication | HTTPS API (port 4443) :: All | * | <empty> | <empty> | Optional direct TLS access using system crypto policy certificates | src/trustyai_service/main.py:399-403, src/trustyai_service/service/tls.py:18-41 |
| add | integration_points | kube-rbac-proxy :: HTTP reverse proxy | * | <empty> | <empty> | Main API loopback binding requires kube-rbac-proxy for external access | src/trustyai_service/main.py:373-374 |
| add | integration_points | KServe Inference Logger :: CloudEvent consumer | * | <empty> | <empty> | CloudEvent consumer registered on health_app for KServe inference logging | src/trustyai_service/main.py:338-340 |
| add | integration_points | ModelMesh Agent :: HTTP consumer | * | <empty> | <empty> | KServe v2 consumer registered on health_app for ModelMesh payloads | src/trustyai_service/main.py:337-339 |
| add | integration_points | MariaDB :: SQL client | * | <empty> | <empty> | Optional database storage backend with TLS support | src/trustyai_service/service/data/storage/__init__.py:108-129 |
| add | integration_points | Prometheus :: Metrics scrape | * | <empty> | <empty> | Metrics endpoint at /q/metrics on health port | src/trustyai_service/endpoints/routes.py:85, src/trustyai_service/main.py:258-265 |
| add | internal_dependencies | kube-rbac-proxy | * | <empty> | <empty> | Authentication proxy required for main API access; loopback binding enforces this | src/trustyai_service/main.py:373-374 |
| add | internal_dependencies | KServe | * | <empty> | <empty> | Inference data source via CloudEvent consumer endpoint | src/trustyai_service/main.py:340 |
| add | internal_dependencies | ModelMesh | * | <empty> | <empty> | Inference data source via KServe v2 consumer endpoint | src/trustyai_service/main.py:339 |
