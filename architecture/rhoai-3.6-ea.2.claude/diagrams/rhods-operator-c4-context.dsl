workspace {
    model {
        admin = person "Cluster Admin" "Manages RHOAI platform installation and configuration"
        datascientist = person "Data Scientist" "Consumes RHOAI platform services"

        rhodsOperator = softwareSystem "rhods-operator" "Central lifecycle operator for Red Hat OpenShift AI - manages installation, configuration, and reconciliation of platform components" {
            manager = container "/manager" "Main operator binary with DAG-based controller registration for components, services, and modules" "Go Controller-Runtime Operator"
            cloudmanager = container "cloudmanager" "Multi-cloud Kubernetes engine provisioning for AWS, Azure, CoreWeave" "Go CLI"
            webhookServer = container "Webhook Server" "Validates and mutates DataScienceCluster, DSCInitialization, HardwareProfile, AcceleratorProfile CRs; handles CRD version conversion" "Go (port 9443/TLS)"
            metricsServer = container "Metrics Server" "Exposes Prometheus metrics with optional RBAC-based auth" "Go (port 8443/TLS)"
            gatewayController = container "Gateway Service Controller" "Creates full ingress chain: Gateway API, kube-auth-proxy, Routes, EnvoyFilters, DestinationRules, NetworkPolicies" "Go Controller"
            authController = container "Auth Service Controller" "Manages namespace-scoped RBAC for admin and allowed groups; watches models-as-a-service and kuadrant-system namespaces" "Go Controller"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster API server for resource operations" "External"
        istio = softwareSystem "Istio Service Mesh" "Service mesh for traffic management, mTLS, EnvoyFilters, DestinationRules" "External"
        gatewayAPI = softwareSystem "Gateway API" "Kubernetes Gateway API for platform ingress routing" "External"
        certManager = softwareSystem "OpenShift service-ca" "Provisions and rotates TLS certificates for webhooks and metrics" "External"
        prometheusOp = softwareSystem "prometheus-operator" "Manages Prometheus monitoring resources (ServiceMonitors, PodMonitors, PrometheusRules)" "External"

        kserve = softwareSystem "KServe" "Model serving infrastructure" "Internal RHOAI"
        modelRegistry = softwareSystem "Model Registry" "Model metadata and artifact registry" "Internal RHOAI"
        feast = softwareSystem "Feast" "Feature store for ML features" "Internal RHOAI"
        dsPipelines = softwareSystem "Data Science Pipelines" "ML pipeline orchestration" "Internal RHOAI"
        dashboard = softwareSystem "ODH Dashboard" "Web UI for RHOAI platform" "Internal RHOAI"
        kuadrant = softwareSystem "Kuadrant" "API gateway policy engine" "Internal RHOAI"
        maas = softwareSystem "Models-as-a-Service" "MaaS subsystem for model hosting" "Internal RHOAI"

        admin -> rhodsOperator "Creates DataScienceCluster and DSCInitialization CRs via kubectl"
        datascientist -> dashboard "Accesses RHOAI platform UI"

        rhodsOperator -> k8sAPI "CRUD operations on cluster resources" "HTTPS/6443, TLS 1.2+, ServiceAccount token"
        rhodsOperator -> istio "Creates EnvoyFilters and DestinationRules (dynamic guard)" "Kubernetes API"
        rhodsOperator -> gatewayAPI "Creates Gateway and HTTPRoute resources" "Kubernetes API"
        rhodsOperator -> prometheusOp "Owns PodMonitors, PrometheusRules, ServiceMonitors" "Kubernetes API"

        rhodsOperator -> kserve "Manages KServe component lifecycle; watches InferenceService CRs" "Kubernetes API"
        rhodsOperator -> modelRegistry "Manages ModelRegistry instances via CRD CRUD" "Kubernetes API"
        rhodsOperator -> feast "Watches FeatureStore CRs for feature store state" "Kubernetes API"
        rhodsOperator -> dsPipelines "Manages DataSciencePipelines component lifecycle" "Kubernetes API"
        rhodsOperator -> kuadrant "Auth controller watches kuadrant-system namespace for RBAC" "Kubernetes API"
        rhodsOperator -> maas "Auth controller watches models-as-a-service namespace; uses maas-controller library" "Kubernetes API + Go library"

        k8sAPI -> rhodsOperator "Sends admission requests to webhook server" "HTTPS/9443, TLS (service-ca cert)"
        certManager -> rhodsOperator "Provisions TLS certificates for webhook and metrics" "Kubernetes Secret"
    }

    views {
        systemContext rhodsOperator "SystemContext" {
            include *
            autoLayout
        }

        container rhodsOperator "Containers" {
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
                color #000000
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
