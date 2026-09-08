workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and runs ML pipelines for data processing, AutoML, and RAG optimization"
        platformAdmin = person "Platform Admin" "Deploys and configures the KFP platform with managed pipelines"

        pipelinesComponents = softwareSystem "pipelines-components" "Reusable KFP components and managed pipeline definitions for data processing, AutoML, AutoRAG, and synthetic data generation" {
            initContainer = container "Init Container" "Copies pre-compiled pipeline YAMLs to shared volume for KFP API server registration" "Python (init_managed_pipelines)"
            tabularLoader = container "Tabular Data Loader" "Loads and preprocesses tabular data from S3 for AutoML training" "Python KFP Component"
            parseChunk = container "Parse & Chunk" "Parses documents and chunks them, optionally using distributed Ray processing" "Python KFP Component"
            sdgComponent = container "SDG Component" "Generates synthetic data using SDG Hub SDK" "Python KFP Component"
            autoragComponent = container "AutoRAG Component" "Optimizes RAG search templates using ai4rag" "Python KFP Component"
            datasetDownload = container "Dataset Download" "Downloads datasets from S3-compatible storage" "Python KFP Component"
        }

        kfpServer = softwareSystem "Kubeflow Pipelines" "Pipeline orchestration platform that manages and executes ML workflows" "Internal RHOAI"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management and RayJob submission" "External"
        s3Storage = softwareSystem "S3-Compatible Storage" "Object storage for data artifacts, models, and datasets" "External"
        rayCluster = softwareSystem "Ray Cluster" "Distributed compute cluster for parallel document processing" "Internal RHOAI"
        sdgHub = softwareSystem "SDG Hub" "Synthetic data generation service" "Internal RHOAI"
        ai4rag = softwareSystem "ai4rag" "RAG search space construction and optimization library" "Internal RHOAI"
        huggingface = softwareSystem "HuggingFace Hub" "Model and dataset repository" "External"

        # Relationships
        platformAdmin -> pipelinesComponents "Deploys init container with managed pipelines"
        dataScientist -> kfpServer "Creates and monitors pipeline runs"

        initContainer -> kfpServer "Stages pipeline YAMLs via shared volume"
        kfpServer -> tabularLoader "Orchestrates as task pod"
        kfpServer -> parseChunk "Orchestrates as task pod"
        kfpServer -> sdgComponent "Orchestrates as task pod"
        kfpServer -> autoragComponent "Orchestrates as task pod"
        kfpServer -> datasetDownload "Orchestrates as task pod"

        tabularLoader -> s3Storage "Reads/writes data artifacts" "HTTPS/443, AWS credentials"
        parseChunk -> s3Storage "Reads/writes processed chunks" "HTTPS/443, AWS credentials"
        parseChunk -> k8sAPI "Submits RayJobs" "HTTPS/6443, SA token"
        parseChunk -> rayCluster "Distributed processing via CodeFlare SDK"
        datasetDownload -> s3Storage "Downloads datasets" "HTTPS/443, AWS credentials"
        sdgComponent -> sdgHub "Executes SDG flows" "SDK calls"
        autoragComponent -> ai4rag "Optimizes RAG templates" "SDK calls"
        tabularLoader -> huggingface "Downloads models/datasets" "HTTPS, HF_TOKEN"
    }

    views {
        systemContext pipelinesComponents "SystemContext" {
            include *
            autoLayout
        }

        container pipelinesComponents "Containers" {
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
