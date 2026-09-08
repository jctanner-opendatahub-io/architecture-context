workspace {
    model {
        user = person "Data Scientist / API Client" "Submits batch inference jobs and manages input/output files"

        batchGateway = softwareSystem "batch-gateway" "Asynchronous batch inference gateway for RHOAI that accepts batch requests, manages files, and orchestrates job processing" {
            apiserver = container "batch-gateway-apiserver" "Accepts batch and file management requests over HTTP, applies middleware chain, persists to PostgreSQL, enqueues via Redis" "Go HTTP Service" {
                tags "FIPS"
            }
            processor = container "batch-gateway-processor" "Dequeues pending jobs from Redis, retrieves input files, forwards inference requests to llm-d, writes results" "Go Background Worker" {
                tags "FIPS"
            }
            gc = container "batch-gateway-gc" "Periodically scans for expired jobs and files, removes from database and file store" "Go Background Worker" {
                tags "FIPS"
            }
        }

        platformGateway = softwareSystem "llm-d Inference Gateway" "Platform gateway providing external auth enforcement and TLS termination via HTTPRoute" "External"
        postgresql = softwareSystem "PostgreSQL" "Relational database for job metadata and status tracking" "External"
        redis = softwareSystem "Redis/Valkey" "Message exchange for job coordination via llm-d-async" "External"
        s3 = softwareSystem "S3-compatible Storage" "Object storage for batch input/output files" "External"
        llmdInference = softwareSystem "llm-d Inference Endpoint" "Downstream inference service for model predictions" "Internal RHOAI"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing aggregation" "External"

        # External relationships
        user -> platformGateway "Submits batch jobs and uploads files" "HTTPS/443"
        platformGateway -> batchGateway "Forwards authenticated requests" "HTTP(S)/8000"

        # Internal container relationships
        user -> apiserver "Creates batch jobs and uploads files" "HTTP(S)/8000"
        apiserver -> postgresql "Persists job metadata and file records" "TCP"
        apiserver -> redis "Enqueues jobs via llm-d-async producer" "TCP"
        apiserver -> s3 "Stores input/output files" "HTTP/HTTPS"

        processor -> redis "Polls for pending jobs" "TCP"
        processor -> postgresql "Updates job status" "TCP"
        processor -> s3 "Reads input files, writes output files" "HTTP/HTTPS"
        processor -> llmdInference "Forwards inference requests with auth passthrough" "HTTP/HTTPS"

        gc -> postgresql "Scans for expired records" "TCP"
        gc -> s3 "Deletes expired files" "HTTP/HTTPS"

        apiserver -> otelCollector "Exports traces" "OTLP/gRPC"
        processor -> otelCollector "Exports traces" "OTLP/gRPC"
        gc -> otelCollector "Exports traces" "OTLP/gRPC"
    }

    views {
        systemContext batchGateway "SystemContext" {
            include *
            autoLayout
        }

        container batchGateway "Containers" {
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
            element "Internal RHOAI" {
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
            element "FIPS" {
                background #4a90e2
                color #ffffff
                border solid
            }
        }
    }
}
