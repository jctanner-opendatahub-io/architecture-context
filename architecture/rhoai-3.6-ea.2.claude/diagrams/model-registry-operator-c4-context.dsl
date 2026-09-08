workspace {
    model {
        user = person "Data Scientist / ML Engineer" "Creates and manages model registries for ML model metadata"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform and component lifecycle"

        modelRegistryOperator = softwareSystem "Model Registry Operator" "Kubernetes operator managing ModelRegistry, AIHub, and Catalog custom resources with per-instance deployments" {
            controllerManager = container "Controller Manager" "Multi-controller process managing three reconciliation loops" "Go Operator (controller-runtime 0.24.1)"
            mrReconciler = container "ModelRegistry Reconciler" "Provisions per-registry REST + PostgreSQL stacks with kube-rbac-proxy sidecars" "Go Controller"
            catalogReconciler = container "Catalog Reconciler" "Provisions model-catalog deployments with PostgreSQL backends" "Go Controller"
            aihubReconciler = container "AIHub Reconciler" "Orchestrates Catalog sub-resources as higher-level aggregation" "Go Controller"
            webhookServer = container "Webhook Server" "Validates, mutates, and converts ModelRegistry CRs" "Admission Webhook (HTTPS/9443)"
        }

        kubeAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External"
        gatewayAPI = softwareSystem "Gateway API" "Platform ingress via data-science-gateway" "External"
        openshiftRoutes = softwareSystem "OpenShift Routes" "OpenShift-native ingress for registry endpoints" "External"
        platformAuth = softwareSystem "ODH Platform Auth" "Centralized authentication configuration (services.platform.opendatahub.io)" "Internal RHOAI"
        componentManager = softwareSystem "ODH Component Manager" "Component lifecycle coordination (components.platform.opendatahub.io)" "Internal RHOAI"
        odhOperator = softwareSystem "ODH Operator" "Platform operator managing RHOAI component lifecycle" "Internal RHOAI"
        postgresql = softwareSystem "PostgreSQL" "Per-instance relational database for model metadata storage" "Managed by Operator"
        kubeRBACProxy = softwareSystem "kube-rbac-proxy" "Sidecar performing TokenReview/SAR authentication" "Sidecar"

        user -> modelRegistryOperator "Creates ModelRegistry CR via kubectl/API"
        platformAdmin -> odhOperator "Manages platform components"
        odhOperator -> modelRegistryOperator "Creates ModelRegistry CRs for component lifecycle"

        controllerManager -> kubeAPI "Watches CRDs, manages resources" "HTTPS/6443 TLS 1.2+"
        mrReconciler -> postgresql "Provisions per-registry PostgreSQL instances" "Internal"
        mrReconciler -> kubeRBACProxy "Deploys as sidecar on registry pods" "Internal"
        mrReconciler -> gatewayAPI "Creates HTTPRoutes for registry ingress" "HTTPS"
        mrReconciler -> openshiftRoutes "Creates Routes for registry ingress" "HTTPS"
        catalogReconciler -> postgresql "Provisions catalog PostgreSQL instance" "Internal"
        aihubReconciler -> catalogReconciler "Manages Catalog sub-resources" "Internal"

        controllerManager -> platformAuth "Watches Auth resources for config" "Kubernetes API"
        controllerManager -> componentManager "Watches ModelRegistries component status" "Kubernetes API"

        kubeRBACProxy -> kubeAPI "TokenReview and SubjectAccessReview" "HTTPS/6443 TLS 1.2+"

        webhookServer -> kubeAPI "Receives admission requests" "HTTPS/9443 TLS"
    }

    views {
        systemContext modelRegistryOperator "SystemContext" {
            include *
            autoLayout
        }

        container modelRegistryOperator "Containers" {
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
            element "Managed by Operator" {
                background #4a90e2
                color #ffffff
            }
            element "Sidecar" {
                background #f5a623
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
