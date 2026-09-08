workspace {
    model {
        operator = person "Platform Operator" "Plans and deploys LLM workloads on Kubernetes clusters"

        llmDPlanner = softwareSystem "llm-d-planner" "LLM deployment planning and recommendation service for Kubernetes clusters" {
            ui = container "Streamlit UI" "Browser-based interface for deployment planning workflows" "Python / Streamlit" "Web Browser"
            backend = container "FastAPI Backend" "REST API for capacity planning, GPU estimation, intent extraction, deployment generation" "Python / FastAPI / Uvicorn"
            ollamaInstance = container "Ollama Instance" "Local LLM inference sidecar for natural-language processing" "Ollama"
            benchmarkDB = container "Benchmark Database" "Local database of GPU and model performance benchmarks" "SQLite"
            gpuDetector = container "GPU Detector" "Discovers GPU types on cluster nodes via Kubernetes API with TTL cache" "Python"
            llmFactory = container "LLM Provider Factory" "Provider-agnostic LLM client factory (Ollama, OpenAI, Vertex AI)" "Python"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Cluster API server for resource management and node discovery" "External"
        openAIAPI = softwareSystem "OpenAI API" "Cloud LLM inference service" "External"
        vertexAI = softwareSystem "Vertex AI (Anthropic Claude)" "Google Cloud hosted Anthropic Claude models" "External"
        huggingFaceHub = softwareSystem "HuggingFace Hub" "Model metadata and configuration repository" "External"
        openshiftServiceCA = softwareSystem "OpenShift Service CA" "CA bundle injection for internal TLS trust" "Internal Platform"

        # Operator interactions
        operator -> llmDPlanner "Plans LLM deployments via browser UI and REST API" "HTTPS"

        # Internal container relationships
        ui -> backend "Forwards user requests" "HTTP/8000"
        backend -> ollamaInstance "Sends LLM inference requests (default provider)" "HTTP/11434"
        backend -> benchmarkDB "Queries performance benchmarks" "SQLite"
        backend -> gpuDetector "Requests available GPU types" "Internal"
        backend -> llmFactory "Creates LLM provider clients" "Internal"
        llmFactory -> ollamaInstance "Local LLM inference" "HTTP/11434"

        # External dependencies
        gpuDetector -> kubernetesAPI "Lists nodes with GPU labels (cached 300s TTL)" "HTTPS/6443"
        llmFactory -> openAIAPI "LLM inference (when LLM_PROVIDER=openai)" "HTTPS"
        llmFactory -> vertexAI "LLM inference (when LLM_PROVIDER=vertex)" "HTTPS/443"
        backend -> huggingFaceHub "Fetches model metadata and configs" "HTTPS"
        backend -> kubernetesAPI "Applies generated deployment manifests" "HTTPS/6443"
    }

    views {
        systemContext llmDPlanner "SystemContext" {
            include *
            autoLayout
        }

        container llmDPlanner "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Person" {
                shape Person
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
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal Platform" {
                background #7ed321
                color #ffffff
            }
            element "Web Browser" {
                shape WebBrowser
            }
        }
    }
}
