workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and runs ML pipelines using Data Science Pipelines"

        dspOperator = softwareSystem "Data Science Pipelines Operator" "Kubernetes operator managing lifecycle of DSP deployments on RHOAI" {
            controller = container "DSPAReconciler" "Watches DSPA CRs, renders templates via manifestival, reconciles full pipeline stack" "Go controller-runtime"
            webhook = container "Webhook Server" "Validates PipelineVersion resources; TLS via OpenShift TLS profile" "Go :9443"
            tlsWatcher = container "SecurityProfileWatcher" "Monitors OpenShift TLS profile changes, triggers graceful restarts" "Go"
        }

        dspStack = softwareSystem "DSP Service Stack" "Per-DSPA deployment of pipeline services" {
            apiServer = container "DS Pipeline API Server" "REST (8888) and gRPC (8887) API for pipeline operations" "Python/Go :8888/:8887"
            oauthProxy = container "OAuth Proxy" "TLS termination and OpenShift OAuth authentication" "oauth-proxy :8443"
            argoController = container "Argo Workflow Controller" "Executes ML pipeline workflows as Argo Workflows" "Go :9090 metrics"
            mariadb = container "MariaDB" "Pipeline metadata storage (optional, can use external DB)" "MariaDB :3306"
            minio = container "MinIO" "Pipeline artifact storage (optional, can use external S3)" "MinIO :9000"
        }

        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "Infrastructure"
        openshiftAPI = softwareSystem "OpenShift APIServer" "Provides cluster-wide TLS security profile" "Infrastructure"
        mlflow = softwareSystem "MLflow" "ML experiment tracking platform" "Internal RHOAI"
        kserve = softwareSystem "KServe" "Model serving platform for inference services" "Internal RHOAI"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebooks" "Notebook workbench management" "Internal RHOAI"
        prometheusOperator = softwareSystem "Prometheus Operator" "Monitoring stack for metrics collection" "Infrastructure"

        # User interactions
        dataScientist -> oauthProxy "Creates/runs pipelines via" "HTTPS/8443 OAuth"
        dataScientist -> k8sAPI "Creates DSPA CRs via kubectl" "HTTPS/6443"

        # Operator interactions
        controller -> k8sAPI "Watches DSPA CRs, applies manifests" "HTTPS/6443 SA token"
        controller -> openshiftAPI "Reads TLS security profile" "HTTPS/6443"
        controller -> mlflow "Reads MLflow instances (direct API)" "HTTPS"
        controller -> kserve "Watches InferenceService state" "HTTPS"
        controller -> kubeflowNotebooks "Manages notebook CRDs" "HTTPS"
        controller -> prometheusOperator "Manages ServiceMonitors" "HTTPS"
        k8sAPI -> webhook "Invokes for PipelineVersion validation" "HTTPS/9443"

        # DSP Stack interactions
        oauthProxy -> apiServer "Forwards authenticated requests" "HTTP/8888"
        apiServer -> mariadb "Stores pipeline metadata" "MySQL/3306"
        apiServer -> minio "Stores pipeline artifacts" "HTTP/9000"
        apiServer -> argoController "Submits workflows" "Kubernetes API"
        argoController -> k8sAPI "Creates/manages workflow pods" "HTTPS/6443"
    }

    views {
        systemContext dspOperator "SystemContext" {
            include *
            autoLayout
        }

        container dspOperator "OperatorContainers" {
            include *
            autoLayout
        }

        container dspStack "DSPStackContainers" {
            include *
            autoLayout
        }

        styles {
            element "Infrastructure" {
                background #999999
                color #ffffff
            }
            element "Internal RHOAI" {
                background #7ed321
                color #000000
            }
            element "Person" {
                shape Person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "Container" {
                background #85bbf0
                color #000000
            }
        }
    }
}
