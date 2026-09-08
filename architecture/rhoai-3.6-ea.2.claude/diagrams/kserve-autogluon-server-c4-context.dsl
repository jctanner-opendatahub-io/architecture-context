workspace {
    model {
        user = person "Data Scientist" "Creates and deploys ML models for inference"

        kserveAutogluon = softwareSystem "KServe AutoGluon Server" "KServe control plane + AutoGluon model serving runtime for RHOAI" {
            manager = container "KServe Controller Manager" "Reconciles InferenceService, InferenceGraph, TrainedModel, ClusterServingRuntime, ServingRuntime CRDs" "Go Operator (controller-runtime)"
            llmisvc = container "LLMInferenceService Operator" "Reconciles LLMInferenceService and LLMInferenceServiceConfig CRDs with Gateway API, KEDA, LeaderWorkerSet support" "Go Operator (controller-runtime)"
            localmodel = container "LocalModel Operator" "Reconciles LocalModelCache and LocalModelNamespaceCache CRDs, provisions PVs/PVCs" "Go Operator (controller-runtime)"
            localmodelnode = container "LocalModelNode Agent" "Reconciles LocalModelNode CRDs, creates download Jobs for local model caching" "Go Operator (controller-runtime)"
            webhook = container "Webhook Server" "18 mutating/validating/conversion admission webhooks for all CRD kinds" "Go Webhook Handler (443/TCP TLS)"
            kubeRbacProxy = container "kube-rbac-proxy" "TLS termination and Kubernetes RBAC authentication proxy for metrics" "Sidecar (8443→8080)"
            autogluonServer = container "AutoGluon Model Server" "Serves inference for AutoGluon TabularPredictor and TimeSeriesPredictor models via HTTP V1/V2 and gRPC V2" "Python (FastAPI + gRPC)"
            router = container "Inference Router" "Routes inference requests across InferenceGraph nodes (ensemble, splitter, switch)" "Go HTTP Server"
            kserveSDK = container "KServe SDK" "Python SDK providing FastAPI model server base, storage handlers, and V2 inference protocol" "Python Library"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster API server for resource management and RBAC" "External"
        istio = softwareSystem "Istio Service Mesh" "Traffic management via VirtualServices, mTLS, AuthorizationPolicy" "External"
        knativeServing = softwareSystem "Knative Serving" "Serverless workload autoscaling and revision management" "External"
        gatewayAPI = softwareSystem "Gateway API" "Kubernetes-native routing via HTTPRoute and Gateway resources" "External"
        keda = softwareSystem "KEDA" "Event-driven autoscaling via ScaledObject resources" "External"
        certManager = softwareSystem "cert-manager" "TLS certificate provisioning for webhook endpoints" "External"
        prometheus = softwareSystem "Prometheus" "Metrics collection via service endpoint scraping" "External"

        s3 = softwareSystem "S3 Storage" "AWS S3-compatible object storage for model artifacts" "External Service"
        gcs = softwareSystem "Google Cloud Storage" "GCS object storage for model artifacts" "External Service"
        azureBlob = softwareSystem "Azure Blob Storage" "Azure Blob storage for model artifacts" "External Service"

        user -> kserveAutogluon "Creates InferenceService / LLMInferenceService CRs via kubectl"
        user -> autogluonServer "Sends inference requests" "HTTP REST / gRPC"

        manager -> k8sAPI "Manages Deployments, Services, networking resources" "HTTPS/6443"
        manager -> istio "Creates VirtualServices for traffic routing" "Kubernetes API"
        manager -> knativeServing "Creates Knative Services for serverless inference" "Kubernetes API"
        manager -> gatewayAPI "Creates HTTPRoutes for Gateway API-based routing" "Kubernetes API"
        llmisvc -> k8sAPI "Manages LLM workloads, Gateway API, KEDA, LWS resources" "HTTPS/6443"
        llmisvc -> keda "Creates ScaledObjects for autoscaling" "Kubernetes API"
        localmodel -> k8sAPI "Manages PVs, PVCs, LocalModelNode resources" "HTTPS/6443"
        localmodelnode -> k8sAPI "Creates batch Jobs for model downloads" "HTTPS/6443"

        autogluonServer -> s3 "Downloads model artifacts" "HTTPS/443 (AWS IAM)"
        autogluonServer -> gcs "Downloads model artifacts" "HTTPS/443 (GCS SA)"
        autogluonServer -> azureBlob "Downloads model artifacts" "HTTPS/443 (Azure AD)"

        prometheus -> kubeRbacProxy "Scrapes metrics" "HTTPS/8443"
        k8sAPI -> webhook "Admission validation and mutation" "HTTPS/443"
    }

    views {
        systemContext kserveAutogluon "SystemContext" {
            include *
            autoLayout
        }

        container kserveAutogluon "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "External Service" {
                background #f5a623
                color #ffffff
            }
            element "Person" {
                background #4a90e2
                color #ffffff
                shape person
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
