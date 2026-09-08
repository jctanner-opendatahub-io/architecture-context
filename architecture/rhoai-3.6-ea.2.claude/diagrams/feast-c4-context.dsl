workspace {
    model {
        dataScientist = person "Data Scientist" "Creates feature definitions, deploys feature stores, and retrieves features for ML models"
        mlEngineer = person "ML Engineer" "Integrates feature retrieval into ML training and serving pipelines"

        feast = softwareSystem "Feast" "Feature store platform for managing, serving, and discovering ML features" {
            operator = container "Feast Operator" "Reconciles FeatureStore CRs, manages lifecycle of feature store workloads" "Go controller-runtime Operator"
            pythonServer = container "Python Feature Server" "Serves online features via REST API with configurable authentication" "Python FastAPI :6566/TCP"
            goServer = container "Go Feature Server" "Low-latency online feature retrieval via HTTP and gRPC" "Go HTTP/gRPC Server"
            registryServer = container "Registry Server" "CRUD API for feature store metadata (entities, views, services, permissions)" "Python gRPC + REST"
            webhookServer = container "Webhook Server" "Validates and mutates FeatureStore CRs" "Go Admission Webhook"
            notebookReconciler = container "NotebookConfigMap Reconciler" "Injects feature store connection ConfigMaps into notebook namespaces" "Go Controller"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster resource management and RBAC enforcement" "Platform"
        prometheus = softwareSystem "Prometheus" "Metrics collection and alerting via ServiceMonitor CRDs" "Platform"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebooks" "Interactive notebook workbenches for data scientists" "Internal RHOAI"
        mlflow = softwareSystem "MLflow" "Experiment tracking and model registry" "Internal RHOAI"
        sparkOperator = softwareSystem "Spark Operator" "Manages SparkApplication CRs for batch materialization" "Internal RHOAI"
        openshiftRoutes = softwareSystem "OpenShift Routes" "External route exposure for UI dashboards" "Platform"

        postgresql = softwareSystem "PostgreSQL" "Online store backend for feature vectors" "External"
        redis = softwareSystem "Redis / Valkey" "Online store backend for low-latency feature retrieval" "External"
        s3 = softwareSystem "S3-compatible Storage" "Registry backend and model artifact storage" "External"
        gcs = softwareSystem "Google Cloud Storage" "Registry backend and object storage" "External"

        # Relationships - Users
        dataScientist -> feast "Creates FeatureStore CR, queries features via REST/gRPC"
        mlEngineer -> feast "Retrieves online features for model serving"

        # Relationships - Operator
        operator -> kubernetesAPI "Watches FeatureStore CRs, manages child resources" "HTTPS/6443 SA token"
        operator -> prometheus "Creates ServiceMonitor resources" "Kubernetes API"
        operator -> openshiftRoutes "Creates Routes for UI dashboards" "Kubernetes API"
        operator -> sparkOperator "Creates SparkApplication CRs for batch jobs" "Kubernetes API"
        notebookReconciler -> kubeflowNotebooks "Watches Notebook CRs for ConfigMap injection" "Kubernetes API"
        notebookReconciler -> kubernetesAPI "Injects ConfigMaps into notebook namespaces" "HTTPS/6443"
        operator -> mlflow "Watches MLflow CRs for integration" "Kubernetes API"

        # Relationships - Feature Serving
        pythonServer -> postgresql "Reads/writes feature vectors" "TCP/5432"
        pythonServer -> redis "Reads/writes feature vectors" "TCP/6379"
        goServer -> postgresql "Reads feature vectors" "TCP/5432"
        goServer -> redis "Reads feature vectors" "TCP/6379"

        # Relationships - Registry
        registryServer -> s3 "Persists registry metadata" "HTTPS/443"
        registryServer -> gcs "Persists registry metadata" "HTTPS/443"
    }

    views {
        systemContext feast "SystemContext" {
            include *
            autoLayout
        }

        container feast "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Platform" {
                background #6c8ebf
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
        }
    }
}
