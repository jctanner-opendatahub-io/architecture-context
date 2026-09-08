workspace {
    model {
        client = person "API Client" "Application or user sending OpenAI-compatible chat completion requests"

        gateway = softwareSystem "vllm-orchestrator-gateway" "HTTP gateway that provides route-specific OpenAI-compatible chat completion endpoints with configurable detector-based content filtering" {
            routerContainer = container "Axum Router" "Dynamically creates POST endpoints per configured route at /{route_name}/v1/chat/completions" "Rust / axum 0.7"
            configContainer = container "Config Loader" "Reads YAML configuration defining routes and detector parameters at startup" "Rust / serde_yml"
            proxyContainer = container "HTTP Proxy Client" "Forwards enriched requests to orchestrator with optional mTLS" "Rust / reqwest + native-tls"
            detectorContainer = container "Detector Enricher" "Injects route-specific input/output detector configurations into requests" "Rust"
            fallbackContainer = container "Fallback Handler" "Substitutes configurable fallback message when detectors flag content" "Rust"
        }

        orchestrator = softwareSystem "TrustyAI Orchestrator" "Backend service that evaluates chat completions against configured content safety detectors" "Internal Platform"

        configFile = softwareSystem "Configuration" "YAML config file defining routes, detectors, and fallback messages" "File System"

        client -> gateway "Sends chat completion requests" "HTTP/8090 POST"
        gateway -> orchestrator "Proxies enriched requests with detector configs" "HTTP or HTTPS (optional mTLS) / configurable port"
        configFile -> gateway "Provides route and detector configuration" "File read at startup"

        routerContainer -> detectorContainer "Routes request to enricher"
        detectorContainer -> proxyContainer "Sends enriched request"
        proxyContainer -> fallbackContainer "Returns response for evaluation"
        configContainer -> routerContainer "Provides route definitions"
    }

    views {
        systemContext gateway "SystemContext" {
            include *
            autoLayout
        }

        container gateway "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Software System" {
                background #4a90e2
                color #ffffff
            }
            element "Internal Platform" {
                background #7ed321
                color #ffffff
            }
            element "File System" {
                background #999999
                color #ffffff
            }
            element "Person" {
                background #f5a623
                color #ffffff
                shape Person
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
        }
    }
}
