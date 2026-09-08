workspace {
    model {
        orchestrator = person "FMS Guardrails Orchestrator" "Sends content analysis requests to detectors for guardrail evaluation"

        guardrailsDetectors = softwareSystem "Guardrails Detectors" "Text content analysis microservices — regex, HuggingFace inference, and LLM-as-Judge — deployed as KServe serving runtimes" {
            builtInDetector = container "Built-in Detector" "Regex and file-type pattern matching for content analysis" "Python/FastAPI" "detector"
            hfDetector = container "HuggingFace Detector" "ML model inference using AutoModelForSequenceClassification or GraniteForCausalLM" "Python/FastAPI/uvicorn" "detector"
            judgeDetector = container "LLM Judge Detector" "Delegates content evaluation to vLLM via vllm-judge library" "Python/FastAPI/uvicorn" "detector"
            baseAPI = container "DetectorBaseAPI" "Common base class providing health endpoints, error handling, and Prometheus instrumentation" "Python/FastAPI" "shared"
        }

        kserve = softwareSystem "KServe" "Model serving platform managing ServingRuntime lifecycle" "Platform"
        vllm = softwareSystem "vLLM Inference Server" "LLM inference server (qwen2-predictor) for content evaluation" "Platform"
        minio = softwareSystem "MinIO" "Object storage for HuggingFace model artifacts" "Internal"
        prometheus = softwareSystem "Prometheus" "Metrics collection and monitoring" "Platform"

        # Relationships - System Context
        orchestrator -> guardrailsDetectors "POST /api/v1/text/contents" "HTTP 8000/8080"
        guardrailsDetectors -> vllm "Forwards evaluation requests" "HTTP/8080"
        guardrailsDetectors -> minio "Loads model artifacts" "TCP/9000"
        kserve -> guardrailsDetectors "Manages ServingRuntime lifecycle" "Kubernetes API"
        prometheus -> guardrailsDetectors "Scrapes metrics" "HTTP GET /metrics"

        # Relationships - Container Level
        orchestrator -> builtInDetector "POST /api/v1/text/contents" "HTTP/8080"
        orchestrator -> hfDetector "POST /api/v1/text/contents" "HTTP/8000"
        orchestrator -> judgeDetector "POST /api/v1/text/contents" "HTTP/8000"

        builtInDetector -> baseAPI "extends" ""
        hfDetector -> baseAPI "extends" ""
        judgeDetector -> baseAPI "extends" ""

        hfDetector -> minio "Loads pre-trained models" "TCP/9000"
        judgeDetector -> vllm "Delegates evaluation via vllm-judge" "HTTP/8080"
    }

    views {
        systemContext guardrailsDetectors "SystemContext" {
            include *
            autoLayout
        }

        container guardrailsDetectors "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Platform" {
                background #999999
                color #ffffff
            }
            element "Internal" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "detector" {
                background #4a90e2
                color #ffffff
            }
            element "shared" {
                background #6baed6
                color #ffffff
            }
        }
    }
}
