workspace {
    model {
        operator = person "Cluster Administrator" "Runs preflight validation before AI workload deployment"

        rhaiiValidator = softwareSystem "rhaii-cluster-validation" "Preflight validation CLI for xKS clusters — verifies GPU availability, RDMA connectivity, network bandwidth, CRDs, and inference readiness" {
            controller = container "Controller (CLI)" "Orchestrates validation lifecycle — cleanup, RBAC provisioning, Job deployment, result collection, reporting" "Go CLI (Cobra)"
            agent = container "Agent (Probe Jobs)" "Executes hardware checks on GPU nodes — GPU driver, ECC, RDMA devices, bandwidth, PCI topology" "Go Binary (agent mode)"
        }

        kubernetes = softwareSystem "Kubernetes API" "Cluster control plane — resource management and scheduling" "External"
        gpuNodes = softwareSystem "GPU Worker Nodes" "Physical/virtual nodes with GPU and RDMA hardware" "External"

        # Relationships
        operator -> rhaiiValidator "Invokes rhaii-validator or kubectl rhaii-validate"
        rhaiiValidator -> kubernetes "Creates Namespaces, ServiceAccounts, ClusterRoles, Jobs, ConfigMaps" "HTTPS/6443 TLS 1.2+"
        controller -> kubernetes "Manages validation lifecycle via kubeconfig credentials" "HTTPS/6443"
        controller -> agent "Deploys as Kubernetes Jobs on GPU nodes"
        agent -> gpuNodes "Reads host devices via privileged SCC" "/sys/class/infiniband, /sys/bus/pci, nvidia-smi"
        kubernetes -> agent "Schedules Jobs on GPU-equipped nodes" "batch/v1"
        controller -> kubernetes "Collects results via log API and ConfigMaps" "HTTPS/6443"
    }

    views {
        systemContext rhaiiValidator "SystemContext" {
            include *
            autoLayout
        }

        container rhaiiValidator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438dd5
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape person
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
