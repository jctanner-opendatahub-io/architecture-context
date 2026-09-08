workspace {
    model {
        user = person "End User" "Browser user or API client authenticating to RHOAI services"
        dataScientist = person "Data Scientist" "Accesses ML services through authenticated proxy"

        kubeAuthProxy = softwareSystem "kube-auth-proxy" "FIPS-compliant reverse authentication proxy gating access to RHOAI services via OAuth2/OIDC, OpenShift OAuth, K8s TokenReview, and Basic Auth" {
            proxyServer = container "Proxy Server" "Main HTTP server handling authentication and proxying" "Go (gorilla/mux, justinas/alice)" {
                preAuthChain = component "Pre-Auth Chain" "Health checks, HTTPS redirect, logging, metrics" "Go Middleware"
                sessionChain = component "Session-Aware Chain" "Session loading and authentication enforcement" "Go Middleware"
                oauthProxy = component "OAuthProxy" "Core OAuth2/OIDC authentication handler" "Go"
                mlflowHandler = component "MLflow Auth-Denied Handler" "Structured error responses for API clients" "Go"
                upstreamProxy = component "Upstream Proxy" "Forwards authenticated requests with identity headers" "Go"
            }
            authProviders = container "Authentication Providers" "Multi-mechanism authentication" "Go" {
                oauth2Provider = component "OAuth2/OIDC Provider" "Authorization code flow with configurable providers" "Go"
                openshiftOAuth = component "OpenShift OAuth" "First-class OpenShift OAuth with auto-discovery" "Go"
                tokenReview = component "K8s TokenReview" "ServiceAccount token validation with singleflight cache (TTL: 10s)" "Go"
                basicAuth = component "htpasswd Basic Auth" "File-based basic authentication" "Go"
                jwtBearer = component "JWT Bearer" "JWT passthrough with configurable issuer validation" "Go"
            }
            sessionStore = container "Session Store" "Cookie-based or Redis-backed session persistence" "Go"
        }

        upstreamService = softwareSystem "Upstream Service" "Protected RHOAI service (e.g., MLflow Tracking Server)" "Internal RHOAI"
        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster API server for TokenReview and resource operations" "Platform"
        openshiftOAuthServer = softwareSystem "OpenShift OAuth Server" "Cluster OAuth server with auto-discovery" "Platform"
        redis = softwareSystem "Redis / Valkey" "Distributed session storage with TLS and Sentinel/Cluster support" "External"
        oidcProvider = softwareSystem "External OIDC Provider" "Third-party OAuth2/OIDC identity provider" "External"

        # Relationships
        user -> kubeAuthProxy "Authenticates via browser (OAuth2) or API (Bearer/Basic)" "HTTPS"
        dataScientist -> kubeAuthProxy "Accesses ML services" "HTTPS"
        kubeAuthProxy -> upstreamService "Forwards authenticated requests with X-Forwarded-User/Email/Groups" "HTTP"
        kubeAuthProxy -> kubernetesAPI "TokenReview API for SA token validation" "HTTPS/6443"
        kubeAuthProxy -> openshiftOAuthServer "OAuth2 authorization code flow, token exchange" "HTTPS"
        kubeAuthProxy -> redis "Session persistence (optional)" "TCP/TLS"
        kubeAuthProxy -> oidcProvider "OIDC discovery and token validation" "HTTPS"
    }

    views {
        systemContext kubeAuthProxy "SystemContext" {
            include *
            autoLayout
        }

        container kubeAuthProxy "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Platform" {
                background #4a90e2
                color #ffffff
            }
            element "Internal RHOAI" {
                background #7ed321
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
            element "Component" {
                background #85bbf0
                color #000000
            }
        }
    }
}
