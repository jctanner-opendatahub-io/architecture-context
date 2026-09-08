workspace {
    model {
        admin = person "Cluster Admin" "Configures Kueue queuing system and resource quotas"
        datascientist = person "Data Scientist" "Submits ML training jobs and batch workloads"

        kueueOperator = softwareSystem "Kueue Operator" "Two-tier operator managing Kueue workload queuing for batch and ML training workloads on OpenShift" {
            operator = container "openshift-kueue-operator" "Watches Kueue CRs and reconciles the controller-manager deployment with all dependent resources" "Go Operator (library-go)" {
                tags "Tier1"
            }
            controllerManager = container "kueue-controller-manager" "Manages workload queuing, fair-sharing, and resource quota across 7 job frameworks" "Go Controller (controller-runtime)" {
                tags "Tier2"
            }
            webhookServer = container "Webhook Server" "34 mutating/validating admission webhooks intercepting workload creation across all supported frameworks" "Admission Webhook (port 9443/TLS)" {
                tags "Tier2"
            }
            visibilityAPI = container "Visibility API Server" "Provides pending workload query API for observability" "API Server (port 8082)" {
                tags "Tier2"
            }
            metricsEndpoint = container "Metrics Endpoint" "Exposes Prometheus metrics with TokenReview/SAR authentication" "Metrics (port 8443/TLS)" {
                tags "Tier2"
            }
        }

        k8sAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management" {
            tags "External"
        }
        certManager = softwareSystem "cert-manager" "TLS certificate provisioning for webhook server" {
            tags "Platform"
        }
        prometheusOp = softwareSystem "prometheus-operator" "Metrics collection and monitoring via ServiceMonitor CRs" {
            tags "Platform"
        }
        kubeflowTraining = softwareSystem "Kubeflow Training Operator" "Manages distributed ML training jobs (MPI, PyTorch, TF, XGBoost, Paddle)" {
            tags "Platform"
        }
        rayOperator = softwareSystem "Ray Operator" "Manages Ray clusters and jobs for distributed computing" {
            tags "Platform"
        }
        codeflare = softwareSystem "CodeFlare Operator" "Manages AppWrapper resources for multi-cluster job dispatching" {
            tags "Platform"
        }
        jobsetController = softwareSystem "JobSet Controller" "Manages JobSet resources for coordinated job groups" {
            tags "Platform"
        }

        # User interactions
        admin -> kueueOperator "Creates Kueue CR to deploy queuing system" "kubectl"
        admin -> kueueOperator "Configures ClusterQueues, ResourceFlavors, Cohorts" "kubectl"
        datascientist -> k8sAPI "Submits Jobs, PyTorchJobs, RayJobs, etc." "kubectl/SDK"

        # Internal flows
        operator -> k8sAPI "Watches Kueue CRs, creates/updates CRDs, RBAC, deployments" "HTTPS/6443"
        operator -> certManager "Creates Certificate and Issuer CRs for webhook TLS" "CRD CRUD"
        operator -> prometheusOp "Creates ServiceMonitor CR for metrics scraping" "CRD CRUD"
        controllerManager -> k8sAPI "Watches/manages ClusterQueues, Workloads, nodes" "HTTPS/6443"
        k8sAPI -> webhookServer "Sends admission requests for workload creation/update" "HTTPS/443→9443 TLS"

        # External integrations
        controllerManager -> kubeflowTraining "Queues and manages Kubeflow training jobs" "CRD watch/patch"
        controllerManager -> rayOperator "Queues and manages Ray clusters/jobs" "CRD watch/patch"
        controllerManager -> codeflare "Queues and manages AppWrappers" "CRD watch/patch"
        controllerManager -> jobsetController "Queues and manages JobSets" "CRD watch/patch"
        prometheusOp -> metricsEndpoint "Scrapes metrics" "HTTPS/8443 TokenReview"
    }

    views {
        systemContext kueueOperator "SystemContext" {
            include *
            autoLayout
        }

        container kueueOperator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Platform" {
                background #7ed321
                color #ffffff
            }
            element "Tier1" {
                background #4a90e2
            }
            element "Tier2" {
                background #e27a4a
            }
        }
    }
}
