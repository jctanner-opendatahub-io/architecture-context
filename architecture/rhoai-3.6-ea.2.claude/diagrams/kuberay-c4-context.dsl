workspace {
    model {
        user = person "Data Scientist / ML Engineer" "Creates and manages Ray clusters, jobs, and services for distributed ML workloads"

        kuberay = softwareSystem "KubeRay Operator" "Kubernetes operator managing the lifecycle of Ray clusters, jobs, and services on OpenShift with OAuth/OIDC auth and mTLS" {
            rayClusterCtrl = container "RayCluster Controller" "Reconciles RayCluster CRs, creates Pods, Services, Secrets" "Go controller-runtime"
            rayJobCtrl = container "RayJob Controller" "Reconciles RayJob CRs, manages batch Jobs and ephemeral clusters" "Go controller-runtime"
            rayServiceCtrl = container "RayService Controller" "Reconciles RayService CRs with blue-green rollout" "Go controller-runtime"
            rayCronJobCtrl = container "RayCronJob Controller" "Reconciles RayCronJob CRs, creates scheduled RayJobs" "Go controller-runtime"
            authCtrl = container "Authentication Controller" "Injects kube-rbac-proxy sidecar for OAuth/OIDC dashboard auth" "Go controller-runtime"
            mtlsCtrl = container "mTLS Controller" "Provisions cert-manager Certificates and Issuers for Ray node mTLS" "Go controller-runtime"
            networkPolicyCtrl = container "NetworkPolicy Controller" "Creates per-RayCluster NetworkPolicies for pod isolation" "Go controller-runtime"
            webhookServer = container "Webhook Server" "Mutating and validating admission webhooks for Ray CRDs" "HTTPS"
            metricsServer = container "Metrics Server" "Prometheus metrics endpoint on :8080" "HTTP"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster API for resource management" "External"
        certManager = softwareSystem "cert-manager" "X.509 certificate lifecycle management" "Platform"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "Platform"
        gatewayAPI = softwareSystem "Gateway API" "Kubernetes Gateway API for traffic routing" "Platform"
        openshiftConfig = softwareSystem "OpenShift Cluster Configuration" "Cluster-wide TLS profile and API server settings" "Platform"
        kubeRBACProxy = softwareSystem "kube-rbac-proxy" "OAuth/OIDC authentication proxy sidecar for Ray Dashboard" "Sidecar"

        user -> kuberay "Creates RayCluster, RayJob, RayService, RayCronJob CRs" "kubectl / YAML"
        kuberay -> kubernetesAPI "CRUD on Pods, Services, Secrets, Jobs, Roles, etc." "HTTPS/6443, SA token"
        kuberay -> certManager "Creates Issuers and Certificates for mTLS" "Kubernetes API"
        kuberay -> gatewayAPI "Creates HTTPRoutes and ReferenceGrants for dashboard access" "Kubernetes API"
        kuberay -> openshiftConfig "Reads cluster TLS security profile" "Kubernetes API"
        prometheus -> kuberay "Scrapes /metrics endpoint" "HTTP/8080"
        kuberay -> kubeRBACProxy "Injects sidecar into Ray head pods for dashboard auth" "Pod spec mutation"
    }

    views {
        systemContext kuberay "SystemContext" {
            include *
            autoLayout
        }

        container kuberay "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Platform" {
                background #7ed321
                color #000000
            }
            element "Sidecar" {
                background #e74c3c
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
        }
    }
}
