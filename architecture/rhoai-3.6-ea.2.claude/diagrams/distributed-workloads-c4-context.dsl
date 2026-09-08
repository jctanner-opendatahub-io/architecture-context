workspace {
    model {
        dataScientist = person "Data Scientist" "Creates and runs distributed training jobs using RHOAI"
        mlEngineer = person "ML Engineer" "Builds and optimizes training pipelines"

        distributedWorkloads = softwareSystem "Distributed Workloads" "Container image factory producing OpenMPI-enabled training runtimes and Jupyter-based universal training images across CUDA, ROCm, and CPU variants" {
            runtimeImages = container "Runtime Training Images" "Pre-configured training environments with OpenMPI for multi-node PyTorch training via SSH-based MPI coordination" "Container Image (AIPCC Base)"
            universalImages = container "Universal Training Images" "Jupyter notebook-ready environments for interactive and batch distributed training workloads" "Container Image (Workbench Base)"
            exampleManifests = container "Example Manifests" "Kubernetes manifests demonstrating distributed training workflows with MinIO, NFS, and KServe" "YAML Manifests"
            testSuite = container "Go Test Suite" "End-to-end tests validating image correctness against platform operators" "Go Test Code"
        }

        kubeflowTrainer = softwareSystem "Kubeflow Trainer v2" "Manages distributed training job lifecycle on Kubernetes" "Platform Operator"
        kueue = softwareSystem "Kueue" "Kubernetes-native job queuing and admission control" "Platform Operator"
        kubeRay = softwareSystem "KubeRay" "Kubernetes operator for Ray cluster management" "Platform Operator"
        kubernetes = softwareSystem "Kubernetes" "Container orchestration platform" "Infrastructure"
        konflux = softwareSystem "Konflux" "Build system with hermetic dependency resolution (Hermeto/cachi2)" "Build System"

        aipccBaseImages = softwareSystem "AIPCC Base Images" "Pre-configured base images with CUDA/ROCm, OpenSSL, FIPS-compatible crypto" "Internal Image Registry"
        workbenchBaseImages = softwareSystem "Workbench Base Images" "UBI-based Jupyter minimal images for notebook environments" "Internal Image Registry"

        minioStorage = softwareSystem "MinIO" "S3-compatible object storage for training data and model artifacts" "Example Storage"
        nfsServer = softwareSystem "NFS Server" "Shared file system for training checkpoints and data" "Example Storage"
        kserve = softwareSystem "KServe" "Serverless ML inference platform for model serving" "Platform Component"

        # Relationships
        dataScientist -> distributedWorkloads "Submits distributed training jobs using"
        mlEngineer -> distributedWorkloads "Builds and tests training images"

        kubeflowTrainer -> runtimeImages "Schedules training pods using" "Kubernetes Pod Spec"
        kubeflowTrainer -> universalImages "Schedules training pods using" "Kubernetes Pod Spec"
        kueue -> runtimeImages "Queues and admits workloads for" "Admission Control"
        kubeRay -> runtimeImages "Orchestrates Ray jobs using" "Ray Cluster Spec"

        runtimeImages -> minioStorage "Downloads/uploads training data" "S3 API / 9000/TCP"
        runtimeImages -> nfsServer "Reads/writes shared checkpoints" "NFS / 2049/TCP"
        runtimeImages -> kubernetes "Reports status, discovers resources" "HTTPS / 6443/TCP"
        universalImages -> minioStorage "Accesses training data" "S3 API / 9000/TCP"
        universalImages -> kubernetes "Reports status" "HTTPS / 6443/TCP"

        aipccBaseImages -> runtimeImages "Provides base layer for" "FROM directive"
        workbenchBaseImages -> universalImages "Provides base layer for" "FROM directive"
        konflux -> runtimeImages "Builds with hermetic prefetch" "cachi2.env"
        konflux -> universalImages "Builds with hermetic prefetch" "cachi2.env"

        testSuite -> kubeflowTrainer "Validates integration with" "Go test"
        testSuite -> kueue "Validates integration with" "Go test"
        testSuite -> kubeRay "Validates integration with" "Go test"

        exampleManifests -> kserve "Defines ServingRuntime for" "YAML manifest"
    }

    views {
        systemContext distributedWorkloads "SystemContext" {
            include *
            autoLayout
        }

        container distributedWorkloads "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Platform Operator" {
                background #9b59b6
                color #ffffff
            }
            element "Infrastructure" {
                background #999999
                color #ffffff
            }
            element "Build System" {
                background #e74c3c
                color #ffffff
            }
            element "Internal Image Registry" {
                background #f5a623
                color #ffffff
            }
            element "Example Storage" {
                background #e8e8e8
                color #333333
            }
            element "Platform Component" {
                background #7ed321
                color #ffffff
            }
        }
    }
}
