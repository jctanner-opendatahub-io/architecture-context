workspace {
    model {
        datascientist = person "Data Scientist" "Deploys and queries LLM models for inference"
        application = person "Application Developer" "Integrates LLM inference into applications via API"

        vllmCpu = softwareSystem "vllm-cpu" "CPU-optimized high-throughput LLM inference and serving engine with OpenAI-compatible APIs" {
            httpServer = container "FastAPI HTTP Server" "OpenAI/Anthropic-compatible API server with modular routers" "Python/FastAPI/Uvicorn"
            authMiddleware = container "Authentication Middleware" "ASGI middleware for conditional Bearer token validation (SHA-256, constant-time)" "Python ASGI"
            grpcServer = container "gRPC Server" "Optional gRPC inference endpoint via smg-grpc-servicer on port 50051" "Python/gRPC"
            asyncLLMEngine = container "AsyncLLM Engine" "Core CPU-optimized model inference engine" "Python/vLLM"
        }

        smgGrpcServicer = softwareSystem "smg-grpc-servicer" "gRPC service implementation for VllmEngine" "External Package"
        kubernetes = softwareSystem "Kubernetes" "Container orchestration platform" "Infrastructure"
        serviceMesh = softwareSystem "Service Mesh / Sidecar" "Provides mTLS and transport encryption for gRPC" "Infrastructure"
        modelStorage = softwareSystem "Model Storage" "S3-compatible or local model artifact storage" "External"
        openshift = softwareSystem "OpenShift / RHOAI" "Red Hat OpenShift AI platform providing serving runtime management" "Platform"

        # External relationships
        datascientist -> vllmCpu "Sends inference requests via HTTP API or gRPC"
        application -> vllmCpu "Integrates via OpenAI-compatible REST API"
        kubernetes -> vllmCpu "Manages pod lifecycle, sends health probes"
        openshift -> vllmCpu "Deploys as ServingRuntime pod"
        vllmCpu -> modelStorage "Loads model artifacts at startup" "HTTPS/S3"
        serviceMesh -> vllmCpu "Provides transport encryption for gRPC port"

        # Internal relationships
        datascientist -> httpServer "POST /v1/chat/completions, /v1/embeddings" "HTTP/HTTPS"
        application -> httpServer "POST /v1/completions, /v1/messages" "HTTP/HTTPS"
        application -> grpcServer "VllmEngine.Generate()" "gRPC/50051"
        httpServer -> authMiddleware "Routes guarded paths (/v1, /v2, /inference)"
        authMiddleware -> asyncLLMEngine "Forwards authenticated requests"
        grpcServer -> asyncLLMEngine "Forwards gRPC inference requests"
        kubernetes -> httpServer "GET /health, /ready, /readyz" "HTTP"
        kubernetes -> grpcServer "grpc.health.v1.Health.Check()" "gRPC"
        grpcServer -> smgGrpcServicer "Uses for VllmEngine service implementation" "Python import"
    }

    views {
        systemContext vllmCpu "SystemContext" {
            include *
            autoLayout
        }

        container vllmCpu "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
            }
            element "Infrastructure" {
                background #999999
            }
            element "Platform" {
                background #7ed321
            }
            element "External Package" {
                background #d4a017
            }
        }
    }
}
