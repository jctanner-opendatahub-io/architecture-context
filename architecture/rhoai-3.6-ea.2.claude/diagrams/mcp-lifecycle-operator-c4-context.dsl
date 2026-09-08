workspace {
    model {
        user = person "Platform User / Admin" "Creates and manages MCPServer custom resources"

        mcpLifecycleOperator = softwareSystem "MCP Lifecycle Operator" "Manages lifecycle of Model Context Protocol servers on Kubernetes" {
            reconciler = container "MCPServerReconciler" "Reconciles MCPServer CRs into Deployments, Services, and NetworkPolicies" "Go controller-runtime"
            healthProbe = container "Health Probe Server" "Exposes /healthz and /readyz endpoints" "HTTP :8081"
            metricsServer = container "Metrics Server" "Exposes Prometheus metrics with TLS and authn/authz" "HTTPS :8443"
            leaderElection = container "Leader Election" "Lease-based coordination for HA" "coordination.k8s.io/Lease"
            tlsConfig = container "TLS Configuration" "Manages TLS settings via env vars (TLS_MIN_VERSION, TLS_CIPHER_SUITES)" "Go crypto/tls"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External" {
            tags "External"
        }

        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External" {
            tags "External"
        }

        mcpServer = softwareSystem "MCP Server Instances" "Managed MCP server workloads (Deployments, Services, NetworkPolicies)" "Managed" {
            tags "Managed"
        }

        controllerRuntime = softwareSystem "controller-runtime" "Kubernetes operator framework" "External" {
            tags "External"
        }

        mcpGoSDK = softwareSystem "MCP Go SDK" "Model Context Protocol Go SDK" "External" {
            tags "External"
        }

        user -> mcpLifecycleOperator "Creates MCPServer CRs via kubectl"
        mcpLifecycleOperator -> k8sAPI "Watches MCPServer, ConfigMap, Secret; CRUD Deployments, Services, NetworkPolicies" "HTTPS/WSS :6443 TLS 1.2+"
        mcpLifecycleOperator -> mcpServer "Creates and manages MCP server workloads" "Kubernetes ownership"
        prometheus -> mcpLifecycleOperator "Scrapes metrics" "HTTPS :8443 TokenReview+SAR"

        reconciler -> k8sAPI "Watch events and CRUD operations" "HTTPS/WSS :6443"
        metricsServer -> k8sAPI "TokenReview and SubjectAccessReview" "HTTPS :6443"
    }

    views {
        systemContext mcpLifecycleOperator "SystemContext" {
            include *
            autoLayout
        }

        container mcpLifecycleOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Managed" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
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
