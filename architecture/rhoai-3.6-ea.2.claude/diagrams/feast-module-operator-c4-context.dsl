workspace {
    model {
        platformAdmin = person "Platform Admin" "Manages RHOAI platform components"

        feastModuleOperator = softwareSystem "Feast Module Operator" "Kubernetes operator managing Feast feature store deployments within RHOAI" {
            controller = container "FeastOperator Controller" "Watches FeastOperator CRs and reconciles Feast deployments" "Go, controller-runtime"
            reconciler = container "ODH Reconciler Pipeline" "Standardized action pipeline for manifest rendering, deployment, GC, and status" "opendatahub-operator SDK"
            kustomize = container "Kustomize Renderer" "Renders Kubernetes manifests from kustomize bases" "kustomize"
            metricsServer = container "Metrics Server" "Exposes Prometheus metrics on :8443 with TLS and RBAC auth" "controller-runtime"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "External"
        feastFeatureStore = softwareSystem "Feast FeatureStore" "Feature store instances managed by Feast operator (feast.dev)" "Internal RHOAI"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebooks" "Notebook workbenches (kubeflow.org)" "Internal RHOAI"
        mlflow = softwareSystem "MLflow" "ML experiment tracking (mlflow.opendatahub.io)" "Internal RHOAI"
        prometheusOperator = softwareSystem "prometheus-operator" "Manages Prometheus monitoring resources" "Internal RHOAI"
        opendatahubOperator = softwareSystem "OpenDataHub Operator" "Platform operator providing reconciler SDK" "Internal RHOAI"
        openShift = softwareSystem "OpenShift" "Routes, API servers, platform configuration" "External"
        sparkOperator = softwareSystem "Spark Operator" "Manages SparkApplications (sparkoperator.k8s.io)" "External"

        platformAdmin -> feastModuleOperator "Creates FeastOperator CR via kubectl"
        feastModuleOperator -> kubernetesAPI "CRUD resources, watch CRs" "HTTPS/6443, TLS 1.2+"
        feastModuleOperator -> feastFeatureStore "Watches FeatureStore CRs" "Kubernetes API"
        feastModuleOperator -> kubeflowNotebooks "CRUD Notebook CRs" "Kubernetes API"
        feastModuleOperator -> mlflow "Watches MLflow CRs" "Kubernetes API"
        feastModuleOperator -> prometheusOperator "Creates ServiceMonitors" "Kubernetes API"
        feastModuleOperator -> openShift "Manages Routes, reads APIServer config" "Kubernetes API"
        feastModuleOperator -> sparkOperator "Creates SparkApplications" "Kubernetes API"
        feastModuleOperator -> opendatahubOperator "Imports reconciler SDK" "Go library"
    }

    views {
        systemContext feastModuleOperator "SystemContext" {
            include *
            autoLayout
        }

        container feastModuleOperator "Containers" {
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
