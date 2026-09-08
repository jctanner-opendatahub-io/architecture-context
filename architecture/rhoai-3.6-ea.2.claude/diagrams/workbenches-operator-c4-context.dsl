workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and manages notebook workbenches for ML development"
        platformAdmin = person "Platform Administrator" "Manages RHOAI platform components and configuration"

        workbenchesOperator = softwareSystem "Workbenches Operator" "Manages the lifecycle of Kubeflow Notebook workbenches within Red Hat OpenShift AI" {
            controller = container "WorkbenchesReconciler" "Reconciles Workbenches CR, applies upstream manifests via server-side apply" "Go controller-runtime"
            webhookServer = container "Webhook Server" "Mutating admission webhooks for notebook pods (connection injection, hardware profile)" "Go HTTPS :9443"
            platformConfig = container "PlatformConfig Reader" "Watches odh-workbenches-config ConfigMap for distribution and version handshake" "Go informer"
            tlsManager = container "TLS Manager" "Manages TLS configuration using OpenShift TLS profile with Mozilla Intermediate fallback" "Go crypto/tls"
            certEnsurer = container "Certificate Ensurer" "Reconciles webhook TLS certificates from service-ca or cert-manager" "Go periodic reconciler"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External"
        platformOrchestrator = softwareSystem "Platform Orchestrator" "RHOAI/ODH orchestrator that manages component lifecycle" "Internal RHOAI"
        certManager = softwareSystem "cert-manager" "Automated TLS certificate management" "External"
        serviceCA = softwareSystem "OpenShift service-ca" "OpenShift service serving certificate signer" "External"
        kubeflowNotebooks = softwareSystem "Kubeflow Notebook Controller" "Manages notebook pod lifecycle" "Managed Operand"
        hardwareProfiles = softwareSystem "HardwareProfile CRDs" "Defines compute resource profiles for workbenches" "Internal RHOAI"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"

        # User interactions
        dataScientist -> kubeflowNotebooks "Creates notebook workbenches via" "kubectl / Dashboard"
        platformAdmin -> platformOrchestrator "Configures RHOAI components via" "DSC/DSCI CRs"

        # Platform orchestrator interactions
        platformOrchestrator -> workbenchesOperator "Creates Workbenches CR with projected fields" "Kubernetes API"
        platformOrchestrator -> workbenchesOperator "Writes odh-workbenches-config ConfigMap" "Kubernetes API"

        # Operator internal flows
        controller -> webhookServer "Configures webhook registrations" "In-process"
        controller -> platformConfig "Reads platform configuration" "In-process"
        controller -> tlsManager "Gets TLS config for webhook server" "In-process"
        controller -> certEnsurer "Ensures webhook certificates exist" "In-process"

        # Operator external interactions
        workbenchesOperator -> kubernetesAPI "CRUD operations on owned operands" "HTTPS/6443 SA Token"
        workbenchesOperator -> kubeflowNotebooks "Deploys and manages via server-side apply" "Kubernetes API"
        workbenchesOperator -> hardwareProfiles "Reads HardwareProfile CRs for webhook injection" "Kubernetes API"

        # Certificate providers
        serviceCA -> workbenchesOperator "Provisions webhook TLS certificates" "kubernetes.io/tls Secret"
        certManager -> workbenchesOperator "Fallback certificate provisioning" "Certificate CR"

        # Admission flow
        kubernetesAPI -> workbenchesOperator "Sends admission requests for notebook CREATE/UPDATE" "HTTPS/443 → 9443"

        # Monitoring
        prometheus -> workbenchesOperator "Scrapes metrics" "HTTPS/8443 TokenReview+SAR"
    }

    views {
        systemContext workbenchesOperator "SystemContext" {
            include *
            autoLayout
        }

        container workbenchesOperator "Containers" {
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
            element "Managed Operand" {
                background #4a90e2
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
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
