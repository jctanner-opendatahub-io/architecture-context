workspace {
    model {
        clusterAdmin = person "Cluster Admin" "Manages RHOAI platform components and creates MCPLifecycleOperator CR"
        namespaceUser = person "Namespace User" "Creates and manages MCPServer resources via RBAC aggregation"

        mcpLifecycleModuleOperator = softwareSystem "MCP Lifecycle Module Operator" "Two-tier Kubernetes operator managing MCP server infrastructure lifecycle within RHOAI" {
            moduleController = container "Module Operator Controller" "Reconciles MCPLifecycleOperator CRs, renders Kustomize manifests, applies via SSA" "Go controller-runtime, GOEXPERIMENT=strictfipsruntime"
            kustomizeRenderer = container "Kustomize Renderer" "Renders embedded manifests with runtime params (image, namespace, TLS)" "Go embedded"
            garbageCollector = container "Garbage Collector" "Label-based cleanup of removed/unmanaged resources" "Go"
            operand = container "mcp-lifecycle-operator-controller-manager" "Manages MCPServer namespaced resources for MCP protocol server instances" "Go, Deployed by Module Operator"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "External" {
            tags "External"
        }

        openshiftAPIServer = softwareSystem "OpenShift APIServer" "Cluster-wide TLS profile configuration" "External" {
            tags "External"
        }

        platformConfigMap = softwareSystem "Platform ConfigMap" "Distribution detection (RHOAI vs standalone)" "Internal RHOAI" {
            tags "Internal RHOAI"
        }

        prometheusOperator = softwareSystem "Prometheus Operator" "Monitoring via ServiceMonitor resources" "External" {
            tags "External"
        }

        odhPlatformUtilities = softwareSystem "odh-platform-utilities" "Shared platform behaviors: conditions, phases, manifest rendering" "Internal RHOAI" {
            tags "Internal RHOAI"
        }

        clusterAdmin -> mcpLifecycleModuleOperator "Creates MCPLifecycleOperator CR via kubectl"
        namespaceUser -> mcpLifecycleModuleOperator "Creates MCPServer CRs via kubectl (RBAC aggregation)"

        moduleController -> kustomizeRenderer "Renders manifests with runtime parameters"
        moduleController -> garbageCollector "Triggers cleanup on resource removal"
        moduleController -> kubernetesAPI "Watches/applies resources via SSA" "HTTPS/6443, TLS 1.2+, SA token"
        moduleController -> openshiftAPIServer "Reads cluster TLS profile" "HTTPS/6443, read-only"
        moduleController -> platformConfigMap "Reads distribution context" "Kubernetes API"

        operand -> kubernetesAPI "Manages MCPServer resources" "HTTPS/6443, TLS 1.2+, SA token"
        operand -> prometheusOperator "Exposes metrics via ServiceMonitor" "HTTPS/8443"

        mcpLifecycleModuleOperator -> odhPlatformUtilities "Uses for conditions, phases, deploy helpers" "Go library"
    }

    views {
        systemContext mcpLifecycleModuleOperator "SystemContext" {
            include *
            autoLayout
        }

        container mcpLifecycleModuleOperator "Containers" {
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
