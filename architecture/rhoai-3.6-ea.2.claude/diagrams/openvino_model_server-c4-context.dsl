workspace {
    model {
        dataScientist = person "Data Scientist" "Deploys and queries ML models via InferenceService"
        mlEngineer = person "ML Engineer" "Configures serving runtimes and model deployments"

        ovms = softwareSystem "OpenVINO Model Server" "High-performance C++ inference server supporting TFS v1, KServe v2, and OpenAI-compatible v3 APIs" {
            grpcServer = container "gRPC Server" "Handles gRPC inference requests via TFS PredictionService, TFS ModelService, and KFS GRPCInferenceService" "C++ / gRPC"
            restServer = container "REST Server" "Handles HTTP inference requests via TFS v1, KFS v2, and OpenAI v3 endpoint handlers" "C++ / HTTP"
            modelManager = container "Model Manager" "Loads, manages, and serves model instances from configured model paths" "C++ / OpenVINO Runtime"
            metricsEndpoint = container "Metrics Endpoint" "Exposes Prometheus metrics at /metrics when enabled" "C++ / HTTP"
            nginxSidecar = container "nginx mTLS Sidecar" "Optional TLS termination and client certificate verification proxy" "nginx" "Optional"

            grpcServer -> modelManager "Dispatches inference requests"
            restServer -> modelManager "Dispatches inference requests"
            nginxSidecar -> grpcServer "Proxies gRPC traffic via grpc_pass (loopback)"
            nginxSidecar -> restServer "Proxies REST traffic via proxy_pass (loopback)"
        }

        kserve = softwareSystem "KServe" "ML model serving controller on Kubernetes" "Internal RHOAI"
        modelStorage = softwareSystem "Model Storage" "PVC or S3-backed storage for model artifacts at /mnt/models" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "Internal RHOAI"
        istio = softwareSystem "Istio / Service Mesh" "Service mesh providing traffic management and platform-level auth" "Internal RHOAI"

        dataScientist -> ovms "Sends inference requests" "REST/gRPC"
        mlEngineer -> kserve "Creates InferenceService CRs" "kubectl / Dashboard"
        kserve -> ovms "Deploys via ServingRuntime CRs" "Kubernetes API"
        ovms -> modelStorage "Loads model artifacts" "File I/O"
        prometheus -> ovms "Scrapes /metrics endpoint" "HTTP"
        istio -> ovms "Routes traffic, enforces auth policy" "Service Mesh"
    }

    views {
        systemContext ovms "SystemContext" {
            include *
            autoLayout
        }

        container ovms "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal RHOAI" {
                background #7ed321
            }
            element "Optional" {
                background #e6550d
                color #ffffff
            }
            element "Person" {
                shape Person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #6baed6
            }
        }
    }
}
