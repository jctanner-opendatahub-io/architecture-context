workspace {
    model {
        dspApiServer = person "DSP API Server" "Data Science Pipelines API server that orchestrates workflows"
        dataScientist = person "Data Scientist" "Creates and runs ML pipelines via DSP"

        argoWorkflows = softwareSystem "Argo Workflows" "Kubernetes-native workflow execution engine for Data Science Pipelines in RHOAI" {
            workflowController = container "workflow-controller" "Reconciles Workflow CRDs, creates and monitors step Pods, manages memoization caches" "Go Operator"
            argoServer = container "argo-server" "gRPC + HTTP API gateway for workflow management, artifact retrieval, and SSO-backed authentication" "Go Service" {
                gatekeeper = component "Gatekeeper" "Authentication interceptor supporting Client (Bearer/Basic), Server (SA), and SSO (OIDC) modes" "Go Interceptor"
                grpcGateway = component "grpc-gateway" "REST-to-gRPC translation layer for HTTP clients" "grpc-gateway"
                grpcServices = component "gRPC Services" "9 services: Workflow, CronWorkflow, WorkflowTemplate, ClusterWorkflowTemplate, ArchivedWorkflow, Event, EventSource, Sensor, Info" "gRPC"
            }
            argoexec = container "argoexec" "Sidecar injected into workflow step Pods; handles artifact collection and container lifecycle" "Go Sidecar"
        }

        k8sApi = softwareSystem "Kubernetes API" "Kubernetes API server for cluster resource management" "External"
        dspOperator = softwareSystem "Data Science Pipelines Operator" "Deploys and configures Argo Workflows as part of the DSP stack" "Internal RHOAI"

        # Relationships
        dataScientist -> dspApiServer "Submits ML pipeline runs"
        dspApiServer -> argoServer "Creates/manages workflows" "gRPC+HTTP/2746"
        dspOperator -> argoWorkflows "Deploys and configures" "Kubernetes resources"

        argoServer -> k8sApi "CRUD on Workflow CRs, impersonation, SelfSubjectAccessReview" "HTTPS+WSS/6443"
        workflowController -> k8sApi "Watches CRDs, creates Pods, ConfigMaps, PDBs, Secrets" "HTTPS+WSS/6443"
        argoexec -> k8sApi "Reports WorkflowTaskResults" "HTTPS/6443"

        workflowController -> argoexec "Injects sidecar into step Pods" "Pod spec injection"
    }

    views {
        systemContext argoWorkflows "SystemContext" {
            include *
            autoLayout
        }

        container argoWorkflows "Containers" {
            include *
            autoLayout
        }

        component argoServer "ArgoServerComponents" {
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
                shape person
                background #4a90e2
                color #ffffff
            }
        }
    }
}
