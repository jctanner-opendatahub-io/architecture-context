workspace {
    model {
        orchestrator = person "Guardrails Orchestrator" "Upstream guardrails component that routes detection requests"

        regexDetector = softwareSystem "guardrails-regex-detector" "Stateless Rust HTTP service for regex-based PII detection (email, SSN, credit card, custom patterns)" {
            server = container "Axum HTTP Server" "Serves detection and health endpoints on port 8080" "Rust / Axum 0.7.9 / Tokio"
            detectionEngine = container "Detection Engine" "Applies built-in and custom regex patterns to text content" "Rust / regex 1.11.1"
        }

        kubelet = softwareSystem "Kubernetes" "Container orchestration platform" "External"
        serviceMesh = softwareSystem "Service Mesh / Gateway" "Provides TLS termination, mTLS, and authentication" "External"

        orchestrator -> regexDetector "POST /api/v1/text/contents (JSON)" "HTTP/8080"
        kubelet -> regexDetector "GET /health" "HTTP/8080"
        serviceMesh -> regexDetector "Provides TLS termination, mTLS, auth enforcement" ""

        server -> detectionEngine "Dispatches detection requests"
    }

    views {
        systemContext regexDetector "SystemContext" {
            include *
            autoLayout
        }

        container regexDetector "Containers" {
            include *
            autoLayout
        }

        styles {
            element "External" {
                background #999999
                color #ffffff
            }
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Container" {
                background #7ed321
                color #ffffff
            }
            element "Person" {
                background #f5a623
                color #ffffff
                shape Person
            }
        }
    }
}
