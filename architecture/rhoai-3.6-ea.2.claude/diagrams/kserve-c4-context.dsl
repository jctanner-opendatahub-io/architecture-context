workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and deploys ML models for inference"
        platformAdmin = person "Platform Admin" "Manages RHOAI platform components"

        kserve = softwareSystem "KServe" "Model serving control plane for RHOAI - manages inference endpoint lifecycle through CRDs" {
            coreController = container "KServe Controller Manager" "Reconciles InferenceService, InferenceGraph, TrainedModel CRDs" "Go Operator (controller-runtime)"
            llmisvcController = container "LLMInferenceService Controller" "Manages LLMInferenceService with HPA, KEDA, Gateway API, LeaderWorkerSet support" "Go Operator (controller-runtime)"
            kserveModule = container "kserve-module Operator" "RHOAI lifecycle manager: CRDs, webhooks, cert-manager, RBAC, serving runtimes" "Go Operator (controller-runtime)"
            localModelController = container "LocalModel Controllers" "Pre-caches model artifacts to cluster nodes via PVs, Jobs, DaemonSets" "Go Operator (controller-runtime)"
            webhookServer = container "Webhook Server" "17 admission webhooks (Fail policy) for CRD validation and mutation" "Kubernetes Admission Webhook"
            router = container "InferenceGraph Router" "Request routing with TokenReview/SubjectAccessReview auth for graph topologies" "Go HTTP Server"
            kubeRBACProxy = container "kube-rbac-proxy" "TLS termination and Kubernetes RBAC auth for metrics endpoint (8443→8080)" "Sidecar"
            pythonSDK = container "Python SDK & Model Servers" "V2 Inference Protocol servers: HuggingFace, vLLM, OVMS, MLServer, sklearn, LightGBM, XGBoost" "Python (FastAPI/uvicorn + gRPC)"
        }

        gatewayAPI = softwareSystem "Gateway API" "Kubernetes Gateway API for ingress routing (HTTPRoute)" "External"
        istio = softwareSystem "Istio" "Service mesh for traffic management (VirtualService)" "External"
        knativeServing = softwareSystem "Knative Serving" "Serverless autoscaling platform" "External"
        certManager = softwareSystem "cert-manager" "TLS certificate lifecycle management" "External"
        keda = softwareSystem "KEDA" "Event-driven autoscaling for Kubernetes" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "External"
        odhPlatform = softwareSystem "ODH Platform Utilities" "Shared platform detection, manifest rendering, deployment helpers" "Internal RHOAI"
        s3Storage = softwareSystem "S3-compatible Storage" "Model artifact storage (AWS S3, MinIO, etc.)" "External"
        azureStorage = softwareSystem "Azure Blob Storage" "Model artifact storage on Azure" "External"
        gcsStorage = softwareSystem "Google Cloud Storage" "Model artifact storage on GCP" "External"
        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster resource management, RBAC, admission" "External"

        dataScientist -> kserve "Creates InferenceService, LLMInferenceService, InferenceGraph CRs via kubectl/API"
        platformAdmin -> kserve "Manages Kserve CR, ClusterServingRuntimes, platform configuration"

        kserve -> kubernetesAPI "Creates Deployments, Services, HPAs, Routes, RBAC resources" "HTTPS/6443 TLS 1.2+ SA token"
        kserve -> gatewayAPI "Creates HTTPRoute resources for model ingress routing" "HTTPS"
        kserve -> istio "Creates VirtualService resources for traffic management" "HTTPS"
        kserve -> knativeServing "Creates Knative Services for serverless inference" "HTTPS"
        kserve -> certManager "Requests TLS certificates for webhook server" "HTTPS"
        kserve -> keda "Creates ScaledObjects for event-driven autoscaling" "HTTPS"
        kserve -> odhPlatform "Platform detection and manifest rendering" "Go library"
        kserve -> s3Storage "Downloads model artifacts for serving" "HTTPS/443"
        kserve -> azureStorage "Downloads model artifacts for serving" "HTTPS/443"
        kserve -> gcsStorage "Downloads model artifacts for serving" "HTTPS/443"
        prometheus -> kserve "Scrapes metrics via kube-rbac-proxy" "HTTPS/8443"
    }

    views {
        systemContext kserve "SystemContext" {
            include *
            autoLayout
        }

        container kserve "Containers" {
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
        }
    }
}
