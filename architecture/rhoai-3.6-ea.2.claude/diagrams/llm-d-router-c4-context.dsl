workspace {
    model {
        operator = person "Platform Operator" "Configures EPP scheduling policies via EndpointPickerConfig CRDs"
        client = person "Inference Client" "Sends LLM inference requests through Envoy"

        llmDRouter = softwareSystem "llm-d-router" "Endpoint Picker for llm-d inference serving stack - routes LLM requests via Envoy ExtProc using scheduling plugins, KV-cache awareness, and model rewriting" {
            epp = container "EPP (Endpoint Picker)" "Envoy External Processing gRPC service with plugin-based scheduling framework" "Go gRPC Service" {
                extProc = component "ExternalProcessor" "gRPC ExtProc service receiving Envoy callouts" "gRPC Server"
                healthGrpc = component "Health Service" "gRPC health check endpoint" "gRPC Server"
                metricsServer = component "Metrics Server" "Prometheus metrics with optional mTLS" "HTTP Server"
                pluginFramework = component "Plugin Framework" "Composable scheduling plugins: request control, data production, data layer, parsing" "Go Framework"
                datastore = component "In-Memory Datastore" "Cached endpoint metrics and state" "In-Memory Store"
            }
            controllers = container "Controllers" "Reconcile CRDs and Pod resources into in-memory datastore" "controller-runtime" {
                podReconciler = component "Pod Reconciler" "Watches model server pods" "Controller"
                poolReconciler = component "InferencePool Reconciler" "Watches pool configuration" "Controller"
                objectiveReconciler = component "InferenceObjective Reconciler" "Watches autoscaling objectives" "Controller"
                rewriteReconciler = component "InferenceModelRewrite Reconciler" "Watches model alias mappings" "Controller"
            }
            coordinator = container "Coordinator" "Multi-EPP orchestration with health and metrics endpoints" "Go controller-runtime"
            pdSidecar = container "pd-sidecar" "Per-pod DNS proxy for NIXL-aware KV-cache transfers" "Go controller-runtime"
        }

        envoy = softwareSystem "Envoy Proxy" "L7 proxy with External Processing filter for request interception" "External"
        k8sApi = softwareSystem "Kubernetes API" "Cluster API server for resource operations and watches" "External"
        modelServers = softwareSystem "Model Server Pods" "Backend LLM model serving pods (e.g., vLLM)" "External"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing backend" "External"
        gatewayApiExt = softwareSystem "Gateway API Inference Extension" "InferencePool CRD provider" "Internal Platform"
        llmDKvCache = softwareSystem "llm-d KV Cache" "KV-cache library for cross-pod cache transfers" "Internal Platform"

        client -> envoy "Sends inference requests" "HTTP/HTTPS"
        envoy -> epp "gRPC ExtProc callout" "gRPC/9002, Optional TLS"
        epp -> envoy "Returns routing metadata (selected backend pod)"
        envoy -> modelServers "Forwards request to selected pod"

        controllers -> k8sApi "Watches Pods, InferencePool, InferenceObjective, InferenceModelRewrite" "HTTPS/6443, TLS 1.2+"
        operator -> k8sApi "Creates/updates EndpointPickerConfig CRDs" "kubectl"

        epp -> otelCollector "Exports traces" "OTLP/gRPC 4317 or OTLP/HTTP 4318"
        pdSidecar -> modelServers "DNS/HTTP proxy for NIXL KV-cache transfers"

        epp -> llmDKvCache "Uses KV-cache library" "Go library"
        controllers -> gatewayApiExt "Watches InferencePool resources" "Kubernetes API"
    }

    views {
        systemContext llmDRouter "SystemContext" {
            include *
            autoLayout
        }

        container llmDRouter "Containers" {
            include *
            autoLayout
        }

        component epp "EPPComponents" {
            include *
            autoLayout
        }

        component controllers "ControllerComponents" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal Platform" {
                background #7ed321
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #4a90e2
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
        }
    }
}
