workspace {
    model {
        datascientist = person "Data Scientist" "Runs ML pipelines that generate metadata"
        pipelinedev = person "Pipeline Developer" "Builds and configures ML pipelines"

        mlmetadata = softwareSystem "ML Metadata (MLMD)" "gRPC metadata store server that records and retrieves metadata associated with ML workflows" {
            server = container "metadata_store_server" "C++ binary exposing MetadataStoreService gRPC API on port 8080/TCP" "C++ / Bazel / gRPC"
            pythonClient = container "ml_metadata Python SDK" "Python client library for programmatic access to the metadata store" "Python"
        }

        dsp = softwareSystem "Data Science Pipelines" "Orchestrates ML pipeline workflows" "Internal RHOAI"
        mysql = softwareSystem "MySQL / MariaDB" "Relational database for persistent metadata storage" "External"
        postgresql = softwareSystem "PostgreSQL" "Alternative relational database backend" "External"
        kubeapi = softwareSystem "Kubernetes API" "Cluster orchestration and pod management" "External"

        # Relationships
        datascientist -> dsp "Submits pipeline runs"
        pipelinedev -> dsp "Configures pipelines"

        dsp -> mlmetadata "Records artifacts, executions, contexts, and events via gRPC" "gRPC/8080"
        mlmetadata -> mysql "Persists metadata" "MySQL protocol/3306, Optional SSL"
        mlmetadata -> postgresql "Persists metadata" "PostgreSQL protocol/5432, Optional SSL"

        pythonClient -> server "gRPC API calls" "gRPC/8080"
    }

    views {
        systemContext mlmetadata "SystemContext" {
            include *
            autoLayout
        }

        container mlmetadata "Containers" {
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
