workspace {
    model {
        dataScientist = person "Data Scientist" "Creates notebooks, deploys models, manages pipelines via the RHOAI web console"
        mlEngineer = person "ML Engineer" "Manages model serving, model registry, and inference endpoints"
        admin = person "Platform Admin" "Installs and configures RHOAI platform components"

        odhDashboard = softwareSystem "ODH Dashboard" "RHOAI web console: federated micro-frontend with per-domain Go BFF sidecars and a Node.js backend" {
            dashboardOperator = container "Dashboard Operator" "Reconciles Dashboard CRs; manages Deployments, Services, Routes, RBAC, NetworkPolicies" "Go (controller-runtime)" "operator"
            workspaceController = container "Workspace Controller" "Manages Workspace StatefulSets, Services, HTTPRoutes" "Go (controller-runtime)" "operator"
            workspaceKindController = container "WorkspaceKind Controller" "Manages WorkspaceKind lifecycle and CRD conversion" "Go (controller-runtime)" "operator"
            webhookServer = container "Webhook Server" "Validates Dashboard, Workspace, WorkspaceKind CRs" "Go (port 9443)" "webhook"
            nodejsBackend = container "Node.js Backend" "Serves React SPA, proxies K8s API, WebSocket watches" "Node.js/Fastify (port 8443 via kube-rbac-proxy)" "backend"
            reactSPA = container "React SPA" "PatternFly 6.5 micro-frontend host with Webpack Module Federation" "React/TypeScript" "frontend"
            coreBFF = container "core-bff" "Core dashboard API: pipelines, PVCs, storage, cluster settings" "Go BFF (port 8080)" "bff"
            genAiBFF = container "gen-ai BFF" "GenAI features: Llama Stack, NeMo Guardrails, MLMD" "Go BFF (port 8080)" "bff"
            maasBFF = container "maas BFF" "Model-as-a-Service: API keys, models, subscriptions" "Go BFF (port 8080)" "bff"
            modelRegistryBFF = container "model-registry BFF" "Model Registry CRUD and version tracking" "Go BFF (port 8080)" "bff"
            agentOpsBFF = container "agent-ops BFF" "Agent operations: sandbox management, per-agent RBAC" "Go BFF (port 8080)" "bff"
            evalHubBFF = container "eval-hub BFF" "TrustyAI integration: fairness and explainability" "Go BFF (port 8080)" "bff"
            mlflowBFF = container "mlflow BFF" "MLflow experiments, prompts, and tracking" "Go BFF (port 8080)" "bff"
        }

        # Internal RHOAI Platform Components
        rhodsOperator = softwareSystem "RHOAI Operator" "Creates and owns the Dashboard CR" "Internal ODH"
        kserve = softwareSystem "KServe" "Model serving and inference management" "Internal ODH"
        trustyai = softwareSystem "TrustyAI" "AI fairness, explainability, and evaluation" "Internal ODH"
        modelRegistry = softwareSystem "Model Registry" "Model version metadata and artifact tracking" "Internal ODH"
        dsPipelines = softwareSystem "DataScience Pipelines" "ML pipeline execution and management" "Internal ODH"
        feast = softwareSystem "Feast" "Feature store for ML features" "Internal ODH"
        mlflow = softwareSystem "MLflow" "Experiment tracking and model lifecycle" "Internal ODH"
        notebooks = softwareSystem "Kubeflow Notebooks" "Interactive notebook environments" "Internal ODH"

        # External Infrastructure
        k8sAPI = softwareSystem "Kubernetes API" "Cluster resource management" "External"
        gatewayAPI = softwareSystem "Gateway API" "Ingress and routing" "External"
        certManager = softwareSystem "cert-manager" "TLS certificate lifecycle" "External"
        prometheus = softwareSystem "Prometheus/Thanos" "Monitoring and metrics" "External"
        istio = softwareSystem "Istio" "Service mesh" "External"

        # External AI Services
        llamaStack = softwareSystem "Llama Stack" "LLM inference, vector stores, files" "External"
        nemoGuardrails = softwareSystem "NeMo Guardrails" "Content moderation and safety" "External"
        maasProvider = softwareSystem "MaaS Provider" "Model-as-a-Service API" "External"
        mlmd = softwareSystem "ML Metadata" "Artifact and execution tracking (gRPC-web)" "External"

        # User relationships
        dataScientist -> odhDashboard "Uses RHOAI web console via browser" "HTTPS/443"
        mlEngineer -> odhDashboard "Manages models and serving via browser" "HTTPS/443"
        admin -> rhodsOperator "Configures RHOAI platform" "CLI/Console"

        # Internal component relationships
        reactSPA -> nodejsBackend "API calls, WebSocket watches" "HTTPS/8443"
        nodejsBackend -> k8sAPI "Impersonated K8s API calls" "HTTPS/6443"
        nodejsBackend -> coreBFF "Proxies /_mf/core-bff/*" "HTTP/8080"
        nodejsBackend -> genAiBFF "Proxies /_mf/gen-ai/*" "HTTP/8080"
        nodejsBackend -> maasBFF "Proxies /_mf/maas/*" "HTTP/8080"
        nodejsBackend -> modelRegistryBFF "Proxies /_mf/model-registry/*" "HTTP/8080"
        nodejsBackend -> agentOpsBFF "Proxies /_mf/agent-ops/*" "HTTP/8080"
        nodejsBackend -> evalHubBFF "Proxies /_mf/eval-hub/*" "HTTP/8080"
        nodejsBackend -> mlflowBFF "Proxies /_mf/mlflow/*" "HTTP/8080"

        # BFF to platform service relationships
        coreBFF -> dsPipelines "Pipeline execution" "HTTPS/8443"
        coreBFF -> prometheus "Metrics queries" "HTTPS/9092"
        genAiBFF -> mlmd "Artifact tracking" "gRPC-web/8443"
        genAiBFF -> llamaStack "LLM inference" "HTTPS"
        genAiBFF -> nemoGuardrails "Content moderation" "HTTPS"
        maasBFF -> maasProvider "API keys and models" "HTTPS"
        modelRegistryBFF -> modelRegistry "Model version CRUD" "HTTPS/8443"
        evalHubBFF -> trustyai "Fairness and explainability" "HTTPS/443"
        mlflowBFF -> mlflow "Experiment tracking" "HTTPS"
        agentOpsBFF -> k8sAPI "Agent RBAC (SubjectAccessReview)" "HTTPS/6443"

        # Operator relationships
        rhodsOperator -> odhDashboard "Creates Dashboard CR"
        dashboardOperator -> k8sAPI "Manages Deployments, Services, Routes, RBAC" "HTTPS/6443"
        workspaceController -> k8sAPI "Manages StatefulSets, Services, HTTPRoutes" "HTTPS/6443"
        workspaceController -> gatewayAPI "Creates HTTPRoutes" "HTTPS"
        dashboardOperator -> certManager "TLS certificates" "HTTPS"

        # CRD watches
        dashboardOperator -> kserve "Watches InferenceService CRs" "K8s Watch"
        dashboardOperator -> feast "Watches FeatureStore CRs" "K8s Watch"
        dashboardOperator -> mlflow "Watches MLflow CRs" "K8s Watch"
        dashboardOperator -> trustyai "Watches TrustyAI CRs" "K8s Watch"
        dashboardOperator -> modelRegistry "Watches ModelRegistry CRs" "K8s Watch"
    }

    views {
        systemContext odhDashboard "SystemContext" {
            include *
            autoLayout
        }

        container odhDashboard "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal ODH" {
                background #7ed321
                color #ffffff
            }
            element "operator" {
                background #4a90e2
                color #ffffff
            }
            element "webhook" {
                background #4a90e2
                color #ffffff
            }
            element "backend" {
                background #68a063
                color #ffffff
            }
            element "frontend" {
                background #61dafb
                color #000000
            }
            element "bff" {
                background #f5a623
                color #000000
            }
        }
    }
}
