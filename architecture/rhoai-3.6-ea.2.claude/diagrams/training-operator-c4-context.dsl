workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and manages distributed ML training jobs"
        mlEngineer = person "ML Engineer" "Configures training pipelines and monitors job execution"

        trainingOperator = softwareSystem "Training Operator" "Kubernetes operator that orchestrates distributed training jobs across six ML frameworks via CRDs with validating admission webhooks" {
            controller = container "Training Operator Controller" "Multi-reconciler controller managing lifecycle of training jobs" "Go / controller-runtime"
            webhookServer = container "Webhook Server" "Validates training job CRs at admission time with Fail policy" "Go / Port 9443"
            metricsServer = container "Metrics Server" "Exposes Prometheus metrics for operator health and job status" "Go / Port 8080"

            pytorchReconciler = component "PyTorchJob Reconciler" "Manages PyTorchJob lifecycle with elastic training (HPA) support" "Go controller"
            tfReconciler = component "TFJob Reconciler" "Manages TFJob lifecycle for distributed TensorFlow training" "Go controller"
            mpiReconciler = component "MPIJob Reconciler" "Manages MPIJob lifecycle with ConfigMaps, SA, Roles for MPI fabric" "Go controller"
            jaxReconciler = component "JAXJob Reconciler" "Manages JAXJob lifecycle for distributed JAX training" "Go controller"
            xgboostReconciler = component "XGBoostJob Reconciler" "Manages XGBoostJob lifecycle for distributed XGBoost training" "Go controller"
            paddleReconciler = component "PaddleJob Reconciler" "Manages PaddleJob lifecycle for distributed PaddlePaddle training" "Go controller"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster API for resource management and admission control" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "Internal Platform"
        openShiftConfig = softwareSystem "OpenShift APIServer Configuration" "Cluster-wide TLS profile configuration" "External"
        volcano = softwareSystem "Volcano Scheduler" "Gang scheduling for coordinated Pod scheduling" "External"
        schedulerPlugins = softwareSystem "Scheduler Plugins" "Alternative gang scheduling via PodGroup resources" "External"

        # Relationships
        dataScientist -> trainingOperator "Submits training job CRs via kubectl" "kubectl / HTTPS"
        mlEngineer -> trainingOperator "Configures and monitors training jobs" "kubectl / HTTPS"

        trainingOperator -> kubernetesAPI "Watches CRDs, creates Pods/Services/NetworkPolicies" "HTTPS/6443, SA token"
        trainingOperator -> openShiftConfig "Reads cluster TLS profile at startup" "Kubernetes API, SA token"
        trainingOperator -> volcano "Creates PodGroup resources for gang scheduling" "Kubernetes API"
        trainingOperator -> schedulerPlugins "Creates PodGroup resources for gang scheduling" "Kubernetes API"
        prometheus -> trainingOperator "Scrapes operator metrics" "HTTP/8080"

        kubernetesAPI -> trainingOperator "Forwards admission webhooks for training job validation" "HTTPS/443 -> 9443"
    }

    views {
        systemContext trainingOperator "SystemContext" {
            include *
            autoLayout
        }

        container trainingOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal Platform" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #5b9bd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #333333
            }
        }
    }
}
