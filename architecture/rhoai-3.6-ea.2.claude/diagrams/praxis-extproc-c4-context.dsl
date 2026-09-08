workspace {
    model {
        client = person "External Client" "Sends inference requests to the MaaS gateway"

        praxisExtproc = softwareSystem "praxis-extproc" "Envoy ExtProc gRPC server executing Praxis AI filter pipelines for request/response mutation in the MaaS ingress gateway" {
            extprocServer = container "ExtProc gRPC Server" "Handles bidirectional gRPC ext_proc streams from Envoy, runs filter pipelines, returns header/body mutations" "Rust (tonic + tokio)" "Service"
            filterPipeline = container "Filter Pipeline" "Configurable chain of Praxis filters including AI-specific filters (e.g. model_to_header)" "praxis-filter + praxis-ai-filters" "Library"
            healthServer = container "Health Check Server" "gRPC health check for Kubernetes liveness/readiness probes" "tonic-health" "Service"
            metricsServer = container "Metrics Exporter" "Prometheus metrics HTTP endpoint exposing request counts, durations, immediate response counts" "hyper + metrics-exporter-prometheus" "Service"
            tlsLayer = container "TLS Layer" "OpenSSL-based TLS with mozilla_intermediate profile, ALPN h2, optional mTLS" "openssl crate" "Library"

            extprocServer -> filterPipeline "Executes filter chain on each request/response"
            tlsLayer -> extprocServer "Secures gRPC connections"
        }

        envoyGateway = softwareSystem "Istio/Envoy Gateway" "MaaS default gateway (maas-default-gateway) in openshift-ingress namespace" "External"
        kuadrant = softwareSystem "Kuadrant" "Authorization WasmPlugin in Envoy filter chain" "External"
        k8sAPI = softwareSystem "Kubernetes API Server" "Provides ConfigMaps, Secrets, and inference.opendatahub.io CRDs" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"

        client -> envoyGateway "Sends inference HTTP requests" "HTTPS/443"
        envoyGateway -> praxisExtproc "Sends ext_proc gRPC streams (pre-auth and post-auth)" "gRPC/9004, TLS SIMPLE"
        kuadrant -> envoyGateway "Provides authorization decisions in filter chain" "WasmPlugin"
        praxisExtproc -> k8sAPI "Reads ConfigMaps, Secrets, ExternalProviders, ExternalModels" "HTTPS/443, SA Token"
        prometheus -> praxisExtproc "Scrapes operational metrics" "HTTP/9090"
    }

    views {
        systemContext praxisExtproc "SystemContext" {
            include *
            autoLayout
        }

        container praxisExtproc "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Service" {
                background #4a90e2
                color #ffffff
            }
            element "Library" {
                background #6c5ce7
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
        }
    }
}
