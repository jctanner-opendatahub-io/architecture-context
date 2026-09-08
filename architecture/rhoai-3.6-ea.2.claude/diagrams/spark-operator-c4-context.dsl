workspace {
    model {
        user = person "Data Engineer" "Creates and manages Apache Spark workloads on OpenShift"

        sparkOperator = softwareSystem "Spark Operator" "Kubernetes operator that manages Apache Spark application lifecycle through SparkApplication, ScheduledSparkApplication, and SparkConnect CRDs" {
            moduleController = container "spark-operator-module" "Manages full operator lifecycle (CRDs, RBAC, Deployments, certs, NetworkPolicies). Watches SparkOperator CR." "Go controller-runtime"
            controller = container "spark-operator-controller" "Reconciles SparkApplication, ScheduledSparkApplication, and SparkConnect CRs into driver/executor pods, services, and supporting resources" "Go Operator (Deployment)"
            webhook = container "spark-operator-webhook" "Validates and mutates SparkApplication submissions and injects Spark configuration into pods via admission webhooks (failurePolicy: Fail)" "Go Service (Deployment)"
            webhookService = container "spark-operator-webhook-svc" "ClusterIP service exposing webhook on 443/TCP" "Kubernetes Service"
        }

        odhOperator = softwareSystem "ODH Operator" "OpenShift AI platform operator that manages component lifecycle" "Internal ODH"
        certManager = softwareSystem "cert-manager" "Provisions and rotates TLS certificates for webhook endpoints" "External"
        prometheusOperator = softwareSystem "Prometheus Operator" "Manages PodMonitor resources for metrics collection" "External"
        kubernetesAPI = softwareSystem "Kubernetes API Server" "Central API for all cluster resource operations" "External"
        odhPlatformUtils = softwareSystem "odh-platform-utilities" "Go library providing platform detection, manifest rendering, and deployment helpers" "Internal ODH"

        # Relationships - External
        user -> sparkOperator "Creates SparkApplication / ScheduledSparkApplication / SparkConnect CRs via kubectl"
        odhOperator -> sparkOperator "Creates SparkOperator CR (cluster-scoped singleton)"

        # Relationships - Internal
        moduleController -> kubernetesAPI "Creates/manages CRDs, RBAC, Deployments, Services, NetworkPolicies" "HTTPS/6443 TLS 1.2+ SA Token"
        moduleController -> certManager "Creates Certificate/Issuer CRs for webhook TLS" "Kubernetes API"
        moduleController -> controller "Deploys and manages lifecycle" "Kubernetes API"
        moduleController -> webhook "Deploys and manages lifecycle" "Kubernetes API"

        controller -> kubernetesAPI "Creates driver/executor pods, services, ConfigMaps, PDBs, ingresses" "HTTPS/6443 TLS 1.2+ SA Token"
        webhook -> kubernetesAPI "Reads ResourceQuotas, SparkApplications; manages secrets and webhook configs" "HTTPS/6443 TLS 1.2+ SA Token"

        kubernetesAPI -> webhookService "Sends admission reviews for SparkApplication and Pod resources" "HTTPS/443 TLS"
        webhookService -> webhook "Routes admission requests" "TCP/443"

        certManager -> sparkOperator "Provisions TLS certificates to spark-operator-webhook-certs Secret"
        prometheusOperator -> sparkOperator "Scrapes metrics via PodMonitor"

        moduleController -> odhPlatformUtils "Uses PlatformObject interface for status/conditions/release coordination" "Go library import"
    }

    views {
        systemContext sparkOperator "SystemContext" {
            include *
            autoLayout
        }

        container sparkOperator "Containers" {
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
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
