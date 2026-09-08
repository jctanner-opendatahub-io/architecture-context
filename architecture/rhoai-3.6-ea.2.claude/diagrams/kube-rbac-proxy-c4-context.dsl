workspace {
    model {
        serviceClient = person "Service Client" "Pod or external client requesting access to a protected upstream service"
        platformAdmin = person "Platform Admin" "Configures kube-rbac-proxy sidecar with TLS certs, auth mode, and authorization policies"

        kubeRbacProxy = softwareSystem "kube-rbac-proxy" "TLS-terminating reverse proxy sidecar that enforces Kubernetes RBAC authentication and authorization" {
            tlsTerminator = container "TLS Terminator" "Terminates TLS connections, supports cert hot-reload, FIPS-compliant crypto" "Go, crypto/tls, strictfipsruntime"
            authNHandler = container "Authentication Handler" "Validates identity via OIDC token validation or Kubernetes TokenReview delegation" "Go, k8s.io/apiserver"
            authZHandler = container "Authorization Handler" "Union chain: hardcoded metrics authorizer, static policy authorizer, SubjectAccessReview authorizer" "Go, k8s.io/apiserver"
            reverseProxy = container "Reverse Proxy" "Forwards authenticated and authorized requests to upstream application" "Go, httputil.ReverseProxy"
            healthEndpoint = container "Health Check Endpoint" "/healthz on dedicated port, same TLS, no auth middleware" "Go"
        }

        kubernetesAPI = softwareSystem "Kubernetes API Server" "Cluster control plane for TokenReview and SubjectAccessReview delegation" "External"
        upstreamApp = softwareSystem "Upstream Application" "Protected service running in the same pod (e.g., Prometheus exporter)" "Internal"
        oidcProvider = softwareSystem "OIDC Provider" "External identity provider for OIDC token validation (optional)" "External"

        serviceClient -> kubeRbacProxy "Sends HTTPS requests" "HTTPS/8443, TLS 1.2+, Bearer Token"
        kubeRbacProxy -> upstreamApp "Forwards authorized requests" "HTTP/8080, plaintext, localhost"
        kubeRbacProxy -> kubernetesAPI "Delegates authentication (TokenReview) and authorization (SubjectAccessReview)" "HTTPS/6443, ServiceAccount token"
        kubeRbacProxy -> oidcProvider "Validates OIDC tokens (when configured)" "HTTPS"
        platformAdmin -> kubeRbacProxy "Configures via CLI flags and mounted files"

        tlsTerminator -> authNHandler "Passes decrypted request"
        authNHandler -> authZHandler "Passes authenticated request"
        authZHandler -> reverseProxy "Passes authorized request"
        authNHandler -> kubernetesAPI "TokenReview" "HTTPS/6443"
        authZHandler -> kubernetesAPI "SubjectAccessReview" "HTTPS/6443"
        reverseProxy -> upstreamApp "HTTP forward" "HTTP/8080"
    }

    views {
        systemContext kubeRbacProxy "SystemContext" {
            include *
            autoLayout
        }

        container kubeRbacProxy "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal" {
                background #7ed321
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
            element "Person" {
                background #08427b
                color #ffffff
                shape person
            }
        }
    }
}
