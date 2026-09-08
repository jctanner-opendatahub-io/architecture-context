workspace {
    model {
        dataScientist = person "Data Scientist" "Creates experiments, logs metrics, manages models, and deploys inference endpoints"
        mlEngineer = person "ML Engineer" "Manages MLflow projects, runs training jobs, configures AI gateway"

        mlflow = softwareSystem "MLflow" "Tracking server and model registry with AI gateway proxy, experiment tracking, model versioning, and Kubernetes-native authentication" {
            trackingServer = container "MLflow Tracking Server" "Flask/FastAPI application serving 48 HTTP endpoints for tracking, registry, gateway, and assistant APIs" "Python 3.12 / gunicorn / uvicorn"
            k8sAuthPlugin = container "kubernetes-auth Plugin" "Authenticates requests using Kubernetes service account bearer tokens with namespace-based workspace isolation" "mlflow-kubernetes-plugins==1.5.0"
            aiGateway = container "AI Gateway" "Proxies requests to upstream LLM providers with provider-specific SDK clients" "FastAPI"
            mcpServer = container "MCP Server" "Model Context Protocol server for model context management" "FastAPI"
            assistantAPI = container "Assistant API" "AI-assisted workflows with provider health checks and session management" "FastAPI"
            webUI = container "Web UI" "React-based web interface for experiment tracking and model management" "Node.js / React"
            mlflowSkinny = container "mlflow-skinny" "Lightweight Python client for tracking operations" "Python SDK"
            mlflowTracing = container "mlflow-tracing" "Tracing SDK for instrumenting code and models" "Python SDK"
        }

        kubernetesAPI = softwareSystem "Kubernetes API" "Orchestrates containers and manages cluster resources" "External"
        s3Storage = softwareSystem "S3-Compatible Storage" "Object storage for model artifacts and experiment data" "External"
        gcsStorage = softwareSystem "Google Cloud Storage" "Cloud object storage for model artifacts" "External"
        openAI = softwareSystem "OpenAI API" "Large language model inference service" "External"
        awsBedrock = softwareSystem "AWS Bedrock" "Managed AI model inference service" "External"
        otherAIProviders = softwareSystem "Other AI Providers" "Cohere, Anthropic, Mistral, Groq, DeepSeek, xAI, OpenRouter, Ollama" "External"

        # User interactions
        dataScientist -> mlflow "Logs experiments, registers models, queries tracking API" "HTTP/5000 Bearer Token"
        mlEngineer -> mlflow "Manages projects, configures gateway, submits jobs" "HTTP/5000 Bearer Token"

        # Internal container relationships
        trackingServer -> k8sAuthPlugin "Validates requests via" "Plugin framework"
        trackingServer -> aiGateway "Routes gateway requests to"
        trackingServer -> mcpServer "Routes MCP requests to"
        trackingServer -> assistantAPI "Routes assistant requests to"

        # External integrations
        mlflow -> kubernetesAPI "Creates Jobs for project execution" "HTTPS/443 SA Token"
        mlflow -> s3Storage "Stores and retrieves model artifacts" "HTTPS/443 AWS IAM"
        mlflow -> gcsStorage "Stores and retrieves model artifacts" "HTTPS/443 GCP Auth"
        aiGateway -> openAI "Proxies chat/completion/embedding requests" "HTTPS/443 Bearer Token"
        aiGateway -> awsBedrock "Proxies inference requests" "HTTPS/443 AWS SigV4"
        aiGateway -> otherAIProviders "Proxies inference requests" "HTTPS/443 Bearer Token"
    }

    views {
        systemContext mlflow "SystemContext" {
            include *
            autoLayout
        }

        container mlflow "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
