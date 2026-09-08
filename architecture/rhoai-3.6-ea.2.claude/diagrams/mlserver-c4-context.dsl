workspace {
    model {
        dataScientist = person "Data Scientist" "Creates, deploys, and queries ML models via InferenceService"

        mlserver = softwareSystem "MLServer" "Python-based inference server implementing KServe V2 Inference Protocol with REST and gRPC interfaces for multi-framework model serving" {
            restServer = container "REST Server" "FastAPI/uvicorn HTTP server implementing V2 Inference Protocol endpoints" "Python FastAPI" "Web Server"
            grpcServer = container "gRPC Server" "grpc.aio server implementing GRPCInferenceService and ModelRepositoryService" "Python gRPC" "gRPC Server"
            dataPlane = container "DataPlane Handler" "Common handler abstracting inference, model lifecycle, and health operations" "Python" "Handler"
            metricsServer = container "Metrics Server" "Prometheus metrics export endpoint" "Python starlette-exporter" "Metrics"
            runtimePlugins = container "Runtime Plugins" "Framework-specific model backends: sklearn, xgboost, lightgbm, onnx, mlflow, huggingface, catboost, mllib, alibi-detect, alibi-explain" "Python packages" "Plugins"
            trustedRuntimes = container "Trusted Runtimes Allowlist" "Security boundary restricting loadable model runtimes via /etc/mlserver/trusted-runtimes.json" "JSON config" "Security"
        }

        kubeRbacProxy = softwareSystem "kube-rbac-proxy" "Sidecar container providing OpenShift OAuth/SA token authentication and RBAC authorization" "External"
        kserve = softwareSystem "KServe" "ML model serving platform managing InferenceService lifecycle and pod injection" "Internal RHOAI"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring system" "External"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing collection (optional)" "External"
        modelStorage = softwareSystem "Model Storage" "Model artifact storage at /mnt/models provisioned by KServe storage initializer" "External"

        # Relationships
        dataScientist -> kubeRbacProxy "Sends inference requests via REST/gRPC" "HTTPS (platform-terminated)"
        kubeRbacProxy -> mlserver "Forwards authenticated requests" "HTTP/gRPC (plaintext, pod-internal)"

        restServer -> dataPlane "Delegates request handling"
        grpcServer -> dataPlane "Delegates request handling"
        dataPlane -> trustedRuntimes "Validates runtime against allowlist"
        trustedRuntimes -> runtimePlugins "Loads approved runtimes"
        runtimePlugins -> modelStorage "Loads model artifacts" "Local filesystem I/O"

        prometheus -> metricsServer "Scrapes metrics" "HTTP/8082"
        mlserver -> otelCollector "Exports traces (when configured)" "OTLP gRPC"

        kserve -> mlserver "Deploys as InferenceService container" "Kubernetes Pod spec"
    }

    views {
        systemContext mlserver "SystemContext" {
            include *
            autoLayout
        }

        container mlserver "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #4a90e2
                color #ffffff
                shape RoundedBox
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal RHOAI" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Web Server" {
                shape WebBrowser
            }
            element "Security" {
                background #e74c3c
                color #ffffff
                shape Hexagon
            }
            element "Plugins" {
                background #7ed321
                color #ffffff
            }
        }
    }
}
