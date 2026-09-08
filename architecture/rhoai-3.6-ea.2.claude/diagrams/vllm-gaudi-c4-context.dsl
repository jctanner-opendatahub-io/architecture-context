workspace {
    model {
        user = person "Data Scientist / Application" "Sends inference requests to deployed models"

        vllmGaudi = softwareSystem "vllm-gaudi" "Intel Gaudi HPU plugin for vLLM, providing hardware-accelerated LLM inference via OpenAI-compatible API" {
            apiServer = container "vLLM API Server" "OpenAI-compatible inference endpoint (api_server entrypoint)" "Python / vLLM"
            gaudiPlugin = container "vllm_gaudi Plugin" "HPU device backend implementing Gaudi-specific tensor operations" "Python Package"
            synapseRuntime = container "SynapseAI Runtime" "Intel Habana driver stack and HPU runtime libraries v1.23.0" "Native Library"
        }

        kserve = softwareSystem "KServe" "Serverless ML inference platform — manages pod lifecycle, networking, and ingress for serving runtimes" "Internal RHOAI"
        istio = softwareSystem "Istio / Service Mesh" "Service mesh providing mTLS, traffic management, and auth policies" "Internal RHOAI"
        vllmUpstream = softwareSystem "vLLM (upstream)" "Core LLM serving framework, cloned at build time from vllm-project/vllm@v0.16.0" "External"
        gaudiHardware = softwareSystem "Intel Gaudi HPU" "Hardware accelerator for LLM inference" "Infrastructure"
        modelStorage = softwareSystem "Model Storage" "Volume-mounted storage containing model weights" "Infrastructure"
        konflux = softwareSystem "Konflux Build" "CI/CD pipeline that builds the multi-stage container image on UBI 9" "Build System"

        user -> kserve "Sends inference requests" "HTTPS/443"
        kserve -> vllmGaudi "Manages serving runtime pod" "Container lifecycle"
        vllmGaudi -> gaudiHardware "Executes tensor operations" "SynapseAI Runtime API"
        vllmGaudi -> modelStorage "Loads model weights at startup" "Filesystem read"
        kserve -> istio "Delegates auth and mTLS" "Service mesh"
        konflux -> vllmUpstream "Clones at build time" "Git/HTTPS"
        konflux -> vllmGaudi "Builds container image" "Multi-stage Docker"

        apiServer -> gaudiPlugin "Delegates HPU operations" "Python in-process"
        gaudiPlugin -> synapseRuntime "Calls Gaudi runtime" "Native API"
    }

    views {
        systemContext vllmGaudi "SystemContext" {
            include *
            autoLayout
        }

        container vllmGaudi "Containers" {
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
            element "Infrastructure" {
                background #f5a623
                color #ffffff
            }
            element "Build System" {
                background #9b59b6
                color #ffffff
            }
        }
    }
}
