workspace {
    model {
        user = person "Data Scientist" "Creates and manages Jupyter notebook workbenches"

        kubeflow = softwareSystem "Kubeflow Notebook Controllers" "Manages lifecycle of Jupyter notebook workbenches on RHOAI, reconciling Notebook CRs into StatefulSets with sidecar injection for authentication, network isolation, and Gateway API routing" {
            notebookController = container "Notebook Controller" "Reconciles Notebook CRs into StatefulSets, Services, and manages idle culling" "Go controller-runtime operator"
            odhController = container "ODH Notebook Controller" "Extends upstream with OpenShift-specific capabilities: kube-rbac-proxy injection, NetworkPolicies, Gateway API routing, Elyra secrets" "Go controller-runtime operator"
            mutatingWebhook = container "Mutating Webhook" "Injects kube-rbac-proxy sidecar, proxy env vars, and Elyra pipeline secrets on Notebook CREATE/UPDATE" "Admission Webhook /mutate-notebook-v1"
            validatingWebhook = container "Validating Webhook" "Validates Notebook CRs on CREATE/UPDATE" "Admission Webhook /validate-notebook-v1"
            conversionWebhook = container "Conversion Webhook" "Converts between Notebook API versions (v1, v1alpha1, v1beta1)" "Admission Webhook /convert"
        }

        k8sAPI = softwareSystem "Kubernetes API Server" "Cluster control plane, admission webhook invocation, resource storage" "External"
        gatewayAPI = softwareSystem "Gateway API" "Manages HTTPRoutes and ReferenceGrants for notebook ingress routing via data-science-gateway" "External"
        dspa = softwareSystem "Data Science Pipelines Operator" "Provides DataSciencePipelinesApplication CRs for Elyra pipeline runtime configuration" "Internal RHOAI"
        openshiftAPI = softwareSystem "OpenShift Platform APIs" "APIServer TLS profile, Proxy config, Image Streams, Routes, OAuthClients" "External"

        user -> kubeflow "Creates Notebook CRs via kubectl/dashboard"
        kubeflow -> k8sAPI "Creates StatefulSets, Services, NetworkPolicies, Secrets" "HTTPS/6443"
        kubeflow -> gatewayAPI "Creates HTTPRoutes and ReferenceGrants for notebook routing" "Kubernetes API"
        kubeflow -> dspa "Reads DSPA CRs to provision Elyra pipeline secrets" "Kubernetes API"
        kubeflow -> openshiftAPI "Reads TLS profile, proxy config, image streams" "HTTPS/6443"

        notebookController -> k8sAPI "Reconciles StatefulSets, Services" "HTTPS"
        odhController -> k8sAPI "Manages NetworkPolicies, RBAC, Secrets" "HTTPS"
        odhController -> mutatingWebhook "Registers webhook"
        odhController -> validatingWebhook "Registers webhook"
        odhController -> conversionWebhook "Registers webhook"
        k8sAPI -> mutatingWebhook "Invokes on Notebook CREATE/UPDATE" "HTTPS/8443"
        k8sAPI -> validatingWebhook "Invokes on Notebook CREATE/UPDATE" "HTTPS/8443"
    }

    views {
        systemContext kubeflow "SystemContext" {
            include *
            autoLayout
        }

        container kubeflow "Containers" {
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
