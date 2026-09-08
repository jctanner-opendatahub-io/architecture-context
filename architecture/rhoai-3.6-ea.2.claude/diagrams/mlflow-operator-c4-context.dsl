workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and manages MLflow tracking server instances for experiment tracking"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform components and configuration"

        mlflowOperator = softwareSystem "mlflow-operator" "Kubernetes operator managing MLflow tracking server lifecycle on RHOAI" {
            mlflowReconciler = container "MLflowReconciler" "Primary controller: reconciles MLflow CRs, renders Helm charts, manages owned resources" "Go controller-runtime"
            mlflowOperatorReconciler = container "MLflowOperatorReconciler" "Platform component controller: bridges RHOAI component lifecycle to MLflow instances" "Go controller-runtime"
            namespaceRBACReconciler = container "NamespaceRBACReconciler" "RBAC propagation controller: propagates view/edit RoleBindings to workspace namespaces" "Go controller-runtime"
            helmEngine = container "Helm Chart Engine" "Renders embedded charts/mlflow templates into Kubernetes manifests" "Helm v3"
            metricsServer = container "Metrics Server" "Exposes :8443/metrics with TLS and TokenReview/SAR authentication" "controller-runtime"
            healthProbes = container "Health Probes" "Exposes :8081/healthz and :8081/readyz for Kubernetes probes" "controller-runtime"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "External"
        gatewayAPI = softwareSystem "Gateway API" "HTTPRoute-based routing for external access to MLflow servers" "External"
        openshiftConsole = softwareSystem "OpenShift Console" "Web console with ConsoleLink integration for MLflow UI access" "External"
        prometheusOperator = softwareSystem "prometheus-operator" "Monitoring via ServiceMonitor resources for metrics collection" "External"
        rhoaiPlatform = softwareSystem "RHOAI Platform" "Platform-level component and auth management (MLflowOperator, Auth CRs)" "Internal RHOAI"

        dataScientist -> mlflowOperator "Creates MLflow CR via kubectl/API"
        platformAdmin -> rhoaiPlatform "Configures MLflowOperator CR and Auth CR"
        rhoaiPlatform -> mlflowOperator "Provides MLflowOperator CR and Auth CR" "Kubernetes API"

        mlflowReconciler -> helmEngine "Renders chart templates"
        helmEngine -> kubernetesAPI "Applies Deployments, Services, PVCs, Jobs, NetworkPolicies" "HTTPS/6443"
        mlflowReconciler -> kubernetesAPI "Watches MLflow, MLflowConfig CRs; manages owned resources" "HTTPS/6443"
        mlflowReconciler -> gatewayAPI "Creates HTTPRoutes for external routing (conditional)" "HTTPS"
        mlflowReconciler -> openshiftConsole "Creates ConsoleLinks for UI integration (conditional)" "HTTPS"
        mlflowReconciler -> prometheusOperator "Creates ServiceMonitors for metrics (conditional)" "HTTPS"
        mlflowOperatorReconciler -> kubernetesAPI "Watches MLflowOperator CR; bridges platform lifecycle" "HTTPS/6443"
        namespaceRBACReconciler -> kubernetesAPI "Watches Auth CR, Namespaces; propagates RoleBindings" "HTTPS/6443"
    }

    views {
        systemContext mlflowOperator "SystemContext" {
            include *
            autoLayout
        }

        container mlflowOperator "Containers" {
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
