workspace {
    model {
        user = person "Application Developer / Data Scientist" "Deploys and configures guardrails for LLM-based applications"
        client = person "Client Application" "Sends chat completion or guardrail check requests"

        nemoGuardrails = softwareSystem "NeMo-Guardrails" "Programmable safety rails for LLM-based conversational systems" {
            server = container "GuardrailsApp" "FastAPI-based guardrails server exposing OpenAI-compatible API" "Python/FastAPI/uvicorn" {
                chatEndpoint = component "/v1/chat/completions" "OpenAI-compatible chat completions with guardrails" "FastAPI Route"
                checksEndpoint = component "/v1/checks" "Colang 1.0 rail evaluation" "FastAPI Route"
                guardrailChecksEndpoint = component "/v1/guardrail/checks" "Role-based message routing to input/output/tool rails" "FastAPI Route"
                healthEndpoint = component "/healthz" "Health check endpoint" "FastAPI Route"
            }
            railsEngine = container "LLMRails Engine" "Evaluates messages against Colang-defined safety rails" "Python/Colang"
            colangConfig = container "Colang Configuration" "Declarative safety rail definitions" "Colang Files/YAML"
            cachedModels = container "Pre-cached Models" "MiniLM, Snowflake Arctic, spaCy, NLTK bundled from Red Hat modelcar images" "ONNX/PyTorch"
        }

        alignScoreService = softwareSystem "AlignScore Service" "Fact-checking evaluation microservice" "Auxiliary" {
            tags "Auxiliary"
        }

        jailbreakService = softwareSystem "Jailbreak Detection Service" "Jailbreak heuristic analysis microservice" "Auxiliary" {
            tags "Auxiliary"
        }

        openAI = softwareSystem "OpenAI API" "LLM inference provider" "External" {
            tags "External"
        }

        azureOpenAI = softwareSystem "Azure OpenAI" "LLM inference and embedding provider" "External" {
            tags "External"
        }

        otelCollector = softwareSystem "OpenTelemetry Collector" "Distributed tracing and observability" "External" {
            tags "External"
        }

        rhoaiPlatform = softwareSystem "RHOAI Platform" "Provides service mesh, authentication, and network policies" "Internal RHOAI" {
            tags "Internal"
        }

        # Relationships
        client -> nemoGuardrails "Sends chat/check requests" "HTTP/8000"
        user -> nemoGuardrails "Configures guardrails via Colang files"

        nemoGuardrails -> openAI "Forwards approved LLM requests" "HTTPS/443, API Key"
        nemoGuardrails -> azureOpenAI "Forwards approved LLM requests" "HTTPS/443, API Key"
        nemoGuardrails -> alignScoreService "Fact-checking evaluation" "HTTP/5000"
        nemoGuardrails -> jailbreakService "Jailbreak detection" "HTTP/1337"
        nemoGuardrails -> otelCollector "Exports traces (optional)" "OTLP gRPC/HTTP"

        rhoaiPlatform -> nemoGuardrails "Provides authentication, mTLS, network policy"

        # Internal relationships
        server -> railsEngine "Evaluates requests against rails"
        railsEngine -> colangConfig "Loads rail definitions"
        railsEngine -> cachedModels "Uses for embedding/NLP evaluation"
    }

    views {
        systemContext nemoGuardrails "SystemContext" {
            include *
            autoLayout
        }

        container nemoGuardrails "Containers" {
            include *
            autoLayout
        }

        component server "Components" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Auxiliary" {
                background #9b59b6
                color #ffffff
            }
            element "Internal" {
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
            element "Component" {
                background #85bbf0
                color #000000
            }
        }
    }
}
