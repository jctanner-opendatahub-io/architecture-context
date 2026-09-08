workspace {
    model {
        user = person "Data Scientist" "Creates and uses interactive workbench environments for ML/AI development"

        notebooks = softwareSystem "Notebooks" "Container image factory producing JupyterLab and code-server workbench images with CPU, CUDA, and ROCm variants on UBI9" {
            jupyterlabImages = container "JupyterLab Images" "Layered notebook images: minimal → datascience → pytorch/tensorflow/trustyai/llmcompressor" "Container Image (UBI9 Python 3.12)"
            codeserverImages = container "Code-Server Images" "code-server IDE with nginx reverse proxy for path-based routing" "Container Image (UBI9 Python 3.12)"
            startNotebook = container "start-notebook.sh" "Entrypoint script assembling JupyterLab ServerApp args from platform env vars" "Shell Script"
            runCodeServer = container "run-code-server.sh" "Entrypoint script starting nginx and code-server with NB_PREFIX routing" "Shell Script"
            buildInputs = container "buildinputs" "Build-time Go utility for resolving image build inputs" "Go Executable"
            checkPayload = container "check-payload" "Build-time FIPS compliance scanner for container images (CGO_ENABLED=0)" "Go Executable"
        }

        controller = softwareSystem "odh-notebook-controller" "Manages workbench pod lifecycle, injects OAuth proxy sidecar and env vars" "Internal RHOAI"
        dashboard = softwareSystem "RHOAI Dashboard" "Web UI for creating and managing workbench instances" "Internal RHOAI"
        oauthProxy = softwareSystem "OAuth Proxy" "Sidecar authenticating requests via OpenShift OAuth" "Internal RHOAI"
        openshiftRoute = softwareSystem "OpenShift Route" "TLS-terminating ingress for workbench access" "OpenShift Platform"
        k8sAPI = softwareSystem "Kubernetes API" "Cluster API for user workload interactions" "OpenShift Platform"
        s3Storage = softwareSystem "S3-Compatible Storage" "Object storage for data and model artifacts" "External"
        konflux = softwareSystem "Konflux" "CI/CD pipeline for building container images" "External"

        user -> dashboard "Creates workbench via UI"
        dashboard -> controller "Triggers workbench creation"
        controller -> notebooks "Creates workbench pod with selected image"
        controller -> oauthProxy "Injects as sidecar into workbench pod"
        user -> openshiftRoute "Accesses workbench via browser (HTTPS/443)"
        openshiftRoute -> oauthProxy "Forwards to OAuth proxy"
        oauthProxy -> jupyterlabImages "Proxies to JupyterLab (HTTP/8888)"
        oauthProxy -> codeserverImages "Proxies to code-server (HTTP/8787)"
        jupyterlabImages -> k8sAPI "User workloads access cluster (HTTPS/443)"
        jupyterlabImages -> s3Storage "User workloads access data (HTTPS/443)"
        konflux -> notebooks "Builds container images from Dockerfiles"
        startNotebook -> jupyterlabImages "Launches JupyterLab server"
        runCodeServer -> codeserverImages "Launches nginx + code-server"
    }

    views {
        systemContext notebooks "SystemContext" {
            include *
            autoLayout
        }

        container notebooks "Containers" {
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
            element "OpenShift Platform" {
                background #ee0000
                color #ffffff
            }
            element "Person" {
                shape Person
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
