workspace {
    model {
        user = person "Data Scientist" "Submits and manages distributed compute workloads via notebooks or workbenches"

        codeflareSDK = softwareSystem "CodeFlare SDK" "Python client library for submitting and managing distributed compute workloads on Kubernetes via KubeRay and Kueue" {
            authLayer = container "Authentication Layer" "kube-authkit auto-detection with legacy fallback (Bearer token, kubeconfig, in-cluster SA)" "Python Module"
            crdPath = container "CRD Job Submission" "Creates RayJob CRs via vendored KubeRay Python client with optional Kueue annotations" "Python Module"
            directPath = container "Direct Job Submission" "RayJobClient wrapper around Ray JobSubmissionClient for HTTP-based job submission" "Python Module"
            certGen = container "Certificate Generator" "Generates self-signed RSA 3072-bit CA/server certificates via cryptography library" "Python Module"
            kuberayVendored = container "Vendored KubeRay Client" "RayjobApi, RayClusterApi - vendored to avoid PyPI version conflicts" "Python Package"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster API for resource management and authentication" "External"
        kuberayOperator = softwareSystem "KubeRay Operator" "Reconciles RayJob and RayCluster CRs into Ray cluster pods" "Internal ODH"
        kueue = softwareSystem "Kueue" "Batch workload scheduling with queue management and priority classes" "Internal ODH"
        rayDashboard = softwareSystem "Ray Dashboard" "HTTP endpoint for direct job submission to existing Ray clusters" "External"
        kubeAuthkit = softwareSystem "kube-authkit" "Shared OpenDataHub library for unified Kubernetes authentication" "Internal ODH"

        user -> codeflareSDK "Submits distributed compute jobs via Python API"
        codeflareSDK -> k8sAPI "Creates RayJob/RayCluster CRs, stores TLS Secrets" "HTTPS/6443"
        codeflareSDK -> rayDashboard "Submits jobs directly to Ray clusters" "HTTP(S)"
        codeflareSDK -> kubeAuthkit "Auto-detects Kubernetes credentials"
        k8sAPI -> kuberayOperator "Notifies on RayJob/RayCluster CR changes"
        k8sAPI -> kueue "Notifies on Workload admission"
        kuberayOperator -> k8sAPI "Creates Ray cluster pods"

        authLayer -> kubeAuthkit "Delegates credential detection"
        crdPath -> kuberayVendored "Creates CRs via vendored API"
        crdPath -> authLayer "Authenticates to K8s"
        directPath -> rayDashboard "HTTP job submission with configurable TLS and auth headers"
        certGen -> k8sAPI "Stores generated TLS certificates as Secrets"
    }

    views {
        systemContext codeflareSDK "SystemContext" {
            include *
            autoLayout
        }

        container codeflareSDK "Containers" {
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
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
        }
    }
}
