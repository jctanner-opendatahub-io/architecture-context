workspace {
    model {
        user = person "Data Scientist / MLOps Engineer" "Creates and manages model serving workloads via InferenceService CRs"
        admin = person "Platform Admin" "Configures RHOAI platform via DataScienceCluster and NIM Account CRs"

        odhModelController = softwareSystem "odh-model-controller" "Kubernetes operator that orchestrates model serving infrastructure, managing InferenceService lifecycle, Gateway API routing, NIM integration, and admission webhooks" {
            controllerManager = container "Controller Manager" "Hosts 10 reconciliation controllers and 8 admission webhooks for KServe resources" "Go / controller-runtime" "Deployment"
            modelServingAPI = container "model-serving-api" "REST API for gateway discovery and LLM sample retrieval" "Go / net/http" "Deployment"
        }

        kubeAPI = softwareSystem "Kubernetes API Server" "Cluster API for resource CRUD, watch streams, and admission control" "External"
        kserve = softwareSystem "KServe" "Model serving platform providing InferenceService, ServingRuntime, and InferenceGraph CRDs" "Internal RHOAI"
        istio = softwareSystem "Istio Service Mesh" "Service mesh for traffic management; operator manages EnvoyFilter resources" "External"
        gatewayAPI = softwareSystem "Gateway API" "Kubernetes Gateway API for ingress routing; operator manages Gateway and HTTPRoute resources" "External"
        kuadrant = softwareSystem "Kuadrant" "API gateway policy engine; operator manages AuthPolicy resources for authorization" "External"
        keda = softwareSystem "KEDA" "Event-driven autoscaler; operator manages TriggerAuthentication resources" "External"
        prometheusOperator = softwareSystem "Prometheus Operator" "Monitoring stack; operator manages ServiceMonitor and PodMonitor resources" "External"
        serviceCa = softwareSystem "OpenShift service-ca" "Provisions TLS certificates for webhook, metrics, and API services" "External"
        otel = softwareSystem "OpenTelemetry Collector" "Distributed tracing collection via OTLP/gRPC" "External"
        dsc = softwareSystem "DataScienceCluster / DSCInitialization" "RHOAI platform configuration CRs indicating enabled components" "Internal RHOAI"
        openshiftAPI = softwareSystem "OpenShift APIServer CR" "Cluster-wide TLS security profile configuration" "External"
        nimAPI = softwareSystem "NVIDIA NIM" "NVIDIA NIM account management for GPU-accelerated inference" "External"

        user -> odhModelController "Creates InferenceService, LLMInferenceService, InferenceGraph CRs via kubectl"
        admin -> odhModelController "Configures NIM Accounts and platform settings"
        user -> modelServingAPI "Queries gateway discovery API" "HTTPS/443, Bearer token"

        controllerManager -> kubeAPI "Watches CRs and creates supporting resources" "HTTPS/6443, ServiceAccount token"
        controllerManager -> kserve "Reconciles InferenceService, ServingRuntime, InferenceGraph" "Kubernetes API"
        controllerManager -> istio "Creates EnvoyFilter resources" "Kubernetes API"
        controllerManager -> gatewayAPI "Creates Gateway and HTTPRoute resources" "Kubernetes API"
        controllerManager -> kuadrant "Creates AuthPolicy resources" "Kubernetes API"
        controllerManager -> keda "Creates TriggerAuthentication resources" "Kubernetes API"
        controllerManager -> prometheusOperator "Creates ServiceMonitor and PodMonitor resources" "Kubernetes API"
        controllerManager -> otel "Exports traces" "OTLP/gRPC, TLS"

        modelServingAPI -> kubeAPI "Lists Gateways, validates tokens via SSAR" "HTTPS/6443, Bearer forwarding"
        modelServingAPI -> otel "Exports traces" "OTLP/gRPC, TLS"

        serviceCa -> controllerManager "Provisions TLS certificates for webhook and metrics"
        serviceCa -> modelServingAPI "Provisions TLS certificate for API server"

        dsc -> controllerManager "Platform component enablement state" "CRD Watch"
        openshiftAPI -> controllerManager "Cluster TLS profile (cipher suites, protocol versions)" "CRD Watch"
    }

    views {
        systemContext odhModelController "SystemContext" {
            include *
            autoLayout
        }

        container odhModelController "Containers" {
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
            element "Deployment" {
                shape RoundedBox
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
        }
    }
}
