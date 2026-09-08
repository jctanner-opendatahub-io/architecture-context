workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and manages ML workloads via AI agents"
        mlEngineer = person "ML Engineer" "Deploys models and configures serving runtimes"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform resources"

        rhoaiMcp = softwareSystem "rhoai-mcp" "MCP server enabling AI agents to interact with Red Hat OpenShift AI environments" {
            mcpServer = container "FastMCP Server" "MCP protocol handler with pluggy-based plugin system" "Python / FastMCP"
            oidcMiddleware = container "OIDC Auth Middleware" "Validates JWT/TokenReview and enforces tool-level RBAC" "Python / Starlette"
            notebooksPlugin = container "Notebooks Plugin" "Manages Kubeflow Notebook workbenches" "Python Plugin"
            modelServingPlugin = container "Model Serving Plugin" "Manages KServe InferenceServices and ServingRuntimes" "Python Plugin"
            pipelinesPlugin = container "Pipelines Plugin" "Manages Data Science Pipelines" "Python Plugin"
            trainingPlugin = container "Training Plugin" "Manages Kubeflow Training jobs" "Python Plugin"
            modelRegistryPlugin = container "Model Registry Plugin" "Queries and manages model registry entries" "Python Plugin"
            workflowTokenMgr = container "Workflow Token Manager" "HMAC-SHA256 signed tokens for multi-step workflow enforcement" "Python"
        }

        kubernetesApi = softwareSystem "Kubernetes API Server" "Cluster API for resource management" "External"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebooks" "Notebook workbench CRD operator (kubeflow.org)" "Internal RHOAI"
        kserve = softwareSystem "KServe" "Model serving platform (serving.kserve.io)" "Internal RHOAI"
        kubeflowTraining = softwareSystem "Kubeflow Training" "Distributed training operator (trainer.kubeflow.org)" "Internal RHOAI"
        dsPipelines = softwareSystem "Data Science Pipelines" "ML pipeline orchestration (opendatahub.io)" "Internal RHOAI"
        modelRegistry = softwareSystem "Model Registry" "Model metadata and artifact registry" "Internal RHOAI"
        plannerBackend = softwareSystem "Planner Backend" "Intent extraction and planning service" "Internal RHOAI"

        aiAgent = softwareSystem "AI Agent" "Claude Desktop or other MCP-compatible agent" "External"

        # External relationships
        dataScientist -> aiAgent "Uses to manage RHOAI resources"
        mlEngineer -> aiAgent "Uses to deploy and monitor models"
        platformAdmin -> aiAgent "Uses to manage platform"

        aiAgent -> rhoaiMcp "MCP Protocol (stdio/SSE/streamable-http)" "8000/TCP"

        # Internal container relationships
        mcpServer -> oidcMiddleware "Authenticates requests"
        mcpServer -> notebooksPlugin "Dispatches notebook tools"
        mcpServer -> modelServingPlugin "Dispatches model serving tools"
        mcpServer -> pipelinesPlugin "Dispatches pipeline tools"
        mcpServer -> trainingPlugin "Dispatches training tools"
        mcpServer -> modelRegistryPlugin "Dispatches registry tools"
        mcpServer -> workflowTokenMgr "Validates/generates workflow tokens"

        # System-to-system relationships
        rhoaiMcp -> kubernetesApi "HTTPS/6443 (SA Token, User-Token, Impersonation)"
        rhoaiMcp -> modelRegistry "HTTP/8080 (None/OAuth/Token)"
        rhoaiMcp -> plannerBackend "HTTP/8000 (cluster-internal)"

        kubernetesApi -> kubeflowNotebooks "Manages Notebook CRs"
        kubernetesApi -> kserve "Manages InferenceService CRs"
        kubernetesApi -> kubeflowTraining "Manages TrainJob CRs"
        kubernetesApi -> dsPipelines "Manages DSPApplication CRs"

        oidcMiddleware -> kubernetesApi "TokenReview validation" "HTTPS/6443"
    }

    views {
        systemContext rhoaiMcp "SystemContext" {
            include *
            autoLayout
        }

        container rhoaiMcp "Containers" {
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
