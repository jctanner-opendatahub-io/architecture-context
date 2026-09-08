# Architecture Changes: praxis-policy

| Action | Category | Row Key | Column | Analyzer Value | Candidate Value | Reason | Evidence |
|--------|----------|---------|--------|----------------|-----------------|--------|----------|
| add | authentication | Inbound requests (host-delegated) :: All | * | <empty> | <empty> | JWT identity resolution plugin validates inbound tokens with fail-closed semantics | builtins/plugins/identity-jwt/Cargo.toml:4-14, crates/ppe-core/Cargo.toml:28-29 |
| add | authentication | Downstream delegation :: All | * | <empty> | <empty> | OAuth 2.0 token exchange plugin performs RFC 8693 delegation against external IdP | builtins/plugins/delegator-oauth/Cargo.toml:4-28 |
| add | authentication | Privileged operations :: All | * | <empty> | <empty> | CIBA elicitation plugin drives human-in-the-loop approval through OIDC backchannel authentication | builtins/plugins/elicitation-ciba/Cargo.toml:4-26 |
| add | integration_points | Valkey/Redis :: Redis client (deadpool-redis) | * | <empty> | <empty> | Session store connects to Valkey/Redis with rustls TLS and connection pooling | builtins/session/valkey/Cargo.toml:43-59 |
| add | integration_points | OAuth 2.0 IdP (Keycloak, Auth0, Hydra, Zitadel) :: HTTP client (via HttpTransport) | * | <empty> | <empty> | Delegator-oauth posts RFC 8693 token exchange requests to IdP token endpoint | builtins/plugins/delegator-oauth/Cargo.toml:4-28 |
| add | integration_points | JWKS endpoint :: HTTP client (via HttpTransport) | * | <empty> | <empty> | Identity-jwt plugin performs background periodic JWKS key refresh | builtins/plugins/identity-jwt/Cargo.toml:62-68 |
| add | integration_points | OIDC CIBA provider :: HTTP client (via HttpTransport) | * | <empty> | <empty> | Elicitation-ciba posts backchannel auth requests and polls token endpoint | builtins/plugins/elicitation-ciba/Cargo.toml:4-26 |
| add | internal_dependencies | praxis-proxy :: Library embedding | * | <empty> | <empty> | Host application embeds praxis-policy and injects Pingora-backed HttpTransport | crates/ppe/Cargo.toml:75-77 |
