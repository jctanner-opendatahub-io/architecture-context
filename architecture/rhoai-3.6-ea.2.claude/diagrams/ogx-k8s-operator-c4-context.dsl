workspace {
    model {
        platformOperator = person "Platform Operator" "Manages RHOAI/ODH platform components"
        dataScientist = person "Data Scientist" "Creates and deploys OGX inference servers"

        ogxOperator = softwareSystem "ogx-k8s-operator" "Manages lifecycle of OGX (LlamaStack) inference servers via CRD-driven deployment, autoscaling, networking, and admission validation" {
            ogxModule = container "ogx-module" "ODH platform component controller; reconciles cluster-scoped OGX CR to deploy the operator" "Go controller-runtime"
            ogxServerController = container "OGXServer Controller" "Reconciles OGXServer CRs into deployment stacks (Deployment, Service, HPA, PDB, NetworkPolicy, Ingress, ConfigMap, PVC)" "Go controller-runtime"
            validatingWebhook = container "Validating Webhook" "Validates OGXServer CREATE/UPDATE requests; FailurePolicy=Fail" "Go HTTPS/9443"
            metricsServer = container "Metrics Server" "Exposes Prometheus metrics with TokenReview+SAR authentication" "Go HTTPS/8443"
            configgen = container "configgen" "Generates default OGX server configurations" "Go CLI"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External"
        prometheusOp = softwareSystem "prometheus-operator" "Manages Prometheus monitoring stack via ServiceMonitor and PrometheusRule CRDs" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and alerting" "External"
        odhPlatformUtils = softwareSystem "odh-platform-utilities" "Platform detection, manifest rendering, and deployment helpers" "Internal ODH"
        openShiftAPI = softwareSystem "OpenShift API" "Provides TLS profiles and platform configuration" "External"

        # Relationships
        platformOperator -> ogxOperator "Creates OGX CR to deploy operator"
        dataScientist -> ogxOperator "Creates OGXServer CRs via kubectl"

        ogxModule -> k8sAPI "Renders and applies kustomize manifests (CRDs, RBAC, webhooks)" "HTTPS/6443"
        ogxModule -> odhPlatformUtils "Uses for manifest rendering and platform detection" "Go library"
        ogxServerController -> k8sAPI "Creates/manages Deployments, Services, HPAs, PDBs, NetworkPolicies, Ingresses" "HTTPS/6443"
        ogxServerController -> prometheusOp "Creates ServiceMonitor and PrometheusRule CRDs" "HTTPS/6443"
        validatingWebhook -> k8sAPI "Receives admission reviews" "HTTPS/9443"
        ogxOperator -> openShiftAPI "Reads TLS profile for cipher suite configuration" "HTTPS/6443"

        prometheus -> metricsServer "Scrapes operator metrics" "HTTPS/8443"
    }

    views {
        systemContext ogxOperator "SystemContext" {
            include *
            autoLayout
        }

        container ogxOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
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
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
