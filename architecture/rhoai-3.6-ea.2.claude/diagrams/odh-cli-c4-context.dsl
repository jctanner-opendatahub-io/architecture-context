workspace {
    model {
        admin = person "Cluster Admin" "RHOAI platform administrator managing deployments"
        aiAgent = person "AI Agent" "MCP client consuming CLI operations programmatically"

        odhCli = softwareSystem "odh-cli (rhai-cli)" "Cobra-based kubectl plugin for managing, diagnosing, and migrating RHOAI deployments" {
            rootCmd = container "Root Command" "Cobra CLI root with 13 subcommand groups" "Go CLI"
            unifiedClient = container "Unified Client Layer" "Wraps 5 Kubernetes client types behind Reader/Writer/Client interfaces" "Go Package"
            migrateCmd = container "Migrate Command" "TrustYAI metrics backup/restore via HTTPS" "Go CLI Subcommand"
            diagnoseCmd = container "Diagnose Command" "Cluster health assessment with failure classification" "Go CLI Subcommand"
            mcpServer = container "MCP Server" "JSON-RPC over SSE for AI agent integration" "Go HTTP Server"
        }

        k8sApi = softwareSystem "Kubernetes API" "Cluster API server for resource operations" "External"
        olm = softwareSystem "Operator Lifecycle Manager" "Manages operator subscriptions and CSVs" "Internal Platform"
        odhOperator = softwareSystem "opendatahub-operator" "Provides clusterhealth, failureclassifier, and mcptools packages" "Internal ODH"
        trustyai = softwareSystem "TrustYAI Service" "ML model explainability and metrics service" "Internal ODH"
        openshiftRoutes = softwareSystem "OpenShift Routes" "Service discovery via Route objects" "External"

        # User interactions
        admin -> odhCli "Runs CLI commands via kubectl plugin" "CLI"
        aiAgent -> odhCli "Invokes CLI operations via MCP protocol" "JSON-RPC/SSE"

        # Internal flows
        rootCmd -> unifiedClient "Delegates cluster operations"
        migrateCmd -> unifiedClient "Reads cluster state"
        diagnoseCmd -> unifiedClient "Reads cluster state"
        mcpServer -> rootCmd "Dispatches tool calls as subcommands"

        # External dependencies
        unifiedClient -> k8sApi "REST + WebSocket" "HTTPS/6443 TLS 1.2+"
        unifiedClient -> olm "Lists Subscriptions, CSVs" "HTTPS/6443"
        diagnoseCmd -> odhOperator "Imports clusterhealth and failureclassifier" "Go library"
        mcpServer -> odhOperator "Imports mcptools for tool definitions" "Go library"
        migrateCmd -> openshiftRoutes "Discovers TrustYAI endpoints" "HTTPS/6443"
        migrateCmd -> trustyai "Backup/restore metrics" "HTTPS/443 TLS 1.2+"
    }

    views {
        systemContext odhCli "SystemContext" {
            include *
            autoLayout
        }

        container odhCli "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal Platform" {
                background #4a90e2
                color #ffffff
            }
            element "Internal ODH" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
        }
    }
}
