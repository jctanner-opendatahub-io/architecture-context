workspace {
    model {
        platformOperator = person "Platform Operator" "Creates and manages LLMBatchGateway CRs for batch inference"

        batchGatewayOperator = softwareSystem "llm-d-batch-gateway-operator" "Kubernetes operator that reconciles LLMBatchGateway CRs to deploy batch inference gateway stacks using embedded Helm charts" {
            manager = container "Manager (/manager)" "Main operator binary; runs LLMBatchGatewayReconciler, MetricsController, SecretSynchronizer" "Go controller-runtime"
            helmRenderer = container "Helm Chart Renderer" "Renders embedded batch-gateway and async-processor Helm charts" "helm.sh/helm/v3"
            tlsProfileManager = container "TLS Profile Manager" "Reads OpenShift TLS profile and enforces cipher suites/min version; triggers graceful restart on changes" "Go"
            metricsController = container "Metrics Controller" "Provisions metrics Service, ServiceMonitor, PrometheusRule" "Go controller-runtime"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "External"
        openshiftAPIServer = softwareSystem "OpenShift APIServer" "Provides cluster TLS profile configuration" "External"
        certManager = softwareSystem "cert-manager" "Manages TLS certificate lifecycle" "External"
        gatewayAPI = softwareSystem "Gateway API" "Kubernetes-native traffic routing (HTTPRoute, ReferenceGrant)" "External"
        prometheusOperator = softwareSystem "prometheus-operator" "Manages Prometheus monitoring resources" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and alerting" "External"

        # Relationships
        platformOperator -> batchGatewayOperator "Creates LLMBatchGateway CR via kubectl"
        batchGatewayOperator -> kubernetesAPI "Watches CRs, creates/updates managed resources" "HTTPS/6443"
        batchGatewayOperator -> openshiftAPIServer "Reads TLS profile configuration" "HTTPS/6443"
        batchGatewayOperator -> certManager "Creates Certificate CRs for workload TLS" "Kubernetes API"
        batchGatewayOperator -> gatewayAPI "Creates HTTPRoutes and ReferenceGrants (conditional)" "Kubernetes API"
        batchGatewayOperator -> prometheusOperator "Creates ServiceMonitor and PrometheusRule (conditional)" "Kubernetes API"
        prometheus -> batchGatewayOperator "Scrapes metrics endpoint" "HTTPS/8443"

        # Internal relationships
        manager -> helmRenderer "Renders charts with CR spec + TLS values"
        manager -> tlsProfileManager "Reads cluster TLS profile at startup"
        manager -> metricsController "Manages observability resources"
    }

    views {
        systemContext batchGatewayOperator "SystemContext" {
            include *
            autoLayout
        }

        container batchGatewayOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
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
