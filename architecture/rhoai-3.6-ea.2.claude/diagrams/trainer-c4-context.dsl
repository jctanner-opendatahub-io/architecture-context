workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and submits distributed training workloads via TrainJob CRs"
        clusterAdmin = person "Cluster Admin" "Configures TrainingRuntimes and ClusterTrainingRuntimes"

        trainer = softwareSystem "Trainer Operator" "Kubeflow Trainer v2 operator that manages distributed training workloads through TrainJob, TrainingRuntime, and ClusterTrainingRuntime CRDs" {
            controllerManager = container "Trainer Controller Manager" "Reconciles TrainJob CRs into downstream JobSet resources with pluggable framework plugins" "Go controller-runtime"
            webhookServer = container "Webhook Server" "Validates and defaults TrainJob and runtime resources with Fail policy" "Go HTTPS/443"
            metricsServer = container "Metrics Server" "Exposes operator metrics" "Go HTTPS/8443"
            statusServer = container "Status Server" "Operator status endpoint" "Go TCP/10443"
            fluxPlugin = container "Flux Plugin" "Manages ConfigMaps and Secrets for basic distributed workloads" "Go Plugin"
            mpiPlugin = container "MPI Plugin" "Manages ConfigMaps and Secrets for MPI-based distributed training" "Go Plugin"
            coschedulingPlugin = container "CoScheduling Plugin" "Creates scheduler-plugins PodGroups for gang scheduling" "Go Plugin"
            volcanoPlugin = container "Volcano Plugin" "Creates Volcano PodGroups for gang scheduling" "Go Plugin"
            networkPolicyReconciler = container "NetworkPolicy Reconciler" "Creates per-TrainJob ingress NetworkPolicies for workload isolation" "Go (RHOAI)"
            progressionTracker = container "Progression Tracker" "Tracks training pod status for TrainJob status reporting" "Go (RHOAI)"
            datasetInitializer = container "Dataset Initializer" "Python init container for dataset preparation" "Python"
            modelInitializer = container "Model Initializer" "Python init container for model preparation" "Python"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "External"
        jobset = softwareSystem "JobSet Controller" "Manages JobSet CRDs for replicated distributed jobs" "Internal Platform"
        schedulerPlugins = softwareSystem "Kubernetes Scheduler Plugins" "CoScheduling scheduler for gang scheduling via PodGroups" "Internal Platform"
        volcanoScheduler = softwareSystem "Volcano Scheduler" "Gang scheduling through Volcano PodGroups" "Internal Platform"
        openshiftPlatform = softwareSystem "OpenShift Platform" "Provides TLSSecurityProfile via config.openshift.io APIServer" "External"
        certController = softwareSystem "OPA cert-controller" "Rotates webhook TLS certificates" "External"

        # User interactions
        dataScientist -> trainer "Creates TrainJob CRs via kubectl" "HTTPS/6443"
        clusterAdmin -> trainer "Configures TrainingRuntime/ClusterTrainingRuntime" "HTTPS/6443"

        # Trainer dependencies
        trainer -> kubernetesAPI "Watches CRDs, creates resources" "HTTPS/6443 SA token"
        trainer -> jobset "Creates JobSet CRs for distributed execution" "Kubernetes API"
        trainer -> schedulerPlugins "Creates PodGroups for gang scheduling" "Kubernetes API"
        trainer -> volcanoScheduler "Creates PodGroups for gang scheduling" "Kubernetes API"
        trainer -> openshiftPlatform "Reads TLSSecurityProfile" "Kubernetes API"
        certController -> trainer "Rotates webhook certificates" "Kubernetes API"

        # Internal container relationships
        controllerManager -> webhookServer "Serves admission requests"
        controllerManager -> fluxPlugin "Resolves Flux runtime"
        controllerManager -> mpiPlugin "Resolves MPI runtime"
        controllerManager -> coschedulingPlugin "Resolves CoScheduling runtime"
        controllerManager -> volcanoPlugin "Resolves Volcano runtime"
        controllerManager -> networkPolicyReconciler "Reconciles NetworkPolicies"
        controllerManager -> progressionTracker "Tracks training progression"
    }

    views {
        systemContext trainer "SystemContext" {
            include *
            autoLayout
        }

        container trainer "Containers" {
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
                shape Person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
