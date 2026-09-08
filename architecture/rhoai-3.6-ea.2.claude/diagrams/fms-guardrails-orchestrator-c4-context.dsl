workspace {
    model {
        user = person "Application Client" "Sends inference requests requiring content safety orchestration"

        guardrailsOrchestrator = softwareSystem "fms-guardrails-orchestrator" "Rust-based orchestration service that coordinates content safety detection and text generation" {
            guardrailsServer = container "Guardrails Server" "Axum HTTP server exposing v1/v2 REST API for classification, detection, and generation orchestration" "Rust (axum)" {
                tags "Primary"
            }
            healthServer = container "Health Server" "Separate unauthenticated HTTP server for health and info endpoints" "Rust (axum)" {
                tags "Health"
            }
            tlsLayer = container "TLS Layer" "Optional TLS termination with mTLS support using rustls (ring crypto provider)" "Rust (rustls)" {
                tags "Security"
            }
            headerPassthrough = container "Header Passthrough" "Filters and forwards configured headers; rewrites X-Forwarded-Access-Token to Authorization Bearer" "Rust" {
                tags "Security"
            }
        }

        chunkerServices = softwareSystem "Chunker Services" "Text segmentation services accessed via gRPC" "External Service" {
            tags "Downstream"
        }
        detectorServices = softwareSystem "Detector Services" "Content safety evaluation services accessed via REST" "External Service" {
            tags "Downstream"
        }
        tgisGeneration = softwareSystem "TGIS Generation Service" "Text Generation Inference Service accessed via gRPC" "External Service" {
            tags "Downstream"
        }
        openaiGeneration = softwareSystem "OpenAI-compatible Generation" "Optional chat/completions generation service accessed via REST" "External Service" {
            tags "Downstream Optional"
        }
        otlpCollector = softwareSystem "OTLP Collector" "OpenTelemetry traces and metrics collection endpoint" "External Service" {
            tags "Observability"
        }

        # Relationships
        user -> guardrailsOrchestrator "Sends classification/detection/generation requests" "HTTPS/8033 (TLS optional)"
        user -> guardrailsOrchestrator "Checks service health" "HTTP/8034"

        guardrailsOrchestrator -> chunkerServices "Segments text for analysis" "gRPC/8085 (TLS optional)"
        guardrailsOrchestrator -> detectorServices "Evaluates content safety" "REST/8080 (TLS optional, Bearer optional)"
        guardrailsOrchestrator -> tgisGeneration "Generates text responses" "gRPC/8033"
        guardrailsOrchestrator -> openaiGeneration "Generates chat/completions" "REST (HTTP/HTTPS)"
        guardrailsOrchestrator -> otlpCollector "Exports traces and metrics" "gRPC/HTTP (OTLP)"

        # Internal relationships
        tlsLayer -> guardrailsServer "Decrypted requests"
        guardrailsServer -> headerPassthrough "Filters headers"
    }

    views {
        systemContext guardrailsOrchestrator "SystemContext" {
            include *
            autoLayout
        }

        container guardrailsOrchestrator "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #438DD5
                color #ffffff
            }
            element "Person" {
                background #08427B
                color #ffffff
                shape person
            }
            element "Container" {
                background #438DD5
                color #ffffff
            }
            element "Downstream" {
                background #999999
                color #ffffff
            }
            element "Downstream Optional" {
                background #BBBBBB
                color #ffffff
                border dashed
            }
            element "Observability" {
                background #9673A6
                color #ffffff
            }
            element "Primary" {
                background #4a90e2
                color #ffffff
            }
            element "Health" {
                background #82b366
                color #ffffff
            }
            element "Security" {
                background #b85450
                color #ffffff
            }
        }
    }
}
