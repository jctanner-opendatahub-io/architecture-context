workspace {
    model {
        user = person "ML Application Client" "Sends LLM inference requests through the serving stack"

        payloadProcessor = softwareSystem "llm-d-inference-payload-processor" "Envoy ExtProc service that intercepts and transforms LLM inference requests with pluggable pre/post-processing pipeline" {
            extProcServer = container "ExtProc gRPC Server" "Receives per-request processing callouts from Envoy, applies plugin pipeline" "Go gRPC Service, port 9004"
            pluginPipeline = container "Plugin Pipeline" "Configurable chain of pre-processors, profile picker, and post-processors" "Go Plugin Framework"
            configMapReconciler = container "ConfigMap Reconciler" "Watches ConfigMaps for base-model-to-header resolution, updates in-memory model mapping" "controller-runtime Reconciler"
            healthServer = container "Health gRPC Server" "Provides liveness and readiness probes" "Go gRPC Service, port 9005"
            metricsServer = container "Metrics HTTP Server" "Exposes Prometheus metrics with optional K8s TokenReview auth" "controller-runtime Metrics, port 9090"
        }

        envoyProxy = softwareSystem "Envoy Proxy" "L7 proxy routing inference traffic, issues ExtProc callouts" "External"
        llmdRouter = softwareSystem "llm-d-router" "Shared plugin type library for the llm-d serving stack" "Internal llm-d"
        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource operations and ConfigMap watches" "External"
        vllmDeepseek = softwareSystem "vLLM DeepSeek R1" "Model inference server for DeepSeek R1" "External"
        vllmLlama = softwareSystem "vLLM Llama 3 8B" "Model inference server for Llama 3 8B Instruct" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"

        user -> envoyProxy "Sends inference requests" "HTTP/8081"
        envoyProxy -> payloadProcessor "gRPC ExtProc callouts per request" "gRPC/9004, self-signed TLS"
        envoyProxy -> vllmDeepseek "Forwards inference requests" "HTTP/8000"
        envoyProxy -> vllmLlama "Forwards inference requests" "HTTP/8000"
        payloadProcessor -> kubernetesAPI "Watches ConfigMaps, resource operations" "HTTPS/6443"
        payloadProcessor -> llmdRouter "Imports shared plugin types" "Go library dependency"
        prometheus -> payloadProcessor "Scrapes metrics" "HTTP/9090"

        extProcServer -> pluginPipeline "Delegates request/response processing"
        configMapReconciler -> pluginPipeline "Updates model resolution table"
        configMapReconciler -> kubernetesAPI "Watches ConfigMaps" "HTTPS/6443"
    }

    views {
        systemContext payloadProcessor "SystemContext" {
            include *
            autoLayout
        }

        container payloadProcessor "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal llm-d" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
