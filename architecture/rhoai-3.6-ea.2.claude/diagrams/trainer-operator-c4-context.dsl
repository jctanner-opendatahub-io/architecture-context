workspace {
    model {
        platformOperator = person "Platform Operator" "Manages RHOAI platform components"
        clusterAdmin = person "Cluster Admin" "Manages OpenShift cluster and security"

        trainerOperator = softwareSystem "Trainer Operator" "Kubernetes operator managing Kubeflow Trainer v2 lifecycle on RHOAI" {
            controller = container "Trainer Controller" "Reconciles Trainer CR, renders and deploys Kubeflow Trainer v2 stack" "Go controller-runtime"
            metricsServer = container "Metrics Server" "Serves operator metrics over HTTPS with K8s authn/authz" "HTTPS :8443"
            tlsWatcher = container "TLS Profile Watcher" "Monitors OpenShift TLS profile changes and triggers graceful restart" "Go"
            manifestRenderer = container "Manifest Renderer" "Renders upstream manifests via kustomize overlays" "odh-platform-utilities"
        }

        kubeflowTrainer = softwareSystem "Kubeflow Trainer v2" "Deployed training infrastructure (TrainJob, ClusterTrainingRuntime, TrainingRuntime)" "Managed"

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster API for resource management" "External"
        jobSetOperator = softwareSystem "JobSet Operator" "Prerequisite operator for batch job orchestration" "External"
        openshiftAPIServer = softwareSystem "OpenShift APIServer" "Provides cluster TLS profile configuration" "External"
        serviceCa = softwareSystem "OpenShift Service-CA" "Provisions and rotates TLS certificates" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"
        olm = softwareSystem "OLM" "Operator Lifecycle Manager for subscription status" "External"

        platformOperator -> trainerOperator "Creates Trainer CR" "kubectl / API"
        clusterAdmin -> openshiftAPIServer "Configures cluster TLS profile"

        trainerOperator -> kubernetesAPI "CRUD resources, watch events, server-side apply" "HTTPS/6443 TLS 1.2+"
        trainerOperator -> kubeflowTrainer "Deploys and manages lifecycle" "Server-Side Apply"
        trainerOperator -> jobSetOperator "Checks CRD availability (prerequisite gate)" "Kubernetes API"
        trainerOperator -> openshiftAPIServer "Resolves TLS profile, watches for changes" "Kubernetes API"
        serviceCa -> trainerOperator "Provisions metrics TLS certificate" "Auto-provisioned"
        prometheus -> trainerOperator "Scrapes /metrics endpoint" "HTTPS/8443 TokenReview+SAR"
        trainerOperator -> olm "Lists OperatorConditions" "Kubernetes API"
    }

    views {
        systemContext trainerOperator "SystemContext" {
            include *
            autoLayout
        }

        container trainerOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Managed" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #4a90e2
                color #ffffff
            }
        }
    }
}
