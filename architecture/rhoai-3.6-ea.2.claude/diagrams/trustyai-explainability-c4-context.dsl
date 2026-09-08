workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and deploys ML models, monitors fairness and drift"
        platformAdmin = person "Platform Admin" "Manages OpenShift AI platform and monitoring"

        trustyai = softwareSystem "TrustyAI Explainability" "Quarkus-based service providing AI model fairness monitoring, data drift detection, and metric export for models served via KServe/ModelMesh" {
            initContainer = container "Init Container" "Registers TrustyAI consumer endpoint with KServe by creating model-serving-config ConfigMap" "Shell Script"
            service = container "TrustyAI Service" "Quarkus 3.8 native application serving fairness/drift metrics and consuming inference payloads" "Java/Quarkus Native" {
                consumerEndpoint = component "ConsumerEndpoint" "Receives inference payloads via /consumer/kserve/v2" "JAX-RS Endpoint"
                payloadReconciler = component "PayloadReconciler" "Joins input-output pairs into structured dataframes" "Internal Service"
                fairnessMetrics = component "Fairness Metrics" "Computes SPD, DIR metrics" "Metric Endpoint"
                driftMetrics = component "Drift Metrics" "Computes Meanshift, KS Test, Fourier MMD" "Metric Endpoint"
                prometheusScheduler = component "PrometheusScheduler" "Periodically computes and exports metrics" "Scheduled Task"
                prometheusExport = component "Prometheus Export" "Exposes metrics at /q/metrics" "Metrics Endpoint"
            }
            pvcStorage = container "PVC Storage" "Flat file storage for inference data at /inputs" "PersistentVolumeClaim" "Storage"
        }

        kserveModelMesh = softwareSystem "KServe/ModelMesh" "Serves ML models and routes inference payloads to registered processors" "Internal Platform"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring platform" "Internal Platform"
        mariadb = softwareSystem "MariaDB" "Optional relational storage backend for inference data" "External (Optional)"
        kubernetes = softwareSystem "Kubernetes API" "Cluster API server for ConfigMap management" "Infrastructure"
        openshiftRoute = softwareSystem "OpenShift Router" "Exposes services externally via Routes" "Infrastructure"

        # Relationships
        dataScientist -> trustyai "Requests fairness/drift metrics, uploads data" "HTTP/8080"
        platformAdmin -> prometheus "Monitors TrustyAI metrics" "HTTP"

        kserveModelMesh -> trustyai "Sends inference payloads" "HTTP/8080 POST /consumer/kserve/v2"
        trustyai -> prometheus "Exports metrics" "HTTP/8080 GET /q/metrics"
        trustyai -> mariadb "Stores inference data (optional)" "JDBC"
        trustyai -> kubernetes "Creates model-serving-config ConfigMap" "HTTPS/443"
        openshiftRoute -> trustyai "Routes external traffic" "HTTP 80→8080"

        # Internal relationships
        initContainer -> kubernetes "Creates ConfigMap" "HTTPS/443 SA Token"
        consumerEndpoint -> payloadReconciler "Forwards payloads"
        payloadReconciler -> pvcStorage "Stores reconciled data"
        prometheusScheduler -> pvcStorage "Reads inference data"
        prometheusScheduler -> fairnessMetrics "Computes SPD, DIR"
        prometheusScheduler -> driftMetrics "Computes Meanshift"
        prometheusScheduler -> prometheusExport "Exports computed metrics"
    }

    views {
        systemContext trustyai "SystemContext" {
            include *
            autoLayout
            description "TrustyAI Explainability in the RHOAI ecosystem"
        }

        container trustyai "Containers" {
            include *
            autoLayout
            description "Internal structure of TrustyAI Explainability"
        }

        component service "Components" {
            include *
            autoLayout
            description "Internal components of the TrustyAI Service"
        }

        styles {
            element "Internal Platform" {
                background #7ed321
                color #ffffff
            }
            element "External (Optional)" {
                background #999999
                color #ffffff
            }
            element "Infrastructure" {
                background #4a90e2
                color #ffffff
            }
            element "Storage" {
                background #f5a623
                color #ffffff
                shape Cylinder
            }
            element "Software System" {
                background #1168bd
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
            element "Component" {
                background #85bbf0
                color #000000
            }
        }
    }
}
