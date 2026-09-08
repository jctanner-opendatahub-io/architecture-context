# Architecture Changes: MLServer

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: /v2 | * | <empty> | <empty> | V2 server metadata endpoint from FastAPI route registration | mlserver/rest/app.py:153 |
| add | http_endpoints | GET :: /v2/health/live | * | <empty> | <empty> | V2 liveness health check endpoint from FastAPI route registration | mlserver/rest/app.py:140 |
| add | http_endpoints | GET :: /v2/health/ready | * | <empty> | <empty> | V2 readiness health check endpoint from FastAPI route registration | mlserver/rest/app.py:141 |
| add | http_endpoints | GET :: /v2/models/{model_name} | * | <empty> | <empty> | V2 model metadata endpoint from FastAPI route registration | mlserver/rest/app.py:116-117 |
| add | http_endpoints | GET :: /v2/models/{model_name}/ready | * | <empty> | <empty> | V2 model readiness endpoint from FastAPI route registration | mlserver/rest/app.py:62-63 |
| add | http_endpoints | POST :: /v2/models/{model_name}/infer | * | <empty> | <empty> | V2 model inference endpoint from FastAPI route registration | mlserver/rest/app.py:71-74 |
| add | http_endpoints | POST :: /v2/models/{model_name}/generate | * | <empty> | <empty> | V2 model text generation endpoint (aliases infer handler) from FastAPI route registration | mlserver/rest/app.py:82-85 |
| add | http_endpoints | POST :: /v2/models/{model_name}/infer_stream | * | <empty> | <empty> | V2 streaming inference endpoint from FastAPI route registration | mlserver/rest/app.py:93-97 |
| add | http_endpoints | POST :: /v2/models/{model_name}/generate_stream | * | <empty> | <empty> | V2 streaming text generation endpoint from FastAPI route registration | mlserver/rest/app.py:104-109 |
| add | http_endpoints | POST :: /v2/repository/index | * | <empty> | <empty> | V2 model repository index endpoint from FastAPI route registration | mlserver/rest/app.py:166-169 |
| add | http_endpoints | POST :: /v2/repository/models/{model_name}/load | * | <empty> | <empty> | V2 model loading endpoint from FastAPI route registration | mlserver/rest/app.py:171-174 |
| add | http_endpoints | POST :: /v2/repository/models/{model_name}/unload | * | <empty> | <empty> | V2 model unloading endpoint from FastAPI route registration | mlserver/rest/app.py:176-179 |
| add | http_endpoints | GET :: /v2/runtimes | * | <empty> | <empty> | Runtime security information endpoint from FastAPI route registration | mlserver/rest/app.py:159-161 |
| add | http_endpoints | GET :: /metrics | * | <empty> | <empty> | Prometheus metrics export endpoint on dedicated metrics port 8082 | mlserver/settings.py:445, mlserver/rest/app.py:226-236 |
| add | integration_points | OpenTelemetry Collector :: OTLP gRPC export | * | <empty> | <empty> | MLServer exports distributed traces via OTLP gRPC when tracing_server is configured | mlserver/rest/app.py:7, mlserver/rest/app.py:192-205, mlserver/grpc/server.py:53-72 |
