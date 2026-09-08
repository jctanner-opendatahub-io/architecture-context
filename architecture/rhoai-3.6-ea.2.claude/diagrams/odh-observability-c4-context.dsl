workspace {
    model {
        datascientist = person "Data Scientist" "Queries metrics for model serving workloads"
        platformadmin = person "Platform Admin" "Manages RHOAI observability configuration"

        odhObservability = softwareSystem "odh-observability" "Kubernetes operator managing the observability stack for Red Hat OpenShift AI — metrics collection, tracing, log forwarding, and alerting" {
            manager = container "Manager" "controller-runtime operator process reconciling the Monitoring CR" "Go Binary (FIPS)"
            webhookServer = container "Webhook Server" "Mutating admission webhook injecting monitoring labels into PodMonitors and ServiceMonitors" "Go, :9443/TCP TLS"
            clusterProxy = container "Cluster Proxy" "kube-rbac-proxy enforcing cluster-wide SubjectAccessReview for Prometheus metrics" "kube-rbac-proxy, :8443/TCP"
            namespaceProxy = container "Namespace Proxy" "kube-rbac-proxy + prom-label-proxy enforcing namespace-scoped SubjectAccessReview for Prometheus metrics" "kube-rbac-proxy + prom-label-proxy, :8443/TCP"
        }

        prometheusOperator = softwareSystem "prometheus-operator" "Manages Prometheus MonitoringStack CRs" "External"
        prometheusOperated = softwareSystem "prometheus-operated" "Prometheus query engine serving collected metrics" "External"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource CRUD, watches, TokenReview, SubjectAccessReview" "External"
        openshiftAPIServer = softwareSystem "OpenShift APIServer" "Provides cluster-wide TLSSecurityProfile configuration" "External"
        odhPlatformUtils = softwareSystem "odh-platform-utilities" "Shared Go library for deployment, platform detection, and manifest rendering" "Internal ODH"
        tempoOperator = softwareSystem "Tempo Operator" "Manages distributed tracing backends" "External"
        lokiStack = softwareSystem "LokiStack" "Log aggregation for usage-log forwarding" "External"

        # Relationships
        platformadmin -> odhObservability "Creates/updates Monitoring CR via kubectl"
        datascientist -> clusterProxy "Queries cluster-wide metrics" "HTTPS/443 via Route"
        datascientist -> namespaceProxy "Queries namespace-scoped metrics" "HTTPS/443 via Route"

        manager -> k8sAPI "Watches Monitoring CR + 15 resource types, server-side apply" "HTTPS/6443"
        manager -> openshiftAPIServer "Reads TLSSecurityProfile" "HTTPS"
        manager -> odhPlatformUtils "Uses deployer and platform detection" "Go library"
        manager -> prometheusOperator "Creates MonitoringStack and PrometheusRule CRs" "HTTPS"

        clusterProxy -> k8sAPI "TokenReview + SubjectAccessReview (metrics.k8s.io/nodes:get)" "HTTPS/6443"
        clusterProxy -> prometheusOperated "Proxies authorized metric queries" "HTTP/9090, mTLS"

        namespaceProxy -> k8sAPI "TokenReview + SubjectAccessReview (metrics.k8s.io/pods, ns-scoped)" "HTTPS/6443"
        namespaceProxy -> prometheusOperated "Proxies namespace-filtered queries" "HTTP/9090, mTLS"

        webhookServer -> k8sAPI "Receives admission requests, returns mutated resources" "HTTPS/9443"

        odhObservability -> tempoOperator "Configures TempoStack CR for distributed tracing" "Kubernetes API"
        odhObservability -> lokiStack "Configures ClusterLogForwarder for usage-log forwarding" "Kubernetes API"
    }

    views {
        systemContext odhObservability "SystemContext" {
            include *
            autoLayout
        }

        container odhObservability "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal ODH" {
                background #7ed321
                color #000000
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
        }
    }
}
