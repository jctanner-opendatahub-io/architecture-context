workspace {
    model {
        producer = person "Upstream Service" "Publishes inference requests to message queues"
        sre = person "SRE / Platform Admin" "Monitors health and metrics"

        llmDAsync = softwareSystem "llm-d-async" "Asynchronous inference processor that bridges message queues with model servers" {
            runner = container "Runner" "Main processing loop: transport subscription, merge policy, worker dispatch" "Go (controller-runtime)"
            transportLayer = container "Transport Layer" "Pluggable message queue abstraction (Redis Pub/Sub, Redis Sorted Set, GCP Pub/Sub)" "Go (pipeline.Flow)"
            healthServer = container "Health Server" "Liveness and readiness probes" "Go HTTP :8081"
            metricsServer = container "Metrics Server" "Prometheus metrics with K8s bearer token auth" "Go HTTP :9090"
            httpClient = container "HTTP Client" "OTel-instrumented HTTP client with optional mTLS" "Go net/http"
            flowGate = container "Flow-Control Gate" "Prometheus metric-based dispatch throttling" "Go"
        }

        redis = softwareSystem "Redis" "Message queue transport (Pub/Sub and Sorted Set modes)" "External"
        gcpPubSub = softwareSystem "Google Cloud Pub/Sub" "Alternative message queue transport" "External"
        inferenceGW = softwareSystem "Inference Gateway" "Downstream model server for inference requests" "Internal"
        prometheus = softwareSystem "Prometheus" "Metrics collection and flow-control metric source" "External"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource ops and auth delegation" "External"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed trace aggregation" "External"
        gatewayAPIExt = softwareSystem "gateway-api-inference-extension" "Flow-control primitives library" "Internal ODH"

        # Relationships
        producer -> redis "Publishes inference requests" "Redis RESP/6379"
        producer -> gcpPubSub "Publishes inference requests" "gRPC/443 TLS"

        llmDAsync -> redis "Subscribes to request queues, publishes results" "TCP/6379"
        llmDAsync -> gcpPubSub "Subscribes to request queues, publishes results" "gRPC/443 TLS"
        llmDAsync -> inferenceGW "Forwards inference requests" "HTTP(S) optional mTLS"
        llmDAsync -> prometheus "Queries metrics for flow-control gates" "HTTP/9090"
        llmDAsync -> k8sAPI "Resource operations, metrics auth delegation" "HTTPS/6443"
        llmDAsync -> otelCollector "Exports distributed traces" "gRPC OTLP/4317"

        sre -> llmDAsync "Scrapes metrics" "HTTP/9090 Bearer token"
        sre -> llmDAsync "Checks health probes" "HTTP/8081"

        # Internal container relationships
        runner -> transportLayer "Creates and manages"
        transportLayer -> redis "Subscribes/publishes"
        transportLayer -> gcpPubSub "Subscribes/publishes"
        runner -> httpClient "Dispatches inference requests"
        runner -> flowGate "Checks dispatch conditions"
        flowGate -> prometheus "Queries metrics"
        httpClient -> inferenceGW "POST inference requests"
        runner -> healthServer "Starts"
        runner -> metricsServer "Starts"
        metricsServer -> k8sAPI "Delegates bearer token validation"
    }

    views {
        systemContext llmDAsync "SystemContext" {
            include *
            autoLayout
        }

        container llmDAsync "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal" {
                background #7ed321
                color #ffffff
            }
            element "Internal ODH" {
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
            element "Person" {
                background #08427b
                color #ffffff
            }
        }
    }
}
