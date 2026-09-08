workspace {
    model {
        user = person "Data Scientist" "Creates and manages interactive development workspaces (Jupyter, VS Code, RStudio)"
        admin = person "Platform Admin" "Defines WorkspaceKind templates and manages cluster-wide workspace configuration"

        workbenches = softwareSystem "Workbenches" "Kubernetes controller and REST backend for managing interactive development workspaces as Workspace and WorkspaceKind custom resources" {
            controller = container "Workspace Controller" "Reconciles Workspace and WorkspaceKind CRs into StatefulSets, Services, ServiceAccounts, RoleBindings, and ingress resources" "Go controller-runtime operator (/manager)"
            webhooks = container "Admission Webhooks" "Validates Workspace/WorkspaceKind create/update/delete and converts CRD versions" "Go webhook handlers"
            backend = container "REST Backend" "Authenticated HTTP API for workspace CRUD, PVC management, secret management, and metrics" "Go HTTP server (/backend) :4000"
            frontend = container "Frontend UI" "React SPA served by nginx for workspace management" "React/nginx :8080"
        }

        k8sApi = softwareSystem "Kubernetes API Server" "Cluster control plane for resource management" "External" {
            tags "External"
        }
        gatewayApi = softwareSystem "Gateway API / Istio" "Ingress routing for workspace pods via HTTPRoute or VirtualService" "External" {
            tags "External"
        }
        oauth2Proxy = softwareSystem "OAuth2 Proxy / Istio AuthN" "Upstream authentication proxy that sets user identity headers" "External" {
            tags "External"
        }
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External" {
            tags "External"
        }

        # User interactions
        user -> workbenches "Creates/manages workspaces via UI"
        admin -> workbenches "Defines WorkspaceKind templates via kubectl"

        # Internal interactions
        frontend -> backend "REST API calls" "HTTP/4000"
        backend -> k8sApi "Workspace CRUD, PVC/Secret operations, SubjectAccessReview" "HTTPS/6443"
        controller -> k8sApi "Reconciles CRs, creates owned resources, watches Pods" "HTTPS/6443"
        k8sApi -> webhooks "Admission requests" "HTTPS/443"
        controller -> gatewayApi "Creates HTTPRoute or VirtualService for workspace routing"

        # External interactions
        oauth2Proxy -> backend "Sets user identity headers for authentication" "HTTP headers"
        prometheus -> workbenches "Scrapes controller metrics" "HTTP/8080"
    }

    views {
        systemContext workbenches "SystemContext" {
            include *
            autoLayout
        }

        container workbenches "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Element" {
                shape RoundedBox
            }
            element "Person" {
                shape Person
                background #4a90e2
                color #ffffff
            }
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "Container" {
                background #85bbf0
                color #000000
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }
}
