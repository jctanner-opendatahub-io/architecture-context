workspace {
    model {
        admin = person "Cluster Administrator" "Deploys and configures RHOAI platform dependencies"

        odhGitops = softwareSystem "odh-gitops" "GitOps configuration repository packaging Helm charts and Kustomize overlays for RHOAI platform dependency installation" {
            openshiftChart = container "rhai-on-openshift-chart" "Helm chart for OpenShift OLM-based operator installation" "Helm Chart"
            xksChart = container "rhai-on-xks-chart" "Helm chart for non-OpenShift Kubernetes (EKS, AKS, CoreWeave)" "Helm Chart"
            kustomizeDeps = container "kustomize-dependencies" "Operator subscription composition overlays" "Kustomize"
            kustomizeConfig = container "kustomize-configurations" "Post-install operator configuration overlays" "Kustomize"
        }

        upstream = softwareSystem "opendatahub-io/odh-gitops" "Upstream open source repository" "External"

        # Target platforms
        openshift = softwareSystem "OpenShift Cluster" "Target OpenShift platform with OLM" "Platform" {
            olm = container "OLM" "Operator Lifecycle Manager for installing operators" "OpenShift"
            apiServer = container "Kubernetes API Server" "Cluster control plane" "Kubernetes"
        }

        xksCluster = softwareSystem "Non-OpenShift Kubernetes" "AWS EKS, Azure AKS, or CoreWeave cluster" "Platform"

        # Provisioned operators - Security
        certManager = softwareSystem "cert-manager" "TLS certificate lifecycle management" "Provisioned Operator"
        kuadrant = softwareSystem "RHCL Operator (Kuadrant)" "API gateway, authorization (Authorino), and rate limiting" "Provisioned Operator"

        # Provisioned operators - Scheduling
        kueue = softwareSystem "Kueue Operator" "Job scheduling and resource quota management" "Provisioned Operator"
        jobset = softwareSystem "JobSet Operator" "Multi-pod job orchestration" "Provisioned Operator"
        lws = softwareSystem "LeaderWorkerSet" "Leader-worker topology for distributed workloads" "Provisioned Operator"

        # Provisioned operators - Observability
        otel = softwareSystem "OpenTelemetry Operator" "Distributed tracing instrumentation" "Provisioned Operator"
        tempo = softwareSystem "Tempo Operator" "Trace storage backend" "Provisioned Operator"
        clusterObs = softwareSystem "Cluster Observability Operator" "Cluster monitoring and metrics" "Provisioned Operator"

        # Provisioned operators - Network (XKS only)
        sail = softwareSystem "Sail Operator (Istio)" "Service mesh for non-OpenShift deployments" "XKS Only"
        gatewayAPI = softwareSystem "Gateway API CRDs" "Kubernetes Gateway API resource definitions" "XKS Only"

        # Provisioned operators - GPU (optional)
        nfd = softwareSystem "Node Feature Discovery" "GPU/accelerator node detection" "Optional"
        nvidia = softwareSystem "NVIDIA GPU Operator" "GPU device plugin and driver management" "Optional"

        # Relationships
        upstream -> odhGitops "Synced via auto-merge" "git"
        admin -> odhGitops "Deploys platform dependencies using" "helm/kustomize"

        odhGitops -> openshift "Installs operators on" "OLM Subscriptions"
        odhGitops -> xksCluster "Installs operators on" "Helm sub-charts"

        odhGitops -> certManager "Provisions" "OLM Subscription / Helm"
        odhGitops -> kuadrant "Provisions and configures" "OLM Subscription / Helm"
        odhGitops -> kueue "Provisions" "OLM Subscription / Helm"
        odhGitops -> jobset "Provisions" "OLM Subscription / Helm"
        odhGitops -> lws "Provisions" "OLM Subscription / Helm"
        odhGitops -> otel "Provisions" "OLM Subscription"
        odhGitops -> tempo "Provisions" "OLM Subscription"
        odhGitops -> clusterObs "Provisions" "OLM Subscription"
        odhGitops -> sail "Provisions (XKS only)" "Helm sub-chart"
        odhGitops -> gatewayAPI "Provisions (XKS only)" "Helm sub-chart"
        odhGitops -> nfd "Provisions (optional)" "OLM Subscription"
        odhGitops -> nvidia "Provisions (optional)" "OLM Subscription"

        certManager -> kuadrant "Issues TLS certs for" "authorino-server-cert"
    }

    views {
        systemContext odhGitops "SystemContext" {
            include *
            autoLayout
        }

        container odhGitops "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Provisioned Operator" {
                background #7ed321
                color #ffffff
            }
            element "Platform" {
                background #4a90e2
                color #ffffff
            }
            element "XKS Only" {
                background #9673a6
                color #ffffff
            }
            element "Optional" {
                background #b85450
                color #ffffff
            }
        }
    }
}
