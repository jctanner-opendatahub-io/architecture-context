# Component: entra-id-emulator

## Purpose

entra-id-emulator is a Flask-based Python service that emulates Microsoft Entra ID for local development. It exposes per-tenant OIDC/OAuth2 endpoints (discovery, authorize, token, JWKS, userinfo, logout), supports authorization code with PKCE, refresh token and password grants, hybrid flows, pairwise subject identifiers, groups claims with overage handling, and per-tenant/per-client token lifetime overrides. Data lives in SQLite with YAML-driven seeding, and an admin REST API plus password-protected web UI manage tenants, users, groups, and clients.

## Architectural Analysis

The service is a single-process Flask application assembled by an app factory (entra_mock/app.py) that loads YAML config, initializes and seeds a SQLite database, ensures an RSA signing key, and registers route blueprints. Routes are split by concern under entra_mock/routes: per-tenant OIDC endpoints (discovery, authorize, token, jwks, userinfo, logout) and an admin REST API with HTTP Basic Auth guarding tenants, users, groups, and clients CRUD, plus a landing page and admin web UI. Token issuance and claim building live in tokens.py; key management in keys.py; persistence and seeding in db.py. Deployment is via run.py on port 8080, a Dockerfile, or compose examples; configuration comes from config.yaml and environment variables (ENTRA_MOCK_DB, FLASK_SECRET_KEY). The analyzer found no authentication middleware on OIDC endpoints (by design for an emulator), no CRDs, no gRPC services, and no ingress resources.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| app factory | Flask application factory | Creates the app, loads config, initializes DB, ensures signing key, registers routes |
| routes (OIDC) | Flask blueprints | Per-tenant discovery, authorize, token, JWKS, userinfo, and logout endpoints |
| admin API and UI | Flask blueprint | CRUD REST API for tenants, users, groups, clients plus password-protected admin console and landing page |
| tokens | Python module | JWT/ID token issuance, claim building, token lifetime handling |
| keys | Python module | RSA signing key management for JWKS and token signing |
| db | SQLite persistence layer | Schema creation, config seeding, and helper queries |
| config | Python module | Loads YAML configuration for server, tenants, users, groups, clients, lifetimes |

## Sub-Component: entra_mock

**API Routes:**

| Path | Methods |
|----|--------|
| /{tenant}/v2.0/.well-known/openid-configuration | GET |
| /{tenant}/oauth2/v2.0/authorize | GET, POST |
| /{tenant}/oauth2/v2.0/token | POST |
| /{tenant}/discovery/v2.0/keys | GET |
| /{tenant}/oauth2/v2.0/logout | GET, POST |
| /oidc/userinfo | GET, POST |
| / | GET |
| /api/tenants | GET, POST |
| /api/tenants/{tenant_id} | PUT, DELETE |
| /api/users | GET, POST |
| /api/users/{user_id} | PUT, DELETE |
| /api/groups | GET, POST |
| /api/groups/{group_id} | PUT, DELETE |
| /api/clients | GET, POST |
| /api/clients/{client_id} | PUT, DELETE |

**Upstream Dependencies:** flask, pyjwt, jwcrypto, cryptography, pyyaml

**Configuration:**

- config.yaml
- ENTRA_MOCK_DB
- FLASK_SECRET_KEY

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /{tenant}/v2.0/.well-known/openid-configuration | GET | OIDC discovery document per tenant |
| /{tenant}/oauth2/v2.0/authorize | GET, POST | Authorization endpoint supporting code, hybrid, and implicit flows with PKCE |
| /{tenant}/oauth2/v2.0/token | POST | Token endpoint for authorization code, refresh token, and password grants |
| /{tenant}/discovery/v2.0/keys | GET | JWKS endpoint exposing public signing keys |
| /{tenant}/oauth2/v2.0/logout | GET, POST | End-session/logout endpoint |
| /oidc/userinfo | GET, POST | UserInfo endpoint returning claims for authenticated user |
| / | GET | Landing page linking to the admin console |
| /api/tenants | GET, POST | List and create tenants |
| /api/tenants/{tenant_id} | PUT, DELETE | Update or delete a tenant |
| /api/users | GET, POST | List and create users |
| /api/users/{user_id} | PUT, DELETE | Update or delete a user |
| /api/groups | GET, POST | List and create groups |
| /api/groups/{group_id} | PUT, DELETE | Update or delete a group |
| /api/clients | GET, POST | List and create OAuth clients |
| /api/clients/{client_id} | PUT, DELETE | Update or delete an OAuth client |

## Dependencies

**External:** flask, pyjwt, jwcrypto, cryptography, pyyaml, SQLite (stdlib)

## Deployment

Runs as a single Python process via run.py on port 8080 (default), configured by config.yaml; ships a Dockerfile (python:3.11-slim) and podman/docker compose examples with an oauth2-proxy integration sample.

**Variants:**

- **local Python**: pip install requirements.txt and python run.py, serving on localhost:8080
- **container**: Dockerfile based on python:3.11-slim exposing port 8080, source mounted at runtime
- **compose with oauth2-proxy**: Example compose files wiring the emulator behind oauth2-proxy for integration testing

## Network Architecture

**Services:**

- **entra-id-emulator**: Single Flask HTTP service listening on configurable host/port (default 0.0.0.0:8080)

## Security

- **Authentication:** OIDC endpoints emulate Entra ID (client credentials, auth codes, PKCE); admin API and UI protected by HTTP Basic Auth when admin_password is configured; no middleware-level auth on public OIDC endpoints
- **Authorization:** Emulated OAuth2 scopes and client-based flows; admin surface gated by shared admin password
- **FIPS Compliance:** not applicable

**Secrets:**

- FLASK_SECRET_KEY (environment variable for session cookies)
- admin_password (config.yaml for admin Basic Auth)
- client_secret and user passwords (config.yaml / SQLite)

## Multi-Tenancy

**Model:** Multiple emulated Entra ID tenants, each with own domain, users, groups, clients, salt, and token lifetime overrides, addressed via per-tenant URL paths

**Isolation Mechanisms:**

- per-tenant URL path segments (/{tenant}/...)
- per-tenant pairwise subject identifier salts
- tenant-scoped users, groups, and clients in SQLite

**Shared Services:** single shared Flask process and SQLite database

## Data Flows

- **OIDC authorization flow**: Client redirects to per-tenant authorize endpoint; user authenticates against seeded credentials; code (with PKCE) is issued and exchanged at the token endpoint for JWTs signed by the RSA key
- **token issuance**: tokens.py builds access/ID/refresh tokens with configurable lifetimes, pairwise sub claims, and groups claim with overage handling; JWKS publishes public keys
- **admin management**: Admin UI/REST API performs CRUD on SQLite-backed tenants, users, groups, and clients, seeded from config.yaml at startup
- **userinfo**: Resource server presents access token to /oidc/userinfo, which returns claims for the token subject

## Integration Points

- **OIDC relying parties**: Any OAuth2/OIDC client (e.g., oauth2-proxy per example config) can use discovery, authorize, token, JWKS, and userinfo endpoints
- **oauth2-proxy integration**: Example compose and oauth2-proxy.cfg demonstrate using the emulator as the OIDC provider for oauth2-proxy

## Concerns

- No authentication middleware on public OIDC endpoints; acceptable for an emulator but unsafe if exposed beyond localhost
- Default admin password (changeme1234) and plaintext secrets in config.yaml
- Single-process SQLite storage with no HA story; intended only for local development and testing
- Sign-in and consent flows are simulated, so fidelity to real Entra ID behavior is partial

