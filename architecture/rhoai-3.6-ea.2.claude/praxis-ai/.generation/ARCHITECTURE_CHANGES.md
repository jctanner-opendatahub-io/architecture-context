# Architecture Changes: praxis-ai

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | http_endpoints | GET :: / | * | <empty> | <empty> | Default listener serves static JSON response on root path; port and protocol established by default.yaml | server/src/default.yaml:15-32 |
| add | http_endpoints | GET :: /healthy | * | <empty> | <empty> | Admin health check endpoint registered by praxis-protocol for container orchestrator probes | server/src/server.rs:222-234, Containerfile:122-123 |
| add | authentication | Upstream AI Providers :: All | * | <empty> | <empty> | credential_inject filter injects static secrets/API keys and AWS SigV4 signing for upstream provider authentication; both registered as security filters | server/src/lib.rs:146-158, filters/Cargo.toml:49-50, filters/src/lib.rs:32 |
| add | authentication | Proxy Listeners :: All | * | <empty> | <empty> | peer_identity_trust filter validates client mTLS certificate digests against configured trusted peer list | server/src/lib.rs:162-195 |
| add | integration_points | LLM/AI Provider Backends :: HTTP Proxy | * | <empty> | <empty> | Proxy routes inference requests to configured upstream AI provider clusters via HTTP/HTTPS | server/src/server.rs:52-68, server/src/lib.rs:63-71 |
| add | integration_points | llm-d (ext_proc) :: gRPC Client | * | <empty> | <empty> | Optional ext_proc compatibility filter sends request/response to llm-d gRPC endpoint for model-aware scheduling | integrations/llmd/ext-proc/src/lib.rs:1-55, server/Cargo.toml:37 |
| add | integration_points | Redis/Valkey :: TCP Client | * | <empty> | <empty> | Experimental token_rate_limit filter uses Redis/Valkey for rate limiting state; feature-gated behind token-rate-limit-filter | filters/Cargo.toml:36, filters/Cargo.toml:61 |
| add | internal_dependencies | praxis-proxy-core (praxis-core) | * | <empty> | <empty> | Core proxy runtime providing configuration, health checks, connection management, sub-request client, and server bootstrap | Cargo.toml:89 |
| add | internal_dependencies | praxis-proxy-filter (praxis-filter) | * | <empty> | <empty> | Filter trait system providing filter registry, built-in filters, security filter enforcement, and HTTP filter trait | Cargo.toml:90 |
| add | internal_dependencies | praxis-proxy-protocol (praxis-protocol) | * | <empty> | <empty> | Protocol handlers for HTTP, TCP, admin API endpoints, and config reload support | Cargo.toml:91, server/Cargo.toml:51 |
| add | internal_dependencies | praxis-proxy-tls (praxis-tls) | * | <empty> | <empty> | TLS configuration and certificate management for proxy listeners | Cargo.toml:92 |
| add | internal_dependencies | quixotic-plecostomus-core (pingora-core) | * | <empty> | <empty> | Underlying Pingora HTTP proxy runtime (temporary fork) with rustls TLS feature | Cargo.toml:106 |
