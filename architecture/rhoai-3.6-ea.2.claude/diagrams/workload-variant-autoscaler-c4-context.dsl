workspace {
    model {
        mlEngineer = person "ML Engineer" "Deploys and manages inference model servers on OpenShift"
        platformAdmin = person "Platform Admin" "Configures autoscaling parameters via ConfigMaps"

        wva = softwareSystem "Workload Variant Autoscaler" "Kubernetes controller that performs intelligent saturation-based autoscaling for inference model servers using Prometheus metrics, Kalman filtering, and GPU rebalancing" {
            configmapCtrl = container "ConfigMap Controller" "Bootstraps and live-updates autoscaling configuration from ConfigMaps; gates readiness probe until initial sync" "Go controller-runtime"
            hpaCtrl = container "HPA Controller" "Watches HorizontalPodAutoscalers to discover autoscaling targets" "Go controller-runtime"
            inferencePoolCtrl = container "InferencePool Controller" "Watches InferencePool resources for pool-based autoscaling configuration" "Go controller-runtime"
            scaledObjectCtrl = container "ScaledObject Controller" "Watches KEDA ScaledObjects for autoscaling targets (conditional)" "Go controller-runtime"
            optimizationEngine = container "Optimization Engine" "Pipeline of pluggable engines: Kalman filter predictor and GPU rebalancing coordinator" "Go"
            directActuator = container "DirectActuator" "Patches autoscaling/v1/Scale subresources on Deployments and LeaderWorkerSets" "Go"
            scaleFromZero = container "Scale-from-Zero Engine" "Uses dynamic client discovery to scale workloads with zero replicas" "Go"
            metricsEndpoint = container "Metrics Endpoint" "Exposes Prometheus metrics on :8443 with TokenReview+SAR auth and self-signed TLS" "Go controller-runtime"
        }

        prometheus = softwareSystem "Prometheus" "Metrics collection and query platform providing workload saturation metrics" "External"
        kubeAPI = softwareSystem "Kubernetes API" "OpenShift/Kubernetes API server for resource management and watch streams" "External"
        keda = softwareSystem "KEDA" "Kubernetes Event-Driven Autoscaling providing ScaledObject CRDs" "External"
        gatewayAPIInference = softwareSystem "Gateway API Inference Extension" "Provides InferencePool CRDs for pool-based inference routing" "Internal RHOAI"
        prometheusOperator = softwareSystem "Prometheus Operator" "Manages ServiceMonitor CRDs for metrics collection" "Internal RHOAI"

        # User interactions
        platformAdmin -> wva "Configures autoscaling parameters via ConfigMaps"
        mlEngineer -> kubeAPI "Deploys inference model servers"

        # Internal container relationships
        configmapCtrl -> kubeAPI "Watches/reads ConfigMaps" "HTTPS/6443"
        hpaCtrl -> kubeAPI "Watches HPAs" "HTTPS/6443"
        inferencePoolCtrl -> kubeAPI "Watches InferencePools" "HTTPS/6443"
        scaledObjectCtrl -> kubeAPI "Watches ScaledObjects" "HTTPS/6443"
        optimizationEngine -> prometheus "Queries saturation metrics" "HTTPS TLS 1.2+ / Bearer Token"
        optimizationEngine -> kubeAPI "Reads Nodes and ResourceQuotas" "HTTPS/6443"
        directActuator -> kubeAPI "Patches Scale subresources" "HTTPS/6443"
        scaleFromZero -> kubeAPI "Dynamic discovery and scaling" "HTTPS/6443"

        # External system relationships
        wva -> prometheus "Queries workload saturation metrics" "HTTPS TLS 1.2+"
        wva -> kubeAPI "Watches resources, patches Scale subresources" "HTTPS/6443"
        wva -> prometheusOperator "Creates ServiceMonitor for metrics scraping" "Kubernetes API"
        keda -> kubeAPI "Provides ScaledObject CRDs"
        gatewayAPIInference -> kubeAPI "Provides InferencePool CRDs"
    }

    views {
        systemContext wva "SystemContext" {
            include *
            autoLayout
        }

        container wva "Containers" {
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
                shape person
                background #4a90e2
                color #ffffff
            }
        }
    }
}
