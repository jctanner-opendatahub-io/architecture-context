workspace {
    model {
        dataScientist = person "Data Scientist" "Creates, versions, and deploys ML models"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform and model registry configuration"

        modelRegistry = softwareSystem "Model Registry" "Centralized metadata store for ML models, versions, and artifacts" {
            registryProxy = container "model-registry" "HTTP proxy for model metadata CRUD backed by GORM" "Go, Port 8080" "FIPS"
            bffServer = container "BFF Server" "UI backend proxy handling auth, K8s resource operations, and registry API forwarding" "Go, Port 4000"
            controller = container "controller-controller-manager" "controller-runtime operator that watches KServe InferenceService and syncs serving state" "Go, controller-runtime"
            asyncUploadJob = container "async-upload Job" "Copies models between storage backends (S3, OCI), performs Sigstore signing, registers results" "Python, boto3, ORAS"
            database = container "Database" "Relational model metadata store" "PostgreSQL / MySQL" "Database"
        }

        istio = softwareSystem "Istio Service Mesh" "Traffic management, mTLS, and authorization policies" "External"
        kserve = softwareSystem "KServe" "Serverless ML inference platform providing InferenceService CRDs" "Internal RHOAI"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management and RBAC" "External"
        s3Storage = softwareSystem "S3 Storage" "Object storage for ML model artifacts" "External"
        ociRegistry = softwareSystem "OCI Registry" "Container/artifact registry for model storage via ORAS" "External"
        sigstore = softwareSystem "Sigstore" "Supply chain security for model signing and verification" "External"

        # User interactions
        dataScientist -> modelRegistry "Registers models, browses catalog, deploys models via UI and API"
        platformAdmin -> modelRegistry "Configures registry, manages access policies"

        # Internal container relationships
        bffServer -> registryProxy "Proxies API requests" "REST/HTTP"
        bffServer -> k8sAPI "Manages ConfigMaps, Secrets, Jobs; performs SubjectAccessReviews" "HTTPS/6443"
        bffServer -> asyncUploadJob "Creates upload jobs" "Kubernetes Job API"
        registryProxy -> database "Reads and writes model metadata" "GORM (PostgreSQL/MySQL driver)"
        controller -> kserve "Watches InferenceService resources" "Kubernetes Watch API"
        controller -> registryProxy "Syncs serving URLs back to registry" "REST/HTTP (OpenAPI client)"
        controller -> k8sAPI "Discovers registry Service endpoints, leader election" "HTTPS/6443"
        asyncUploadJob -> s3Storage "Copies model artifacts" "HTTPS/443, AWS IAM"
        asyncUploadJob -> ociRegistry "Pushes/pulls model artifacts" "HTTPS, ORAS/skopeo"
        asyncUploadJob -> sigstore "Signs model artifacts" "HTTPS"
        asyncUploadJob -> registryProxy "Registers uploaded models" "REST/HTTP"

        # External system relationships
        modelRegistry -> istio "Traffic routing and mTLS enforcement" "VirtualService + AuthorizationPolicy"
        modelRegistry -> kserve "Watches InferenceService CRDs for serving state" "Kubernetes API"
        modelRegistry -> s3Storage "Downloads/uploads model artifacts" "HTTPS/443"
        modelRegistry -> k8sAPI "Resource management, RBAC enforcement" "HTTPS/6443"
    }

    views {
        systemContext modelRegistry "SystemContext" {
            include *
            autoLayout
        }

        container modelRegistry "Containers" {
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
            element "Internal RHOAI" {
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
            element "Database" {
                shape cylinder
                background #f5a623
                color #000000
            }
            element "FIPS" {
                background #4a90e2
                color #ffffff
            }
        }
    }
}
