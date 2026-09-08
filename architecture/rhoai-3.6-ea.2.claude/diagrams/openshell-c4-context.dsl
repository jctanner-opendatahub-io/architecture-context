workspace {
    model {
        datascientist = person "Data Scientist / AI Developer" "Creates and manages sandboxed AI agent environments"
        platformadmin = person "Platform Admin" "Configures workspaces, providers, and gateway policies"

        openshell = softwareSystem "OpenShell" "Sandboxed execution environments for autonomous AI agents with declarative policy enforcement" {
            gateway = container "OpenShell Gateway" "Control-plane server managing sandbox lifecycle, authentication, authorization, policy delivery, and credential injection" "Rust (gRPC/HTTP, rustls TLS)" {
                server = component "Server Framework" "Auth chain, gRPC handlers, CLI entry point" "openshell-server"
                policyLib = component "Policy Engine" "YAML policy parsing, validation, defaults" "openshell-policy"
                prover = component "Policy Prover" "Z3-based formal policy verification" "openshell-prover"
                router = component "Inference Router" "Local inference model API routing" "openshell-router"
                ocsf = component "Security Events" "OCSF structured security event logging" "openshell-ocsf"
                otel = component "Observability" "OpenTelemetry distributed tracing" "openshell-otel"
            }
            supervisor = container "Supervisor" "Statically-linked binary injected into sandbox pods; enforces filesystem, network, process, and inference policies" "Rust (static binary, nftables, L7 proxy)"
            cli = container "CLI" "User-facing tool for sandbox creation, policy management, and TUI monitoring" "Rust (static binary)"
            driverK8s = container "Kubernetes Driver" "Provisions sandbox pods with supervisor sideloading" "Rust Library"
            driverDocker = container "Docker Driver" "Local sandbox container creation" "Rust Library"
            driverPodman = container "Podman Driver" "Local sandbox container creation" "Rust Library"
            driverVM = container "VM Driver" "MicroVM-based sandbox isolation" "Rust Library"
        }

        # External Systems
        kubernetes = softwareSystem "Kubernetes / OpenShift" "Container orchestration platform" "External"
        keycloak = softwareSystem "OIDC Provider (Keycloak)" "User authentication and role management" "External"
        certManager = softwareSystem "cert-manager" "Automated TLS certificate lifecycle" "External"
        vault = softwareSystem "HashiCorp Vault / OpenBao" "Secure credential storage backend" "External"
        spiffe = softwareSystem "SPIFFE / SPIRE" "Workload identity framework" "External"
        postgresql = softwareSystem "PostgreSQL" "Persistent database for multi-replica gateways" "External"
        envoyGateway = softwareSystem "Envoy Gateway" "Gateway API-based ingress routing" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"
        externalEndpoints = softwareSystem "External Services" "AI model APIs, cloud services, etc." "External"

        # Relationships - Users
        datascientist -> openshell "Creates sandboxes, runs AI agents via CLI/SDK" "gRPC/8080 TLS"
        platformadmin -> openshell "Configures workspaces and providers" "gRPC/8080 TLS"

        # Relationships - Internal
        cli -> gateway "Issues sandbox and provider commands" "gRPC/8080 TLS + Bearer Token"
        gateway -> driverK8s "Provisions sandbox pods" "Internal"
        gateway -> driverDocker "Creates local containers" "Internal"
        gateway -> driverPodman "Creates local containers" "Internal"
        gateway -> driverVM "Creates MicroVMs" "Internal"
        driverK8s -> supervisor "Sideloads supervisor binary into pods" "Init container / ImageVolume"
        supervisor -> gateway "Connects back for policy and credentials" "gRPC/8080 mTLS + Sandbox JWT (Ed25519)"

        # Relationships - External
        gateway -> keycloak "Validates OIDC JWT tokens (JWKS fetch)" "HTTPS/443"
        gateway -> kubernetes "Manages pod lifecycle, namespaces, RBAC, Sandbox CRs" "HTTPS/443"
        gateway -> certManager "Requests TLS certificates" "Certificate CRDs"
        gateway -> vault "Stores and retrieves provider credentials" "HTTP(S)/8200"
        gateway -> spiffe "Exchanges workload identity tokens" "gRPC (Unix socket)"
        gateway -> postgresql "Persists state for multi-replica scaling" "TCP/5432"
        envoyGateway -> gateway "Routes external gRPC traffic" "GRPCRoute/8080 TLS"
        prometheus -> gateway "Scrapes metrics" "HTTP/9090"
        supervisor -> externalEndpoints "Policy-controlled agent egress (L7-aware, fail-closed)" "HTTPS/443"
    }

    views {
        systemContext openshell "SystemContext" {
            include *
            autoLayout
        }

        container openshell "Containers" {
            include *
            autoLayout
        }

        component gateway "GatewayComponents" {
            include *
            autoLayout
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
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
