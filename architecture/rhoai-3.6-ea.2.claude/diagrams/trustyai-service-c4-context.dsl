workspace {
    model {
        dataScientist = person "Data Scientist" "Queries fairness, drift, and explainability metrics for deployed ML models"
        mlEngineer = person "ML Engineer" "Deploys models and configures monitoring"
        securityAuditor = person "Security Auditor" "Reviews model fairness and bias compliance"

        trustyaiService = softwareSystem "TrustyAI Service" "AI observability service providing fairness, drift detection, and explainability metrics for ML models" {
            kubeRbacProxy = container "kube-rbac-proxy" "Authenticates requests via Kubernetes RBAC and forwards to main API" "Go sidecar" "Sidecar"
            mainApi = container "Main FastAPI App" "Serves fairness, drift, explainability, and metadata endpoints" "Python FastAPI + Hypercorn" {
                fairnessEndpoints = component "Fairness Endpoints" "SPD, DIR metrics computation and scheduling" "FastAPI Router"
                driftEndpoints = component "Drift Endpoints" "KS test, Jensen-Shannon, MMD, CompareMeans, streaming drift detection" "FastAPI Router"
                explainerEndpoints = component "Explainer Endpoints" "LIME, SHAP, PDP, counterfactual explanations" "FastAPI Router"
                metadataEndpoints = component "Metadata Endpoints" "Model info and service metadata" "FastAPI Router"
                metricsScheduler = component "Metrics Scheduler" "Background asyncio task computing scheduled metrics at configurable interval" "asyncio"
            }
            healthApp = container "Health/Consumer FastAPI App" "Receives inference data from KServe/ModelMesh, serves health probes and Prometheus metrics" "Python FastAPI + Hypercorn"
            httpsListener = container "HTTPS Listener" "Optional TLS endpoint using PolicyAwareConfig for FIPS-compatible crypto" "Hypercorn PolicyAwareConfig" "Optional"
            storageInterface = container "GlobalStorageInterface" "Singleton storage abstraction supporting PVC (HDF5) and MariaDB backends" "Python"
        }

        kubeRbacProxy -> mainApi "Forwards authenticated requests" "HTTP/8081 loopback"
        mainApi -> storageInterface "Reads/writes inference data and metrics" "Python API"
        healthApp -> storageInterface "Writes ingested inference data" "Python API"
        metricsScheduler -> storageInterface "Reads scheduled metric requests" "Python API"

        kserve = softwareSystem "KServe" "ML model serving platform with inference logging" "External"
        modelMesh = softwareSystem "ModelMesh" "Multi-model serving with inference payload forwarding" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and alerting" "External"
        mariadb = softwareSystem "MariaDB" "Relational database for optional persistent storage" "External"
        pvc = softwareSystem "PVC Storage" "Kubernetes Persistent Volume Claim for HDF5 file storage" "Infrastructure"
        kubelet = softwareSystem "Kubelet" "Kubernetes node agent for health probes" "Infrastructure"

        dataScientist -> kubeRbacProxy "Queries fairness/drift/explainability APIs" "HTTPS/8443"
        mlEngineer -> kubeRbacProxy "Configures metric schedules and model metadata" "HTTPS/8443"
        securityAuditor -> kubeRbacProxy "Reviews fairness compliance metrics" "HTTPS/8443"

        kserve -> healthApp "Sends inference CloudEvents" "HTTP/8080 POST /"
        modelMesh -> healthApp "Sends KServe v2 inference payloads" "HTTP/8080 POST /consumer/kserve/v2"
        prometheus -> healthApp "Scrapes pre-computed metrics" "HTTP/8080 GET /q/metrics"
        kubelet -> healthApp "Health probes" "HTTP/8080 GET /health"

        storageInterface -> pvc "Reads/writes HDF5 files" "Filesystem"
        storageInterface -> mariadb "SQL queries with optional TLS" "MySQL/3306"
    }

    views {
        systemContext trustyaiService "SystemContext" {
            include *
            autoLayout
        }

        container trustyaiService "Containers" {
            include *
            autoLayout
        }

        component mainApi "MainApiComponents" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Infrastructure" {
                background #d6b656
                color #333333
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
            element "Sidecar" {
                background #f5a623
                color #333333
            }
            element "Optional" {
                background #b8d4e3
                color #333333
                border dashed
            }
            element "Component" {
                background #85bbf0
                color #333333
            }
        }
    }
}
