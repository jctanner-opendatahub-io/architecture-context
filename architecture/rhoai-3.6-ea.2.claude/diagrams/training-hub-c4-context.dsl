workspace {
    model {
        user = person "Data Scientist" "Creates and runs ML training jobs via notebooks or scripts"

        trainingHub = softwareSystem "Training Hub" "Unified algorithm-focused interface for LM training techniques (SFT, LoRA, GRPO, GEPA)" {
            registry = container "AlgorithmRegistry" "Factory-based algorithm/backend selection" "Python"
            sftBackend = container "SFT Backend" "Supervised fine-tuning via InstructLab Training with torchrun" "Python"
            osftBackend = container "OSFT Backend" "Optimized SFT via Mini-Trainer" "Python"
            loraBackend = container "LoRA Backend" "Parameter-efficient LoRA training via Unsloth" "Python"
            grpoBackend = container "GRPO Backend" "RL from verifiable rewards via ART/OpenPipe with co-located vLLM" "Python"
            verlBackend = container "VeRL Backend" "Distributed GRPO training via VeRL framework" "Python"
            gepaBackend = container "GEPA Backend" "Gradient-free prompt optimization via evolutionary search" "Python"
            gepaMLflowBackend = container "GEPA MLflow Backend" "Prompt optimization with MLflow integration" "Python"
            callbackSystem = container "TrainingHubCallback" "Unified callback abstraction across all backends" "Python"
            memEstimator = container "Memory Estimator" "GPU memory estimation utilities" "Python"
        }

        instructlabTraining = softwareSystem "InstructLab Training" "Torchrun-based distributed training library" "Internal"
        miniTrainer = softwareSystem "Mini-Trainer" "Optimized SFT training library" "Internal"
        artOpenPipe = softwareSystem "ART (OpenPipe)" "Framework for co-located vLLM inference + LoRA training" "Internal"
        vllm = softwareSystem "vLLM" "High-throughput LLM inference engine" "External"
        unsloth = softwareSystem "Unsloth" "Parameter-efficient LoRA training" "External"
        verl = softwareSystem "VeRL" "Distributed GRPO training framework" "External"
        gepaLib = softwareSystem "GEPA Library" "Gradient-free evolutionary prompt optimization" "External"
        itsHub = softwareSystem "ITS Hub" "Inference-time scaling algorithms (BestOfN, SelfConsistency)" "Internal"
        litellm = softwareSystem "LiteLLM" "Unified LLM API client supporting OpenAI-compatible endpoints" "External"
        openaiAPI = softwareSystem "OpenAI-compatible API" "LLM inference endpoint for prompt optimization" "External"
        mlflowServer = softwareSystem "MLflow Tracking Server" "Experiment tracking, metric logging, prompt registry" "External"
        pytorch = softwareSystem "PyTorch" "Deep learning framework" "External"
        transformers = softwareSystem "Transformers" "Hugging Face model library" "External"

        user -> trainingHub "Invokes training algorithms" "Python API"
        trainingHub -> instructlabTraining "Delegates SFT training" "Python Library"
        trainingHub -> miniTrainer "Delegates optimized SFT" "Python Library"
        trainingHub -> artOpenPipe "Delegates GRPO training" "Python Library"
        trainingHub -> unsloth "Uses for LoRA parameter updates" "Python Library"
        trainingHub -> verl "Delegates distributed GRPO" "Python Library"
        trainingHub -> gepaLib "Uses for evolutionary search" "Python Library"
        trainingHub -> itsHub "Uses for inference-time scaling" "Python Library"
        trainingHub -> litellm "Routes LLM inference requests" "Python Library"
        trainingHub -> vllm "Co-located inference engine" "In-process"
        litellm -> openaiAPI "Sends inference requests" "HTTP/HTTPS, Bearer Token"
        trainingHub -> mlflowServer "Logs experiments, reads prompt templates" "HTTP/HTTPS REST"
        trainingHub -> pytorch "Uses for tensor operations and training" "Python Library"
        trainingHub -> transformers "Uses for model loading and tokenization" "Python Library"
    }

    views {
        systemContext trainingHub "SystemContext" {
            include *
            autoLayout
        }

        container trainingHub "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Internal" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                background #4a90e2
                color #ffffff
                shape Person
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
