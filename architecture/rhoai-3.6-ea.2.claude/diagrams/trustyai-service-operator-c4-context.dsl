workspace {
    model {
        user = person "Data Scientist / ML Engineer" "Creates TrustyAI services, evaluation jobs, and guardrails configurations"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform and operator configuration"

        trustyaiOperator = softwareSystem "TrustyAI Service Operator" "Multi-controller Kubernetes operator managing AI model trustworthiness, evaluation, and guardrails services" {
            manager = container "Manager" "controller-runtime operator process running seven reconcilers" "Go 1.26, controller-runtime 0.23.3"
            trustyaiServiceCtrl = container "TrustyAIService Reconciler" "Manages per-namespace TrustyAI deployments with TLS and kube-rbac-proxy" "Go Controller"
            evalHubCtrl = container "EvalHub Reconciler" "Orchestrates model evaluation across tenant namespaces" "Go Controller"
            gorchCtrl = container "GuardrailsOrchestrator Reconciler" "Coordinates guardrails with model serving endpoints" "Go Controller"
            lmevalCtrl = container "LMEvalJob Reconciler" "Manages evaluation job pods with PVC and Kueue" "Go Controller"
            nemoCtrl = container "NemoGuardrails Reconciler" "NVIDIA NeMo guardrails support with Gateway API" "Go Controller"
            trustyaiModCtrl = container "TrustyAI Module Reconciler" "Platform-level TrustyAI lifecycle management" "Go Controller"
            conversionWebhook = container "Conversion Webhook" "CRD version conversion at /convert" "HTTPS :9443"
            metricsServer = container "Metrics Server" "Prometheus-compatible metrics with conditional K8s auth" "HTTPS"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External"
        openshiftAPIServer = softwareSystem "OpenShift APIServer" "Cluster-wide TLS profile configuration" "External"
        odhOperator = softwareSystem "OpenDataHub Operator" "Platform operator providing trustyai-dsc-config ConfigMap" "Internal RHOAI"
        kserve = softwareSystem "KServe" "Model serving platform providing InferenceService resources" "Internal RHOAI"
        prometheusOperator = softwareSystem "Prometheus Operator" "Monitoring operator managing ServiceMonitor CRDs" "Internal RHOAI"
        kueue = softwareSystem "Kueue" "Batch scheduling for evaluation workloads" "Internal RHOAI"
        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing and metrics collection" "External"
        prometheus = softwareSystem "Prometheus" "Metrics storage and alerting" "Internal RHOAI"
        istio = softwareSystem "Istio Service Mesh" "VirtualService routing for TrustyAI services" "External"
        odhPlatformUtils = softwareSystem "odh-platform-utilities" "Go library for platform detection and manifest rendering" "Internal RHOAI"

        user -> trustyaiOperator "Creates TrustyAIService, EvalHub, LMEvalJob, GuardrailsOrchestrator, NemoGuardrails CRs" "kubectl / RHOAI Dashboard"
        platformAdmin -> odhOperator "Configures trustyai-dsc-config" "kubectl"

        trustyaiOperator -> kubernetesAPI "CRUD operations on Deployments, Services, Secrets, RBAC" "HTTPS/6443, SA Token"
        trustyaiOperator -> openshiftAPIServer "Reads TLS profile (10s timeout)" "Kubernetes API"
        trustyaiOperator -> odhOperator "Reads trustyai-dsc-config ConfigMap" "Kubernetes API"
        trustyaiOperator -> kserve "Watches InferenceService for guardrails coordination" "Kubernetes API"
        trustyaiOperator -> prometheusOperator "Creates/manages ServiceMonitor resources" "Kubernetes API"
        trustyaiOperator -> kueue "Creates Workload resources for batch scheduling" "Kubernetes API"
        trustyaiOperator -> otelCollector "Exports traces and metrics" "OTLP gRPC/HTTP"
        trustyaiOperator -> istio "Creates VirtualService for external access" "Kubernetes API"
        prometheus -> trustyaiOperator "Scrapes metrics endpoint" "HTTPS, Token Delegation"

        manager -> trustyaiServiceCtrl "Manages"
        manager -> evalHubCtrl "Manages"
        manager -> gorchCtrl "Manages"
        manager -> lmevalCtrl "Manages"
        manager -> nemoCtrl "Manages"
        manager -> trustyaiModCtrl "Manages"
    }

    views {
        systemContext trustyaiOperator "SystemContext" {
            include *
            autoLayout
        }

        container trustyaiOperator "Containers" {
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
