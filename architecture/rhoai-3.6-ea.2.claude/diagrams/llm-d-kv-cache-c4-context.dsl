workspace {
    model {
        router = person "llm-d-router" "Prefix-aware request router that selects inference pods based on cache affinity"

        kvCache = softwareSystem "llm-d-kv-cache" "KV cache management toolkit for the llm-d distributed LLM inference platform" {
            eventProcessor = container "Event Processor" "Subscribes to vLLM cache events via ZeroMQ, processes and indexes cache block metadata" "Go Service"
            blockIndexer = container "Block Indexer" "Pluggable storage backends (Redis, Valkey, in-memory Ristretto) for KV cache block indexing" "Go Library"
            scoringAPI = container "Scoring API" "HTTP endpoints for pod cache affinity scoring" "Go HTTP Service"
            indexerService = container "IndexerService" "gRPC service for programmatic cache lookups" "Go gRPC Service"
            podReconciler = container "Pod Reconciler" "Watches Pod lifecycle events to track available cache sources" "Go controller-runtime"
            metricsServer = container "Metrics Server" "Prometheus metrics endpoint" "Go HTTP Service"
            tokenizer = container "External Tokenizer" "Optional sidecar for tokenization over Unix domain socket" "Python gRPC Service"
        }

        vllm = softwareSystem "vLLM Inference Engines" "LLM inference engines publishing KV cache events" "External"
        redis = softwareSystem "Redis / Valkey" "In-memory data store for KV cache block index" "External"
        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for pod lifecycle management" "External"
        otel = softwareSystem "OpenTelemetry Collector" "Distributed tracing backend" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and alerting" "External"

        vllm -> kvCache "Publishes KV cache events" "ZMQ pub/sub 5557/TCP"
        router -> kvCache "Queries pod cache affinity scores" "HTTP POST 8080/TCP"
        kvCache -> redis "Reads/writes cache block index" "Redis protocol 6379/TCP"
        kvCache -> k8sAPI "Watches Pod resources" "HTTPS 6443/TCP"
        kvCache -> otel "Exports distributed traces" "OTLP/gRPC"
        prometheus -> kvCache "Scrapes metrics" "HTTP GET /metrics 8080/TCP"

        eventProcessor -> blockIndexer "Indexes processed events"
        blockIndexer -> redis "Stores/retrieves cache blocks" "Redis protocol"
        scoringAPI -> blockIndexer "Reads cache index for scoring"
        indexerService -> blockIndexer "Reads cache index for lookups"
        scoringAPI -> tokenizer "Tokenization requests" "gRPC over UDS"
        podReconciler -> k8sAPI "Watch /v1/Pod" "HTTPS 6443/TCP ServiceAccount"
        eventProcessor -> otel "Export traces" "OTLP/gRPC"
    }

    views {
        systemContext kvCache "SystemContext" {
            include *
            autoLayout
        }

        container kvCache "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Person" {
                background #f5a623
                color #ffffff
                shape Person
            }
        }
    }
}
