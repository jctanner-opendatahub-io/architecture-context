workspace {
    model {
        dataScientist = person "Data Scientist" "Submits evaluation jobs and manages evaluation collections"
        platform = person "Platform Admin" "Configures providers and manages eval-hub deployment"

        evalHub = softwareSystem "eval-hub" "Evaluation orchestration service for RHOAI that manages evaluation job lifecycle, provider configurations, and evaluation collections" {
            apiServer = container "eval-hub API Server" "REST API for evaluation CRUD, job orchestration, and provider management" "Go :8080"
            metricsServer = container "Metrics Server" "Prometheus metrics endpoint" "Go HTTP"
            initContainer = container "eval-runtime-init" "Init container that downloads test data from S3" "Go"
            sidecar = container "eval-runtime-sidecar" "Sidecar proxy managing evaluation lifecycle" "Go"
            mcpServer = container "evalhub-mcp" "MCP server interface" "Go HTTP"
            storageLayer = container "Storage Layer" "Pluggable SQL abstraction over PostgreSQL or SQLite" "Go (pgx/modernc.org)"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API for managing Jobs, ConfigMaps, Secrets, and CRDs" "External"
        mlflow = softwareSystem "MLflow Tracking Server" "Experiment tracking and model registry" "External"
        s3 = softwareSystem "S3-compatible Storage" "Object storage for test data artifacts" "External"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing, metrics, and log collection" "External"
        postgresql = softwareSystem "PostgreSQL" "Relational database for evaluation data persistence" "External"
        hardwareProfileCR = softwareSystem "HardwareProfile CRD" "Custom resource for hardware resource requirements" "Internal RHOAI"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"

        dataScientist -> evalHub "Creates evaluation jobs and collections via REST API"
        platform -> evalHub "Configures evaluation providers"

        apiServer -> storageLayer "Stores/retrieves evaluation data"
        apiServer -> kubernetesAPI "Creates Jobs, ConfigMaps, Secrets; reads HardwareProfiles" "HTTPS/WSS :6443"
        apiServer -> otelCollector "Exports traces, metrics, logs" "OTLP/gRPC"
        apiServer -> mlflow "Reports experiment results" "HTTP/HTTPS"

        initContainer -> s3 "Downloads test data artifacts" "HTTPS"
        sidecar -> mlflow "Reports evaluation results" "HTTP/HTTPS"

        storageLayer -> postgresql "Stores evaluation records" "TCP (pgx)"

        kubernetesAPI -> hardwareProfileCR "Serves HardwareProfile CRs" "infrastructure.opendatahub.io/v1"

        prometheus -> metricsServer "Scrapes /metrics" "HTTP"
    }

    views {
        systemContext evalHub "SystemContext" {
            include *
            autoLayout
        }

        container evalHub "Containers" {
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
                background #438dd5
                color #ffffff
            }
        }
    }
}
