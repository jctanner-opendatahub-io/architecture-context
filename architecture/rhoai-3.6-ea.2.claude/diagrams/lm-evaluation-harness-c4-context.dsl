workspace {
    model {
        dataScientist = person "Data Scientist / ML Engineer" "Requests model evaluations via the RHOAI platform"

        lmesOperator = softwareSystem "LMES Operator (trustyai-service-operator)" "Creates and manages evaluation Jobs on Kubernetes" "Internal RHOAI"

        lmEvalHarness = softwareSystem "lm-evaluation-harness" "Batch-oriented Python framework for evaluating language models, packaged as a Kubernetes Job image (odh-ta-lmes-job-rhel9)" {
            cli = container "lm-eval CLI" "Console entrypoint for evaluation execution" "Python / lm_eval.__main__:cli_evaluate"
            modelBackends = container "Model Backends" "Abstraction layer supporting HuggingFace, OpenAI, Anthropic, WatsonX, vLLM" "Python"
            taskFramework = container "Task Framework" "Unitxt-based evaluation task definitions and benchmark loading" "Python / Unitxt"
            evalHubSDK = container "eval-hub-sdk" "Integration with RHOAI evaluation hub" "Python / ~1.0.0"
        }

        openaiAPI = softwareSystem "OpenAI-Compatible API" "Language model inference (OpenAI, vLLM endpoints)" "External"
        anthropicAPI = softwareSystem "Anthropic API" "Anthropic language model inference" "External"
        watsonxAPI = softwareSystem "IBM WatsonX API" "IBM WatsonX language model inference" "External"
        huggingfaceHub = softwareSystem "HuggingFace Hub" "Benchmark datasets and model weights (datasets-server.huggingface.co)" "External"
        s3Storage = softwareSystem "S3-Compatible Storage" "Dataset and model artifact storage (AWS S3 / IBM COS)" "External"
        outputStorage = softwareSystem "Output Storage" "Evaluation results storage (PVC / local volume)" "Infrastructure"

        dataScientist -> lmesOperator "Triggers evaluation via RHOAI UI/API"
        lmesOperator -> lmEvalHarness "Creates K8s Job with env vars and volumes" "Kubernetes Job API"

        lmEvalHarness -> openaiAPI "Sends inference requests" "HTTPS / API key"
        lmEvalHarness -> anthropicAPI "Sends inference requests" "HTTPS / API key"
        lmEvalHarness -> watsonxAPI "Sends inference requests" "HTTPS / API key"
        lmEvalHarness -> huggingfaceHub "Downloads benchmark datasets" "HTTPS/443 / HF_TOKEN"
        lmEvalHarness -> s3Storage "Downloads/uploads data artifacts" "HTTPS / AWS IAM"
        lmEvalHarness -> outputStorage "Writes evaluation results" "Filesystem"

        cli -> modelBackends "Dispatches inference to configured backend"
        cli -> taskFramework "Loads evaluation tasks and benchmarks"
        cli -> evalHubSDK "Integrates with eval hub"
        modelBackends -> openaiAPI "Inference requests" "HTTPS"
        modelBackends -> anthropicAPI "Inference requests" "HTTPS"
        modelBackends -> watsonxAPI "Inference requests" "HTTPS"
        taskFramework -> huggingfaceHub "Downloads datasets" "HTTPS/443"
    }

    views {
        systemContext lmEvalHarness "SystemContext" {
            include *
            autoLayout
        }

        container lmEvalHarness "Containers" {
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
            element "Person" {
                shape Person
                background #4a90e2
                color #ffffff
            }
        }
    }
}
