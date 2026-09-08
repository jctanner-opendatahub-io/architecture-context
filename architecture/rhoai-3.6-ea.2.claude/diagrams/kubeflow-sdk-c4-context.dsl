workspace {
    model {
        dataScientist = person "Data Scientist" "Defines and submits ML training jobs, pipelines, and experiments"
        mlEngineer = person "ML Engineer" "Manages training workflows and model deployment pipelines"

        kubeflowSDK = softwareSystem "Kubeflow SDK" "Python client library providing a unified interface for managing ML workloads across Kubeflow Trainer, Katib, Spark, Pipelines, and Model Registry" {
            coreTrainer = container "kubeflow.trainer" "Training job management with backend abstraction" "Python Module"
            k8sBackend = container "Kubernetes Backend" "Translates training definitions into Kubernetes custom resources (TrainJob CRs)" "Python Module"
            rhaiExtensions = container "RHAI Extensions" "SpeculativeDecodingTrainer, TrainingHubTrainer, JIT Checkpoint Injection" "Python Module (RHOAI-specific)"
            pipelinesModule = container "kubeflow.pipelines" "Pipeline definition and execution compatibility layer" "Python Module (Optional)"
            katibModule = container "kubeflow.katib" "Hyperparameter tuning experiment management" "Python Module (Optional)"
            sparkModule = container "kubeflow.spark" "Spark workload management" "Python Module (Optional)"
            modelRegistryModule = container "kubeflow.model_registry" "Model metadata and artifact registry client" "Python Module (Optional)"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster control plane handling resource CRUD and authentication" "External"
        trainerController = softwareSystem "Kubeflow Trainer Controller" "Manages TrainJob lifecycle, creates training pods" "Internal RHOAI"
        katibController = softwareSystem "Katib Controller" "Manages hyperparameter tuning experiments" "Internal RHOAI"
        kubeflowPipelines = softwareSystem "Kubeflow Pipelines" "ML pipeline orchestration platform" "Internal RHOAI"
        modelRegistry = softwareSystem "Model Registry" "Stores model metadata and artifact references" "Internal RHOAI"
        sparkOperator = softwareSystem "Spark Operator" "Manages Spark workloads on Kubernetes" "Internal RHOAI"

        # Relationships
        dataScientist -> kubeflowSDK "Defines training jobs, pipelines, experiments via Python API"
        mlEngineer -> kubeflowSDK "Manages RHAI-specific training workflows"

        kubeflowSDK -> kubernetesAPI "Creates/manages CRs via kubernetes Python client" "HTTPS/6443, kube-config/SA token"
        kubeflowSDK -> kubeflowPipelines "Defines and executes pipelines" "via kfp SDK"
        kubeflowSDK -> modelRegistry "Registers and queries model metadata" "Python client"

        k8sBackend -> kubernetesAPI "CustomObjectsApi / CoreV1Api calls" "HTTPS/6443"
        rhaiExtensions -> k8sBackend "Submits RHAI-extended TrainJob configurations"
        pipelinesModule -> kubeflowPipelines "Pipeline definition and execution"
        katibModule -> kubernetesAPI "Creates Experiment/Trial CRs"
        sparkModule -> kubernetesAPI "Creates SparkConnect CRs"

        kubernetesAPI -> trainerController "Watch events for TrainJob CRs"
        kubernetesAPI -> katibController "Watch events for Experiment CRs"
        kubernetesAPI -> sparkOperator "Watch events for SparkConnect CRs"
    }

    views {
        systemContext kubeflowSDK "SystemContext" {
            include *
            autoLayout
        }

        container kubeflowSDK "Containers" {
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
        }
    }
}
