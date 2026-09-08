workspace {
    model {
        user = person "Platform User" "Creates and manages data connections via DataConnectService CRs"
        client = person "API Client" "Consumes data connection REST and Arrow Flight APIs"

        dataConnectHub = softwareSystem "Data Connect Hub" "Kubernetes operator managing data connection lifecycle with REST and Arrow Flight services" {
            dcController = container "dc-controller-manager" "Reconciles DataConnectService, InitDataConnection, InitDataConnectionType CRs; manages service deployments and Gateway API routes" "Go controller-runtime Operator"
            restService = container "REST Service" "Tenant-scoped CRUD API for connection types and connections under /api/{version}/data/*" "Rust actix-web"
            flightService = container "Flight Service" "Apache Arrow Flight protocol access for high-throughput data transfer" "Rust tonic/arrow-flight"
            kubeRbacProxy = container "kube-rbac-proxy" "Sidecar performing Kubernetes TokenReview-based authentication with configurable audiences" "Go Sidecar"
            connectors = container "Backend Connectors" "Pluggable connector modules: PostgreSQL, Elasticsearch, Milvus, Neo4j, S3, SQLite, URI" "Rust Libraries"
        }

        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" "Platform"
        gatewayAPI = softwareSystem "Gateway API" "Gateway and HTTPRoute resources for ingress routing" "Platform"
        openshiftIngress = softwareSystem "OpenShift Ingress Config" "Cluster routing domain and ingress controller configuration" "Platform"

        postgresql = softwareSystem "PostgreSQL" "Relational database backend" "External Data Service"
        elasticsearch = softwareSystem "Elasticsearch" "Search and analytics engine backend" "External Data Service"
        milvus = softwareSystem "Milvus" "Vector database backend" "External Data Service"
        neo4j = softwareSystem "Neo4j" "Graph database backend" "External Data Service"
        s3 = softwareSystem "S3 Storage" "Object storage backend" "External Data Service"

        # Relationships
        user -> dataConnectHub "Creates DataConnectService CRs via kubectl/API"
        client -> kubeRbacProxy "Sends REST/Flight requests with Bearer Token" "HTTPS TLS 1.2+"
        kubeRbacProxy -> k8sAPI "TokenReview authentication" "HTTPS/6443"
        kubeRbacProxy -> restService "Forwards authenticated requests" "HTTP localhost"
        kubeRbacProxy -> flightService "Forwards authenticated requests" "gRPC localhost"

        dcController -> k8sAPI "Watches CRs, creates Deployments, Services, ConfigMaps, NetworkPolicies" "HTTPS/6443"
        dcController -> gatewayAPI "Creates/manages HTTPRoute resources" "HTTPS/6443"
        dcController -> openshiftIngress "Reads cluster routing domain" "HTTPS/6443"
        dcController -> restService "Syncs connection type definitions" "HTTP internal"

        restService -> connectors "Routes to appropriate backend connector"
        connectors -> postgresql "Queries/mutates data" "Backend-specific"
        connectors -> elasticsearch "Queries/mutates data" "Backend-specific"
        connectors -> milvus "Queries/mutates data" "Backend-specific"
        connectors -> neo4j "Queries/mutates data" "Backend-specific"
        connectors -> s3 "Reads/writes objects" "HTTPS"
    }

    views {
        systemContext dataConnectHub "SystemContext" {
            include *
            autoLayout
        }

        container dataConnectHub "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Platform" {
                background #999999
                color #ffffff
            }
            element "External Data Service" {
                background #f5a623
                color #ffffff
            }
            element "Person" {
                shape person
                background #4a90e2
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
