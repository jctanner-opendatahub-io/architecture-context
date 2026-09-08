workspace {
    model {
        dataScientist = person "Data Scientist" "Sends inference requests, manages models and agents"
        appDeveloper = person "Application Developer" "Integrates AI capabilities via OpenAI/Anthropic-compatible APIs"

        ogxDistribution = softwareSystem "OGX Distribution" "Containerized AI agent server exposing OpenAI-compatible and Anthropic Messages APIs for inference, RAG, and agent orchestration" {
            entrypoint = container "Entrypoint Script" "Resolves _FILE secrets from K8s mounts, configures environment, starts server" "Bash"
            ogxServer = container "OGX Server" "Provider-pluggable AI server runtime with OAuth2 auth" "Python (OGX Framework)"
            inferenceAPI = container "Inference API" "OpenAI-compatible /v1/chat/completions endpoint" "HTTP/8321"
            responsesAPI = container "Responses API" "Agent orchestration via /v1/responses" "HTTP/8321"
            messagesAPI = container "Messages API" "Anthropic Messages passthrough via /v1/messages" "HTTP/8321"
            vectorIOProvider = container "Vector IO Provider" "RAG retrieval from vector databases" "Python Plugin"
            metricsEndpoint = container "Metrics Endpoint" "Prometheus metrics on /metrics" "HTTP"
        }

        vllm = softwareSystem "vLLM" "High-performance inference backend for chat completions and embeddings" "Internal RHOAI"
        postgresql = softwareSystem "PostgreSQL" "Relational database for KV store, SQL store, conversations, batches, files metadata" "Internal"
        ogxOperator = softwareSystem "OGX Operator" "Kubernetes operator managing OGX server deployment lifecycle" "Internal RHOAI"
        milvus = softwareSystem "Milvus" "Vector database for RAG retrieval" "Optional"
        pgvector = softwareSystem "PGVector" "PostgreSQL vector extension for RAG" "Optional"
        qdrant = softwareSystem "Qdrant" "Vector database for RAG retrieval" "Optional"
        idp = softwareSystem "OAuth2 Identity Provider" "JWKS-based JWT token validation" "External"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing and metrics collection" "External"
        prometheus = softwareSystem "Prometheus" "Metrics scraping and alerting" "Internal"

        dataScientist -> ogxDistribution "Sends inference/agent requests via HTTP"
        appDeveloper -> ogxDistribution "Integrates via OpenAI/Anthropic APIs"

        ogxDistribution -> vllm "Proxies inference requests" "HTTP/HTTPS"
        ogxDistribution -> postgresql "Stores state (KV, SQL, metadata)" "PostgreSQL/5432"
        ogxDistribution -> milvus "Queries vectors for RAG" "HTTP/gRPC, mTLS"
        ogxDistribution -> pgvector "Queries vectors for RAG" "PostgreSQL/5432"
        ogxDistribution -> qdrant "Queries vectors for RAG" "HTTP/6333, gRPC/6334"
        ogxDistribution -> idp "Validates JWT tokens via JWKS" "HTTPS/443"
        ogxDistribution -> otelCollector "Exports traces and metrics" "OTLP"
        ogxOperator -> ogxDistribution "Manages deployment lifecycle"
        prometheus -> ogxDistribution "Scrapes /metrics endpoint" "HTTP"
    }

    views {
        systemContext ogxDistribution "SystemContext" {
            include *
            autoLayout
        }

        container ogxDistribution "Containers" {
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
                color #ffffff
            }
            element "Internal" {
                background #4a90e2
                color #ffffff
            }
            element "Optional" {
                background #e1d5e7
                color #333333
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
        }
    }
}
