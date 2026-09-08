workspace {
    model {
        user = person "Data Scientist / ML Engineer" "Sends inference requests to deployed LLM models"

        llmd = softwareSystem "llm-d" "Disaggregated LLM inference serving framework with vllm backend, Envoy routing, and optional RDMA KV-cache transfer" {
            envoyProxy = container "Envoy Sidecar Proxy" "Accepts client traffic and delegates routing decisions to EPP via ext_proc" "Envoy" "8081/TCP"
            epp = container "Endpoint Picker Plugin (EPP)" "Evaluates InferencePool membership and model server load to select optimal backend" "gRPC Service" "9002/TCP"
            decodeDeployment = container "Decode Deployment" "vllm OpenAI-compatible API server for decode-phase inference" "Python vllm" "8000/TCP"
            prefillDeployment = container "Prefill Deployment" "vllm server for prefill-phase computation with nixl RDMA KV-cache export" "Python vllm" "8000/TCP, 5600/TCP"
            routingSidecar = container "Routing Sidecar" "Coordinates KV-cache handoff between prefill and decode pods" "vllm sidecar" "--kv-connector=nixlv2"
        }

        vllm = softwareSystem "vllm" "Python inference engine - model serving backend" "Runtime Dependency"
        llmdRouter = softwareSystem "llm-d-router" "Envoy proxy + EPP for intelligent model server selection" "Internal"
        gatewayAPI = softwareSystem "Gateway API (InferencePool)" "Defines model server pool for EPP routing decisions" "Kubernetes CRD"
        istio = softwareSystem "Istio Service Mesh" "Optional mTLS and authorization policies" "External (Optional)"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Receives OTLP traces from model servers and EPP" "Observability"
        jaeger = softwareSystem "Jaeger" "Distributed trace storage and visualization" "Observability"
        prometheus = softwareSystem "Prometheus" "Metrics scraping via PodMonitor" "Observability"

        user -> llmd "Sends inference requests via HTTP"
        user -> envoyProxy "POST /v1/completions, /v1/chat/completions" "HTTP/8081"
        envoyProxy -> epp "ext_proc routing decisions" "gRPC/9002"
        epp -> gatewayAPI "Reads InferencePool membership"
        envoyProxy -> decodeDeployment "Forwards requests via ORIGINAL_DST" "HTTP/8000"
        envoyProxy -> prefillDeployment "Forwards requests via ORIGINAL_DST" "HTTP/8000"
        prefillDeployment -> routingSidecar "KV-cache transfer" "RDMA/5600 (nixl)"
        routingSidecar -> decodeDeployment "KV-cache handoff" "HTTP/8000"
        llmd -> vllm "Uses as inference backend"
        llmd -> llmdRouter "Uses for request routing"
        decodeDeployment -> otelCollector "OTLP trace export" "gRPC/4317"
        prefillDeployment -> otelCollector "OTLP trace export" "gRPC/4317"
        epp -> otelCollector "OTLP trace export" "gRPC/4317"
        otelCollector -> jaeger "Forward traces" "gRPC/4317"
        prometheus -> decodeDeployment "Scrape metrics" "PodMonitor"
        prometheus -> prefillDeployment "Scrape metrics" "PodMonitor"
        istio -> llmd "Optional mTLS enforcement"
    }

    views {
        systemContext llmd "SystemContext" {
            include *
            autoLayout
        }

        container llmd "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "External (Optional)" {
                background #bbbbbb
                color #ffffff
            }
            element "Internal" {
                background #7ed321
                color #ffffff
            }
            element "Runtime Dependency" {
                background #4a90e2
                color #ffffff
            }
            element "Observability" {
                background #f5a623
                color #ffffff
            }
            element "Kubernetes CRD" {
                background #e8544e
                color #ffffff
            }
        }
    }
}
