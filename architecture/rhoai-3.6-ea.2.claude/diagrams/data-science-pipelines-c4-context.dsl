workspace {
    model {
        dataScientist = person "Data Scientist" "Defines, schedules, and monitors ML pipelines via SDK, CLI, or web UI"
        platformAdmin = person "Platform Admin" "Manages DSP deployment and RBAC configuration"

        dsp = softwareSystem "Data Science Pipelines" "Kubeflow Pipelines-based ML workflow orchestration platform for defining, scheduling, and executing ML pipelines on OpenShift" {
            apiServer = container "ml-pipeline API Server" "Central control plane exposing 10 gRPC services and REST endpoints via grpc-gateway. Handles auth (TokenReview + HTTP header), pipeline CRUD, and admission webhooks." "Go Service" "Port 8887 gRPC, 8888 REST, 8443 Webhooks"
            pipelineUI = container "ml-pipeline-ui" "Web frontend for browsing pipelines, runs, experiments, and visualizations" "Node.js" "Port 3000"
            persistenceAgent = container "Persistence Agent" "Watches Argo Workflow status and synchronizes run state back to the API server database" "Go Service"
            scheduledWorkflow = container "Scheduled Workflow Controller" "Manages recurring pipeline runs via cron-like scheduling mechanism" "Go Controller"
            cacheServer = container "Cache Server" "Intercepts workflow step execution via mutating webhook, returns cached outputs for identical inputs" "Go Service" "Port 443"
            viewerController = container "Viewer Controller" "Manages Viewer CRDs for pipeline visualization deployments" "Go Controller"
            vizServer = container "Visualization Server" "Generates visualizations for pipeline outputs" "Python Service" "Port 8888"
            metadataWriter = container "Metadata Writer" "Watches workflow pods and writes ML Metadata artifacts to the metadata store" "Python Service"
            metadataEnvoy = container "Metadata Envoy" "gRPC proxy fronting the ML Metadata store" "Envoy Proxy" "Port 9090"
            metadataStore = container "Metadata gRPC Store" "ML Metadata (MLMD) storage backend for experiment tracking" "ml_metadata_store_server" "Port 8080"
            driver = container "Driver" "Executes individual pipeline steps, manages input/output artifacts" "Go Binary" "FIPS: GOFIPS140"
            launcher = container "Launcher-v2" "Launches pipeline step containers with proper configuration" "Go Binary" "FIPS: GOFIPS140"
        }

        argoWorkflows = softwareSystem "Argo Workflows" "Workflow execution engine that orchestrates pipeline steps as Kubernetes pods" "External"
        mysql = softwareSystem "MySQL 8.4" "Relational database for pipeline metadata, run state, and experiment data. Protected by Istio AuthorizationPolicy." "External"
        seaweedfs = softwareSystem "SeaweedFS" "S3-compatible object storage for pipeline artifacts and logs" "External"
        kubernetesAPI = softwareSystem "Kubernetes API" "Platform API server for resource management, TokenReview, SubjectAccessReview, and CRD operations" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection via prometheus.io/scrape annotations" "External"
        externalS3 = softwareSystem "External S3 Storage" "Remote S3-compatible storage for model artifacts (AWS S3, MinIO)" "External"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebooks" "Notebook workbench management for interactive ML development" "Internal RHOAI"

        # Person interactions
        dataScientist -> dsp "Submits pipelines, creates runs, monitors experiments via gRPC/REST API and Web UI"
        platformAdmin -> dsp "Configures RBAC, manages pipeline infrastructure"

        # API Server relationships
        apiServer -> mysql "Stores/retrieves pipeline metadata" "MySQL/3306 Istio mTLS"
        apiServer -> seaweedfs "Stores/retrieves pipeline artifacts" "S3 API/8333"
        apiServer -> argoWorkflows "Creates Argo Workflow resources for pipeline execution" "Kubernetes API"
        apiServer -> kubernetesAPI "TokenReview, SubjectAccessReview, CRD management" "HTTPS/6443"
        apiServer -> externalS3 "Downloads/uploads model artifacts" "HTTPS/443 AWS SDK"

        # UI relationships
        pipelineUI -> apiServer "Queries pipeline data" "REST/8888"
        pipelineUI -> mysql "Direct metadata queries" "MySQL/3306"

        # Execution relationships
        persistenceAgent -> argoWorkflows "Watches workflow status" "Kubernetes API"
        persistenceAgent -> apiServer "Reports run status" "gRPC"
        scheduledWorkflow -> argoWorkflows "Creates scheduled workflows" "Kubernetes API"
        cacheServer -> argoWorkflows "Intercepts workflow steps via mutating webhook" "HTTPS/443"
        driver -> seaweedfs "Reads/writes step artifacts" "S3 API"
        driver -> externalS3 "Reads/writes step artifacts" "HTTPS AWS SDK"
        launcher -> seaweedfs "Reads/writes step artifacts" "S3 API"

        # Metadata relationships
        metadataWriter -> metadataEnvoy "Writes ML Metadata" "gRPC/9090"
        metadataEnvoy -> metadataStore "Proxies metadata requests" "gRPC/8080"
        metadataStore -> mysql "Persists metadata" "MySQL/3306"

        # External integrations
        prometheus -> apiServer "Scrapes metrics" "HTTP/8888"
        dsp -> kubeflowNotebooks "Creates notebook workbenches" "HTTPS Kubernetes API"

        # Webhook flows
        kubernetesAPI -> apiServer "Admission webhooks for PipelineVersion" "HTTPS/8443"
        kubernetesAPI -> cacheServer "Cache mutating webhook" "HTTPS/443"
    }

    views {
        systemContext dsp "SystemContext" {
            include *
            autoLayout
        }

        container dsp "Containers" {
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
