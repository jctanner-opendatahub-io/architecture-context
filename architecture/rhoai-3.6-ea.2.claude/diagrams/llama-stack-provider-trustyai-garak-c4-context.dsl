workspace {
    model {
        datascientist = person "Data Scientist / Security Engineer" "Configures and triggers red-teaming evaluations against deployed LLMs"

        garakAdapter = softwareSystem "llama-stack-provider-trustyai-garak" "Garak red-teaming evaluation adapter that runs as a K8s Job to assess LLM safety and vulnerability using NVIDIA Garak framework" {
            adapterCore = container "GarakAdapter" "FrameworkAdapter implementation that orchestrates scan execution in simple or KFP mode" "Python 3.12+"
            garakCLI = container "Garak CLI" "NVIDIA Garak security testing framework executed as subprocess (simple mode)" "Python CLI"
            kfpClient = container "KFP Pipeline Client" "Submits and monitors 6-step Kubeflow Pipeline for distributed scan execution (KFP mode)" "Python KFP SDK"
            authResolver = container "Auth Resolution Chain" "Multi-tier credential resolution: API Key → Named Key → Env Var → Role Convention → DUMMY" "Python Module"
            resultReporter = container "Result Reporter" "Parses JSONL results and reports via DefaultCallbacks sidecar" "Python Module"
        }

        evalHub = softwareSystem "Eval-Hub" "Evaluation orchestration platform that manages benchmark jobs and collects results" "Internal RHOAI"
        kfpServer = softwareSystem "Kubeflow Pipelines" "ML pipeline orchestration platform for distributed scan execution" "Internal RHOAI"
        targetLLM = softwareSystem "Target LLM" "Large Language Model endpoint being evaluated for safety vulnerabilities" "External"
        s3Storage = softwareSystem "S3-Compatible Storage" "Object storage for KFP pipeline artifact transfer (via Data Connection secret)" "External"
        ociRegistry = softwareSystem "OCI Registry" "Container/artifact registry for persisting scan result artifacts" "External"
        kubernetes = softwareSystem "Kubernetes" "Container orchestration platform that runs the adapter as a batch Job" "Infrastructure"

        # Relationships
        datascientist -> evalHub "Configures evaluation job"
        evalHub -> garakAdapter "Creates K8s Job with JobSpec ConfigMap"

        adapterCore -> garakCLI "Executes scan (simple mode)"
        adapterCore -> kfpClient "Submits pipeline (KFP mode)"
        adapterCore -> authResolver "Resolves credentials"
        adapterCore -> resultReporter "Sends parsed results"

        garakCLI -> targetLLM "Sends red-teaming probes" "HTTPS / API Key"
        kfpClient -> kfpServer "Submits 6-step pipeline" "HTTPS / KFP_AUTH_TOKEN"
        kfpClient -> s3Storage "Transfers artifacts" "HTTPS/443 / AWS IAM"
        resultReporter -> evalHub "Reports results" "HTTP/HTTPS / DefaultCallbacks"
        resultReporter -> ociRegistry "Persists artifacts" "HTTPS/443 / Registry Auth"

        garakAdapter -> kubernetes "Runs as batch Job"
    }

    views {
        systemContext garakAdapter "SystemContext" {
            include *
            autoLayout
        }

        container garakAdapter "Containers" {
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
            element "Infrastructure" {
                background #4a90e2
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                shape RoundedBox
            }
            element "Container" {
                shape RoundedBox
            }
        }
    }
}
