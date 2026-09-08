workspace {
    model {
        dataScientist = person "Data Scientist" "Creates model subscriptions and accesses AI model inference endpoints"
        platformAdmin = person "Platform Admin" "Manages tenants, model references, and platform configuration"

        maas = softwareSystem "Models-as-a-Service" "Multi-tenant API gateway and controller platform for managing AI model subscriptions, API key authentication, and Gateway API routing" {
            maasAPI = container "maas-api" "REST API server exposing OpenAI-compatible endpoints for model discovery, subscription management, and API key lifecycle" "Go / Gin" {
                tenantAuthMW = component "TenantAuthMiddleware" "Validates Bearer tokens via Kubernetes TokenReview and SubjectAccessReview" "Go middleware"
                modelHandler = component "Model Handler" "Lists available models and model references" "Gin route handler"
                subscriptionHandler = component "Subscription Handler" "Manages model subscriptions per tenant" "Gin route handler"
                apiKeyHandler = component "API Key Handler" "CRUD operations for API keys" "Gin route handler"
                tenantHandler = component "Tenant Handler" "Internal-only tenant management (not gateway-exposed)" "Gin route handler"
            }
            maasController = container "maas-controller" "Kubernetes controller manager reconciling CRD-driven resource model with 6 reconcilers" "Go / controller-runtime" {
                aiTenantReconciler = component "AITenant Reconciler" "Manages tenant namespaces and configuration" "controller-runtime"
                authPolicyReconciler = component "MaaSAuthPolicy Reconciler" "Creates Kuadrant AuthPolicy for per-tenant gateway authentication" "controller-runtime"
                modelRefReconciler = component "MaaSModelRef Reconciler" "Tracks model availability via KServe InferenceService watches" "controller-runtime"
                subscriptionReconciler = component "MaaSSubscription Reconciler" "Creates HTTPRoute and TokenRateLimitPolicy resources" "controller-runtime"
                tenantConfigReconciler = component "MaasTenantConfig Reconciler" "Manages per-tenant configuration" "controller-runtime"
                lifecycleReconciler = component "Lifecycle Reconciler" "Manages component lifecycle and deployment state" "controller-runtime"
            }
            webhookServer = container "Webhook Server" "Validates AITenant, MaaSAuthPolicy, MaaSModelRef, MaaSSubscription resources" "ValidatingWebhookConfiguration"
        }

        gatewayAPI = softwareSystem "Gateway API" "Kubernetes Gateway API for ingress routing (maas-default-gateway)" "External"
        kuadrant = softwareSystem "Kuadrant/Authorino" "API key, TokenReview, and OIDC JWT authentication at the gateway layer" "External"
        kserve = softwareSystem "KServe" "Model serving platform providing InferenceService for model availability" "Internal RHOAI"
        postgresql = softwareSystem "PostgreSQL" "Persistent storage for API keys, subscriptions, and tenant metadata" "External"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource operations, TokenReview, and SubjectAccessReview" "External"
        otel = softwareSystem "OpenTelemetry Collector" "Distributed tracing via OTLP/gRPC" "External"

        # User interactions
        dataScientist -> maas "Discovers models, creates subscriptions, manages API keys" "HTTPS via Gateway API"
        platformAdmin -> maas "Manages tenants and model references" "HTTPS / kubectl"

        # System interactions
        maas -> gatewayAPI "Routes external traffic via HTTPRoute" "Kubernetes API"
        maas -> kuadrant "Enforces per-tenant authentication via AuthPolicy" "Kubernetes API"
        maas -> kserve "Reads model serving state (conditional watch)" "Kubernetes API"
        maas -> postgresql "Stores API keys, subscriptions, tenant metadata" "SQL (pgx)"
        maas -> k8sAPI "TokenReview, SubjectAccessReview, CRD operations" "HTTPS/6443"
        maas -> otel "Exports traces" "OTLP/gRPC"
        kuadrant -> k8sAPI "Validates tokens at gateway" "HTTPS/6443"
    }

    views {
        systemContext maas "SystemContext" {
            include *
            autoLayout
        }

        container maas "Containers" {
            include *
            autoLayout
        }

        component maasAPI "MaaSAPIComponents" {
            include *
            autoLayout
        }

        component maasController "MaaSControllerComponents" {
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
            element "Component" {
                background #85bbf0
                color #000000
            }
        }
    }
}
