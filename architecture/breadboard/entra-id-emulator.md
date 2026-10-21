# Component: entra-id-emulator

## Purpose

The emulator is a Flask-based Python service that mimics Microsoft Entra ID for local development. It exposes tenant-scoped OIDC/OAuth2 endpoints (discovery, authorize, token, JWKS, userinfo, logout) supporting authorization code with PKCE, refresh token, password, and hybrid flows. State lives in SQLite seeded from a YAML config, tokens are signed with generated RSA keys, and a password-protected admin REST API and web UI allow full CRUD on tenants, users, groups, and clients.

## Architectural Analysis

A single-process Flask application created by a factory (entra_mock/app.py) that loads YAML config, initializes and seeds an SQLite database, ensures an RSA signing key, and registers route blueprints under entra_mock/routes/. OIDC surfaces are tenant-scoped paths mirroring Entra ID URL conventions (/<tenant>/oauth2/v2.0/*, discovery, JWKS), plus an admin REST API (/api/tenants, /api/users, /api/groups, /api/clients) protected by optional HTTP Basic Auth against a configured admin_password, and an /oidc/userinfo endpoint. Token issuance (entra_mock/tokens.py) supports ID, access, and refresh tokens with pairwise subject identifiers and per-tenant/client lifetime overrides; keys.py manages RSA keys and JWKS. Deployment is a python:3.11-slim container running run.py on port 8080, with source mounted at runtime; example compose files pair it with oauth2-proxy as a relying party. There is no ingress, gRPC, CRD, or platform integration; state is local SQLite and all data is in-memory/file-backed, making it a single-instance development tool rather than a scalable service.

## Architecture Components

| Component | Type | Purpose |
|----|----|-------|
| entra_mock app factory | Flask application factory | Loads YAML config, initializes SQLite DB, seeds data, ensures signing keys, and registers route bluephints |
| OIDC route blueprints | Flask blueprints | Tenant-scoped authorize, token, discovery, JWKS, userinfo, and logout endpoints emulating Entra ID v2.0 |
| Admin API and UI | Flask blueprint with HTTP Basic Auth | CRUD management of tenants, users, groups, and clients, plus password-protected admin web console at /admin/ |
| Token service | Python module | Generates and signs ID, access, and refresh tokens with pairwise subs and lifetime overrides |
| Key management | Python module | Generates 2048-bit RSA signing keys, persists them, and builds JWKS responses |
| SQLite datastore | Embedded database | Stores tenants, users, groups, clients, tokens, and signing keys; seeded from config.yaml |

## Sub-Component: entra_mock

**API Routes:**

| Path | Methods |
|----|--------|
| /<tenant>/oauth2/v2.0/authorize | GET, POST |
| /<tenant>/oauth2/v2.0/token | POST |
| /<tenant>/oauth2/v2.0/logout | GET, POST |
| /<tenant>/v2.0/.well-known/openid-configuration | GET |
| /<tenant>/discovery/v2.0/keys | GET |
| /oidc/userinfo | GET, POST |
| /api/tenants | GET, POST |
| /api/tenants/<tenant_id> | PUT, DELETE |
| /api/users | GET, POST |
| /api/users/<user_id> | PUT, DELETE |
| /api/groups | GET, POST |
| /api/groups/<group_id> | PUT, DELETE |
| /api/clients | GET, POST |
| /api/clients/<client_id> | PUT, DELETE |
| / | GET |
| /admin/ | GET |

**Configuration:**

- config.yaml (server host/port/scheme/debug/admin_password, tenants, users, clients, token lifetimes)
- ENTRA_MOCK_DB environment variable (SQLite path, default data/entra_mock.db)
- FLASK_SECRET_KEY environment variable (Flask session secret)

## APIs Exposed

### HTTP Endpoints

| Path | Methods | Description |
|----|---------|-------------|
| /<tenant>/oauth2/v2.0/authorize | GET, POST | OIDC authorization endpoint supporting code, hybrid, and implicit flows with PKCE |
| /<tenant>/oauth2/v2.0/token | POST | Token endpoint supporting authorization code, refresh token, and password grants |
| /<tenant>/oauth2/v2.0/logout | GET, POST | OIDC logout including front-channel logout |
| /<tenant>/v2.0/.well-known/openid-configuration | GET | OIDC discovery document for the tenant |
| /<tenant>/discovery/v2.0/keys | GET | JWKS endpoint exposing public signing keys |
| /oidc/userinfo | GET, POST | UserInfo endpoint returning claims for bearer access tokens |
| /api/tenants | GET, POST | List and create tenants (admin, optionally password-protected) |
| /api/tenants/<tenant_id> | PUT, DELETE | Update and delete tenants |
| /api/users | GET, POST | List and create users |
| /api/users/<user_id> | PUT, DELETE | Update and delete users |
| /api/groups | GET, POST | List and create groups |
| /api/groups/<group_id> | PUT, DELETE | Update and delete groups |
| /api/clients | GET, POST | List and create OAuth2 client registrations |
| /api/clients/<client_id> | PUT, DELETE | Update and delete OAuth2 client registrations |
| / | GET | Landing page linking to the admin console |
| /admin/ | GET | Admin web UI, protected by HTTP Basic Auth when admin_password is set |

## Dependencies

**External:** flask>=3.0, pyjwt>=2.8, cryptography>=42.0, jwcrypto>=1.5, pyyaml>=6.0, SQLite (stdlib)

## Deployment

Single-container deployment from a python:3.11-slim Docker image running run.py on port 8080, with source and data mounted at runtime; compose examples integrate it with oauth2-proxy for testing OIDC flows.

**Variants:**

- **Local Python**: pip install requirements.txt and python run.py; serves on host/port from config.yaml
- **Docker/Podman compose**: Container with mounted source and data volumes, port 8080 published, optionally alongside oauth2-proxy as relying party

## Network Architecture

**Services:**

- **entra-id-emulator**: Single Flask HTTP service listening on port 8080 (configurable via config.yaml)

**Ingress:**

- **none**: No ingress resources; direct HTTP exposure on port 8080, scheme configurable in config.yaml

**Egress:**

- **none**: No outbound runtime connections; the emulator makes no calls to external services

## Security

- **Authentication:** Emulated OIDC authentication: user passwords hashed (werkzeug) in SQLite, client authentication via client_secret_basic or client_secret_post at the token endpoint, and bearer access tokens for /oidc/userinfo. Admin API and UI use optional HTTP Basic Auth against server.admin_password from config.yaml; no authentication middleware is registered on the Flask app itself.
- **Authorization:** OAuth2 scope and redirect_uri validation per registered client; no role-based authorization beyond the admin password gate.
- **FIPS Compliance:** not applicable

**Secrets:**

- FLASK_SECRET_KEY environment variable (Flask session secret)
- server.admin_password in config.yaml (admin Basic Auth)
- client_secret values stored in SQLite/config.yaml
- RSA signing private keys stored in SQLite

## Multi-Tenancy

**Model:** Emulated multi-tenancy: multiple Entra ID tenants stored as rows in SQLite, each with its own domain, salt, and token lifetime overrides, addressed via tenant-scoped URL paths.

**Isolation Mechanisms:**

- Per-tenant URL path scoping (/<tenant>/...)
- Per-tenant salt for pairwise subject identifiers
- Tenant foreign keys on users, groups, and clients

**Shared Services:** Single shared SQLite database and shared signing keys across all emulated tenants

## Data Flows

- **OIDC authorization code flow**: Client redirects user to authorize endpoint; user authenticates against seeded credentials; server issues a one-time code exchanged at the token endpoint for signed ID/access/refresh tokens.
- **Config seeding**: On startup, config.yaml tenants, users, groups, and clients are loaded into SQLite; signing keys are generated if absent.
- **Admin management**: Admin API/UI CRUD operations write directly to the SQLite datastore, affecting subsequent OIDC behavior.
- **Token validation by relying parties**: Relying parties (e.g., oauth2-proxy) fetch JWKS and discovery documents to validate issued JWTs.

## Integration Points

- **OAuth2 relying parties**: Any OIDC client such as oauth2-proxy can use the emulator as an identity provider; examples include compose and oauth2-proxy configuration
- **ODH/RHOAI BYOIDC**: Documentation describes configuring OpenShift AI and ODH Bring-Your-Own-Identity-Provider against the emulator for local testing

## Concerns

- Emulator only: emulated authentication, plaintext secrets in config.yaml, and no production hardening; must not be exposed publicly
- Single-instance, stateful SQLite storage with no high-availability or replication path
- Admin API has no authentication unless admin_password is explicitly configured; default credentials are committed in config.yaml
- No TLS by default (scheme http); encryption depends on external ingress
- No health probes, resource limits, or Kubernetes manifests; Dockerfile omits source, requiring runtime volume mounts

